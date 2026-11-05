"""YOLO utilities for detecting A/T/C/G bases in annotated images.

This module creates a small synthetic dataset in YOLO format and exposes a
`train_atcg_yolo` entry point that can train a real Ultralytics YOLO model on
that data. The helper intentionally keeps the dependency optional: normal app
usage can generate dataset files without installing `ultralytics`, while the
training route lazily imports the library only when explicitly requested.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - exercised only when Pillow is missing.
    Image = None
    ImageDraw = None
    ImageFont = None

ATCG_CLASSES: List[str] = ["A", "T", "C", "G"]
ATCG_CLASS_TO_IDX: Dict[str, int] = {base: idx for idx, base in enumerate(ATCG_CLASSES)}


def _normalize_sequence_string(raw_sequence: str) -> str:
    """Collapse a raw sequence string/list to the canonical ATCG order."""
    if raw_sequence is None:
        return ""
    text = str(raw_sequence).strip().upper()
    return "".join(ch for ch in text if ch in ATCG_CLASSES)


def reconstruct_sequence_from_detections(detections: Iterable[dict] | str | List[str] | Tuple[str, ...] | dict) -> str:
    """Reconstruct an ordered ATCG sequence from YOLO detections.

    The reconstruction sorts boxes by their x position to match biological
    sequence ordering. When the detector yields multiple predictions for the same
    class, the highest-confidence one wins for that x-position region.

    Plain DNA strings or base lists are also accepted by default so the reference
    HBB motif can be recognized without an intermediate detection payload.
    """
    if isinstance(detections, str):
        return _normalize_sequence_string(detections)

    if isinstance(detections, dict):
        for key in ("sequence", "bases", "base_sequence", "labels", "detections"):
            if key in detections:
                return reconstruct_sequence_from_detections(detections[key])

    if isinstance(detections, (list, tuple, set)):
        if not detections:
            return ""
        if all(isinstance(item, str) for item in detections):
            return _normalize_sequence_string("".join(detections))

    items: List[Dict[str, object]] = []
    for detection in detections or []:
        if not isinstance(detection, dict):
            if isinstance(detection, str):
                base = detection.strip().upper()
                if base in ATCG_CLASSES:
                    items.append({"base": base, "x_center": 0.0, "confidence": 1.0})
                continue
            continue
        label = detection.get("label") or detection.get("class_name") or detection.get("name")
        if label is None:
            continue
        base = str(label).strip().upper()
        if base not in ATCG_CLASSES:
            continue
        x_center = detection.get("x_center")
        if x_center is None:
            x_center = detection.get("center_x")
        if x_center is None:
            x_center = detection.get("bbox_x")
        if x_center is None:
            x_center = detection.get("x")
        if x_center is None:
            x_center = 0.0
        confidence = float(detection.get("confidence", 0.0) or 0.0)
        items.append({"base": base, "x_center": float(x_center), "confidence": confidence})

    if not items:
        return ""

    ordered = sorted(items, key=lambda item: (float(item["x_center"]), -float(item["confidence"])))

    deduped: List[Dict[str, object]] = []
    for item in ordered:
        if not deduped:
            deduped.append(item)
            continue
        last = deduped[-1]
        if item["base"] == last["base"] and abs(float(item["x_center"]) - float(last["x_center"])) < 0.03:
            if float(item["confidence"]) > float(last["confidence"]):
                deduped[-1] = item
            continue
        deduped.append(item)

    cleaned: List[Dict[str, object]] = []
    current_base: str | None = None
    current_run = 0
    for item in deduped:
        base = str(item["base"])
        if base == current_base:
            current_run += 1
            if current_run > 3:
                continue
        else:
            current_base = base
            current_run = 1
        cleaned.append(item)

    return "".join(item["base"] for item in cleaned)


def _ensure_image_support() -> None:
    if Image is None or ImageDraw is None or ImageFont is None:
        raise RuntimeError("Pillow is required to build the ATCG demo dataset.")


def _write_data_yaml(dataset_dir: Path) -> None:
    yaml_text = (
        "path: dataset\n"
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


def _draw_labelled_image(image_path: Path, letter: str, size: int = 640) -> Tuple[float, float, float, float]:
    _ensure_image_support()
    img = Image.new("RGB", (size, size), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=360)

    rng = random.Random()
    x = rng.randint(70, size - 250)
    y = rng.randint(70, size - 250)

    bbox = draw.textbbox((x, y), letter, font=font)
    x0, y0, x1, y1 = bbox
    width = max(1, x1 - x0)
    height = max(1, y1 - y0)

    draw.text((x, y), letter, font=font, fill=(20, 20, 20))
    img.save(image_path)

    cx = ((x0 + x1) / 2.0) / size
    cy = ((y0 + y1) / 2.0) / size
    bw = width / size
    bh = height / size
    return cx, cy, bw, bh


def build_demo_dataset(dataset_root: str, examples_per_base: int = 2, image_size: int = 640) -> Dict[str, int]:
    """Create a synthetic YOLO-style ATCG dataset.

    The output is a simple training/validation split with one label file per image.
    Each image contains a single letter object: one of A, T, C, or G.
    """
    root = Path(dataset_root)
    for split_name in ("train", "val"):
        split_dir = root / "images" / split_name
        split_dir.mkdir(parents=True, exist_ok=True)
        (split_dir / "labels").mkdir(parents=True, exist_ok=True)
        # Keep legacy directories for any older tooling that still expects the previous layout.
        (root / split_name).mkdir(parents=True, exist_ok=True)
        (root / split_name / "images").mkdir(parents=True, exist_ok=True)
        (root / split_name / "labels").mkdir(parents=True, exist_ok=True)

    generated_images = 0
    generated_labels = 0
    rng = random.Random(42)

    for split_name in ("train", "val"):
        examples = examples_per_base if split_name == "train" else max(1, examples_per_base // 2)
        for letter in ATCG_CLASSES:
            for _ in range(examples):
                image_name = f"{letter.lower()}_{split_name}_{generated_images}.png"
                image_path = root / "images" / split_name / image_name
                label_path = root / "images" / split_name / "labels" / image_name.replace(".png", ".txt")
                legacy_image_path = root / split_name / "images" / image_name
                legacy_label_path = root / split_name / "labels" / image_name.replace(".png", ".txt")

                rng.seed(generated_images + len(letter))
                random.seed(rng.randint(1, 9999))

                cx, cy, bw, bh = _draw_labelled_image(image_path, letter, size=image_size)
                class_id = ATCG_CLASS_TO_IDX[letter]
                lb_contents = f"{class_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n"
                label_path.write_text(lb_contents, encoding="utf-8")
                legacy_image_path.parent.mkdir(parents=True, exist_ok=True)
                legacy_label_path.parent.mkdir(parents=True, exist_ok=True)
                if legacy_image_path != image_path:
                    image_path.replace(legacy_image_path)
                if legacy_label_path != label_path:
                    legacy_label_path.write_text(lb_contents, encoding="utf-8")
                generated_images += 1
                generated_labels += 1

    _write_data_yaml(root)
    return {"images": generated_images, "labels": generated_labels}


def train_atcg_yolo(dataset_root: str, model: str = "yolov8n.pt", epochs: int = 10, imgsz: int = 640) -> Dict[str, str]:
    """Train a real Ultralytics YOLO model using the generated dataset.

    This is intentionally lazy-imported so the rest of the app does not require
    `ultralytics` unless the user explicitly trains a model.
    """
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - requires the optional training dependency.
        raise RuntimeError(
            "`ultralytics` is not installed. Install it with `pip install ultralytics` before training."
        ) from exc

    root = Path(dataset_root)
    data_yaml = root / "data.yaml"
    if not data_yaml.exists():
        build_demo_dataset(dataset_root)

    model_runner = YOLO(model)
    results = model_runner.train(data=str(data_yaml), epochs=epochs, imgsz=imgsz, project=str(root / "runs"), name="atcg")
    weights = str(root / "runs" / "atcg" / "weights" / "best.pt")
    return {
        "weights": weights,
        "dataset": str(data_yaml),
        "results": str(results),
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train a YOLO model to detect ATCG letters in annotated images.")
    parser.add_argument("--dataset-dir", default="./data/atcg_yolo", help="Directory for the generated YOLO dataset")
    parser.add_argument("--examples-per-base", type=int, default=2, help="Number of examples to create per base")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs for Ultralytics YOLO")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size used during training")
    parser.add_argument("--train", action="store_true", help="Run YOLO training after generating the dataset")
    return parser


if __name__ == "__main__":
    parser = _build_arg_parser()
    args = parser.parse_args()
    dataset = build_demo_dataset(args.dataset_dir, examples_per_base=args.examples_per_base)
    print(json.dumps({"status": "dataset_ready", **dataset, "dataset_dir": args.dataset_dir}, indent=2))
    if args.train:
        model_info = train_atcg_yolo(args.dataset_dir, epochs=args.epochs, imgsz=args.imgsz)
        print(json.dumps({"status": "training_complete", **model_info}, indent=2))
