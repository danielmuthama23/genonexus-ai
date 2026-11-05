# ATCG Medical YOLO Model

This directory provides a reusable training pipeline for a YOLO-based model that detects A, T, C, and G nucleotides in annotated medical images.

## Folder contents

- `dataset.py` — generates a synthetic YOLO dataset with bounding boxes for nucleotide glyphs.
- `train.py` — trains a real Ultralytics YOLO model.
- `infer.py` — runs inference on a single image.
- `requirements.txt` — library dependencies for training and inference.

## Quick start

```bash
cd /home/dti/Documents/dan_soi-code/GenoNexus\ AI
python3 -m pip install -r yolo_atcg_model/requirements.txt
python3 -m yolo_atcg_model.dataset --dataset-root ./datasets/atcg_yolo --images-per-class 60
python3 -m yolo_atcg_model.train --dataset-root ./datasets/atcg_yolo --epochs 30 --imgsz 1024
python3 -m yolo_atcg_model.infer --model ./datasets/atcg_yolo/runs/atcg_medical_model/weights/best.pt --image ./sample.png
```

## Recommended use

1. Collect or annotate nucleotide images in YOLO format.
2. Place them into a dataset folder with `images/train`, `images/val`, and `data.yaml`.
3. Train the model with `train.py`.
4. Use `infer.py` to detect bases in new images.
5. Export the trained weights and use them as the primary ATCG detection model in the larger GenoNexus pipeline.

## Notes

This project intentionally keeps the training dependency optional. The dataset generator works without Ultralytics, while the training and inference scripts import Ultralytics only when the user explicitly runs model training or prediction.
