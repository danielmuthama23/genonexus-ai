#!/usr/bin/env python3
"""Inference script for the trained ATCG YOLO model."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def prepare_input_image(image_path: str | Path) -> str:
    """Normalize a PDF or image upload into a PNG file that YOLO can analyze."""
    source = Path(image_path)
    if not source.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")

    suffix = source.suffix.lower()
    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        return str(source)

    if suffix != ".pdf":
        raise ValueError(
            f"Unsupported input type: {suffix}. Upload a PNG, JPG, or PDF file containing the DNA helix."
        )

    target = source.with_name(f"{source.stem}_converted.png")

    for module_name in ("fitz", "pymupdf", "pypdfium2"):
        try:
            module = __import__(module_name)
        except ImportError:
            continue

        if module_name in {"fitz", "pymupdf"}:
            document = module.open(str(source))
            try:
                page = document[0]
                pixmap = page.get_pixmap(matrix=module.Matrix(2, 2))
                pixmap.save(str(target))
                return str(target)
            finally:
                document.close()

        if module_name == "pypdfium2":
            document = module.PdfDocument(str(source))
            try:
                page = document[0]
                image = page.render(scale=2)
                rendered = image.to_pil()
                rendered.save(str(target))
                return str(target)
            finally:
                document.close()

    pdftocairo = shutil.which("pdftocairo")
    if pdftocairo:
        subprocess.run(
            [pdftocairo, "-png", str(source), str(target.with_suffix(""))],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        converted = target.with_name(f"{source.stem}_converted-1.png")
        if converted.exists():
            return str(converted)

    raise RuntimeError(
        "PDF conversion is required for this workflow but no PDF renderer was found. "
        "Install PyMuPDF (pip install pymupdf) or pdftocairo to enable PDF uploads."
    )


def run_inference(model_path: str, image_path: str, conf: float = 0.25) -> list[dict]:
    """Run YOLO prediction on a PNG or PDF input and return detection objects."""
    image_file = prepare_input_image(image_path)
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - optional dependency for inference.
        raise RuntimeError("ultralytics is not installed. Run: pip install ultralytics") from exc

    model = YOLO(model_path)
    results = model(str(image_file), conf=conf, verbose=False)
    detections: list[dict] = []

    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
            label = result.names.get(cls_id, str(cls_id))
            detections.append(
                {
                    "label": label,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2],
                    "class_id": cls_id,
                }
            )
    return detections


def main() -> None:
    parser = argparse.ArgumentParser(description="Run inference with a trained ATCG YOLO model.")
    parser.add_argument("--model", required=True, help="Path to best.pt model file")
    parser.add_argument("--image", required=True, help="PNG, JPG, or PDF file to analyze")
    parser.add_argument("--conf", type=float, default=0.25, help="Minimum confidence threshold")
    args = parser.parse_args()

    detections = run_inference(args.model, args.image, conf=args.conf)
    for item in detections:
        print(item)


if __name__ == "__main__":
    main()
