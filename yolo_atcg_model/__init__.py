"""ATCG medical YOLO training pipeline."""

__all__ = [
    "ATCG_CLASSES",
    "CLASS_TO_IDX",
    "generate_dataset",
    "train_model",
    "run_inference",
    "prepare_input_image",
]


def __getattr__(name):
    if name in {"ATCG_CLASSES", "CLASS_TO_IDX", "generate_dataset"}:
        from .dataset import ATCG_CLASSES, CLASS_TO_IDX, generate_dataset
        if name == "ATCG_CLASSES":
            return ATCG_CLASSES
        if name == "CLASS_TO_IDX":
            return CLASS_TO_IDX
        return generate_dataset
    if name == "train_model":
        from .train import train_model
        return train_model
    if name == "run_inference":
        from .infer import run_inference
        return run_inference
    if name == "prepare_input_image":
        from .infer import prepare_input_image
        return prepare_input_image
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
