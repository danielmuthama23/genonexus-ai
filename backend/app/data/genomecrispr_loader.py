import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def _candidate_paths() -> List[Path]:
    root = Path(__file__).resolve().parents[3]
    return [
        root / "GenomeCRISPR_full.csv" / "GenomeCRISPR.csv",
        root / "GenomeCRISPR.csv",
        root / "GenomeCRISPR_full.csv" / "genomecrispr.csv",
        root / "genomecrispr.csv",
    ]


def _coerce_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _coerce_int_list(value: Any) -> List[int]:
    if value is None or value == "":
        return []
    text = str(value).strip()
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1]
    if not text:
        return []
    out: List[int] = []
    for part in text.split(","):
        cleaned = part.strip().replace("{", "").replace("}", "")
        if not cleaned:
            continue
        try:
            out.append(int(float(cleaned)))
        except ValueError:
            continue
    return out


def _resolve_dataset_path() -> Path:
    for path in _candidate_paths():
        if path.exists():
            return path
    raise FileNotFoundError(
        "GenomeCRISPR dataset not found. Expected GenomeCRISPR.csv or GenomeCRISPR_full.csv/GenomeCRISPR.csv in the project root."
    )


def load_genomecrispr_records(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load the real CRISPR screening dataset and normalize each row for downstream task execution."""
    path = _resolve_dataset_path()
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            sequence = (row.get("sequence") or "").strip()
            if not sequence:
                continue
            record = {
                "start": _coerce_int(row.get("start")),
                "end": _coerce_int(row.get("end")),
                "chr": (row.get("chr") or "").strip(),
                "strand": (row.get("strand") or "").strip(),
                "pubmed": _coerce_int(row.get("pubmed")),
                "cellline": (row.get("cellline") or "").strip(),
                "condition": (row.get("condition") or "").strip(),
                "sequence": sequence,
                "symbol": (row.get("symbol") or "").strip(),
                "ensg": (row.get("ensg") or "").strip(),
                "log2fc": _coerce_float(row.get("log2fc")),
                "rc_initial": _coerce_int_list(row.get("rc_initial")),
                "rc_final": _coerce_int_list(row.get("rc_final")),
                "effect": _coerce_int(row.get("effect")),
                "cas": (row.get("cas") or "").strip(),
                "screentype": (row.get("screentype") or "").strip(),
            }
            rows.append(record)
            if limit is not None and len(rows) >= limit:
                break
    return rows


def build_task_queue(limit: int = 10) -> List[Dict[str, Any]]:
    """Build a realistic, dataset-backed task queue for downstream simulation steps."""
    rows = load_genomecrispr_records(limit=limit)
    tasks: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        tasks.append({
            "id": f"task-{idx:03d}",
            "gene": row["symbol"],
            "chr": row["chr"],
            "strand": row["strand"],
            "sequence": row["sequence"],
            "effect": row["effect"],
            "log2fc": row["log2fc"],
            "cas": row["cas"],
            "screen_type": row["screentype"],
            "status": "ready",
        })
    return tasks
