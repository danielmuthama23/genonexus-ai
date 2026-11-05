#!/usr/bin/env python3
"""Training entry point for the ATCG medical YOLO model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

try:
    from .dataset import generate_dataset
except ImportError:  # pragma: no cover - allows direct script execution.
    from dataset import generate_dataset


def train_model(
    dataset_root: str,
    model: str = "yolov8n.pt",
    epochs: int = 30,
    imgsz: int = 1024,
    batch: int = 8,
    project: str | None = None,
    name: str = "atcg_medical_model",
) -> Dict[str, str]:
    """Train a real Ultralytics YOLO model on the generated ATCG dataset."""
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - optional dependency for training.
        raise RuntimeError("ultralytics is not installed. Run: pip install ultralytics") from exc

    root = Path(dataset_root)
    data_yaml = root / "data.yaml"
    if not data_yaml.exists():
        generate_dataset(str(root))

    project_dir = Path(project) if project else root / "runs"
    model_runner = YOLO(model)
    model_runner.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=str(project_dir),
        name=name,
        exist_ok=True,
    )

    weights_path = project_dir / name / "weights" / "best.pt"
    return {
        "weights": str(weights_path),
        "dataset": str(data_yaml),
        "project": str(project_dir),
        "name": name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a YOLO model to detect A/T/C/G nucleotides in annotated images.")
    parser.add_argument("--dataset-root", default="./datasets/atcg_yolo", help="Dataset directory")
    parser.add_argument("--model", default="yolov8n.pt", help="Ultralytics model checkpoint to start from")
    parser.add_argument("--epochs", type=int, default=30, help="Training epochs")
    parser.add_argument("--imgsz", type=int, default=1024, help="Image size for training")
    parser.add_argument("--batch", type=int, default=8, help="Batch size")
    parser.add_argument("--project", default=None, help="Directory to store training artifacts")
    parser.add_argument("--name", default="atcg_medical_model", help="Run name for the training output")
    args = parser.parse_args()

    result = train_model(
        dataset_root=args.dataset_root,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
    )
    print(json.dumps({"status": "training_complete", **result}, indent=2))


if __name__ == "__main__":
    main()
