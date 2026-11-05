#!/usr/bin/env python3
"""Dataset builder for YOLO-based ATCG nucleotide detection in annotated images."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - dependency is optional until dataset is built.
    raise RuntimeError("Pillow is required to build the ATCG YOLO dataset. Install it via pip install Pillow.") from exc

ATCG_CLASSES: List[str] = ["A", "T", "C", "G"]
CLASS_TO_IDX: Dict[str, int] = {base: idx for idx, base in enumerate(ATCG_CLASSES)}
DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _safe_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(DEFAULT_FONT, size=size)
    except OSError:
        return ImageFont.load_default()


def _normalize_box(x0: float, y0: float, x1: float, y1: float, image_size: int) -> Tuple[float, float, float, float]:
    width = max(1.0, x1 - x0)
    height = max(1.0, y1 - y0)
    center_x = ((x0 + x1) / 2.0) / image_size
    center_y = ((y0 + y1) / 2.0) / image_size
    box_w = width / image_size
    box_h = height / image_size
    return center_x, center_y, box_w, box_h


def _draw_sequence_image(image_path: Path, sequence: str, image_size: int = 1024, seed: int = 0) -> List[Tuple[str, float, float, float, float]]:
    rng = random.Random(seed)
    img = Image.new("RGB", (image_size, image_size), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)

    pad_x = 80
    pad_y = 300
    step = max(80, (image_size - 2 * pad_x) // max(1, len(sequence)))
    positions = []
    labels: List[Tuple[str, float, float, float, float]] = []
    font_size = max(140, min(250, step + 20))
    font = _safe_font(font_size)

    for index, letter in enumerate(sequence):
        x = pad_x + index * step + rng.randint(-10, 10)
        y = pad_y + rng.randint(-25, 25)
        bbox = draw.textbbox((x, y), letter, font=font)
        x0, y0, x1, y1 = bbox
        draw.text((x, y), letter, font=font, fill=(26, 26, 26))
        cx, cy, bw, bh = _normalize_box(x0, y0, x1, y1, image_size)
        labels.append((letter, cx, cy, bw, bh))
        positions.append((x, y, letter))

    img.save(image_path)
    return labels


def _write_data_yaml(dataset_dir: Path) -> None:
    yaml_text = (
        "path: .\n"
        "train: images/train\n"
        "val: images/val\n"
        "nc: 4\n"
        "names:\n"
        "  0: A\n"
        "  1: T\n"
        "  2: C\n"
        "  3: G\n"
    )
    (dataset_dir / "data.yaml").write_text(yaml_text, encoding="utf-8")


def _create_split_dirs(dataset_dir: Path) -> None:
    for split_name in ("train", "val"):
        split_image_dir = dataset_dir / "images" / split_name
        split_label_dir = split_image_dir / "labels"
        split_image_dir.mkdir(parents=True, exist_ok=True)
        split_label_dir.mkdir(parents=True, exist_ok=True)


def generate_dataset(
    dataset_root: str,
    images_per_class: int = 60,
    val_ratio: float = 0.2,
    image_size: int = 1024,
    seed: int = 42,
) -> Dict[str, int]:
    """Create a synthetic YOLO dataset for ATCG detection from annotated image snippets."""
    root = Path(dataset_root)
    root.mkdir(parents=True, exist_ok=True)
    _create_split_dirs(root)

    rng = random.Random(seed)
    generated_images = 0
    generated_labels = 0
    total = images_per_class * len(ATCG_CLASSES)
    val_count = max(1, int(round(total * val_ratio)))

    for index in range(total):
        split_name = "val" if index < val_count else "train"
        sequence_length = rng.randint(6, 10)
        sequence = "".join(rng.choice(ATCG_CLASSES) for _ in range(sequence_length))
        image_name = f"atcg_{split_name}_{index:03d}.png"
        image_path = root / "images" / split_name / image_name
        label_path = root / "images" / split_name / "labels" / image_name.replace(".png", ".txt")

        labels = _draw_sequence_image(image_path, sequence, image_size=image_size, seed=index + seed)
        lines: List[str] = []
        for (letter, cx, cy, bw, bh) in labels:
            class_id = CLASS_TO_IDX[letter]
            lines.append(f"{class_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
            generated_labels += 1

        label_path.write_text("".join(lines), encoding="utf-8")
        generated_images += 1

    _write_data_yaml(root)
    return {"images": generated_images, "labels": generated_labels}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a YOLO ATCG dataset from annotated DNA images.")
    parser.add_argument("--dataset-root", default="./datasets/atcg_yolo", help="Folder to create the dataset under")
    parser.add_argument("--images-per-class", type=int, default=60, help="Number of synthetic images per nucleotide class")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="Validation split ratio")
    parser.add_argument("--image-size", type=int, default=1024, help="Square image width/height")
    args = parser.parse_args()
    info = generate_dataset(
        dataset_root=args.dataset_root,
        images_per_class=args.images_per_class,
        val_ratio=args.val_ratio,
        image_size=args.image_size,
    )
    print(f"Generated dataset: {info}")


if __name__ == "__main__":
    main()
