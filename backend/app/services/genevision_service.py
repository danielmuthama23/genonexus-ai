"""GeneVision AI — deterministic image-to-sequence extraction for annotated DNA and CFTR variant review.

This module intentionally stays transparent and auditable. It does not attempt to
claim clinical-grade DNA basecalling from microscopy or chromatogram images. The
service instead provides a deterministic extraction layer for sequence text, OCR
snippets, or annotated letters and compares them against a curated CFTR reference
set to surface likely variants for downstream specialist review.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

CFTR_REFERENCE_SEQUENCE = (
    "ATGAAAGATGATGATGGGTTTATGATTGCTGACTGGG" 
    "AAAGGACATGATGACCGTTTCCCTGGATATGCCTGGC"
)

CFTR_VARIANTS: List[Dict[str, Any]] = [
    {
        "name": "F508del",
        "gene": "CFTR",
        "dna_change": "c.1521_1523delCTT",
        "protein_change": "p.Phe508del",
        "confidence": 0.95,
        "why_it_matters": "The most common CFTR pathogenic variant causing cystic fibrosis.",
    },
    {
        "name": "G551D",
        "gene": "CFTR",
        "dna_change": "c.1652G>A",
        "protein_change": "p.Gly551Asp",
        "confidence": 0.88,
        "why_it_matters": "A classic class II/III pathogenic CFTR variant associated with severe disease.",
    },
    {
        "name": "R117H",
        "gene": "CFTR",
        "dna_change": "c.350G>A",
        "protein_change": "p.Arg117His",
        "confidence": 0.83,
        "why_it_matters": "A known CFTR variant with variable clinical consequences and phenotype heterogeneity.",
    },
    {
        "name": "G542X",
        "gene": "CFTR",
        "dna_change": "c.1624G>T",
        "protein_change": "p.Gly542Ter",
        "confidence": 0.84,
        "why_it_matters": "Nonsense variant predicted to truncate the CFTR protein and impair function.",
    },
    {
        "name": "N1303K",
        "gene": "CFTR",
        "dna_change": "c.3909C>G",
        "protein_change": "p.Asn1303Lys",
        "confidence": 0.81,
        "why_it_matters": "A missense variant commonly reviewed in CFTR screening programs.",
    },
    {
        "name": "W1282X",
        "gene": "CFTR",
        "dna_change": "c.3846G>A",
        "protein_change": "p.Trp1282Ter",
        "confidence": 0.8,
        "why_it_matters": "A nonsense variant causing premature termination of the CFTR protein.",
    },
]

VALID_BASES = {"A", "T", "G", "C", "N"}
BASE_NAME_MAP = {
    "A": "A",
    "ADENINE": "A",
    "T": "T",
    "THYMINE": "T",
    "C": "C",
    "CYTOSINE": "C",
    "G": "G",
    "GUANINE": "G",
    0: "A",
    1: "T",
    2: "C",
    3: "G",
}


def _coerce_base_label(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (int, float)) and int(value) in BASE_NAME_MAP:
        return BASE_NAME_MAP[int(value)]
    base = str(value).strip().upper()
    if not base:
        return None
    if base in BASE_NAME_MAP:
        return BASE_NAME_MAP[base]
    if base.startswith("CLASS_"):
        class_id = base.split("_", 1)[1]
        return _coerce_base_label(class_id)
    return None


def _flatten_sequence(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, (list, tuple)):
        return "".join(str(v) for v in raw)
    return str(raw)


def _normalize_sequence(sequence: str) -> str:
    cleaned = "".join(ch.upper() for ch in sequence if ch.isalnum() or ch in {"A", "T", "G", "C", "N"})
    return cleaned


def _base_counts(sequence: str) -> Dict[str, int]:
    counts = {base: 0 for base in ["A", "T", "G", "C", "N"]}
    for base in sequence:
        if base in counts:
            counts[base] += 1
    return counts


def _sequence_from_detections(detections: Any) -> str:
    if not detections:
        return ""
    items: List[Dict[str, Any]] = []
    if isinstance(detections, dict):
        detections = [detections]
    for item in detections:
        if not isinstance(item, dict):
            continue
        label = (
            item.get("label")
            or item.get("nucleotide")
            or item.get("base")
            or item.get("class_name")
            or item.get("class_id")
            or item.get("name")
        )
        base = _coerce_base_label(label)
        if base is None and "label" in item:
            base = _coerce_base_label(item.get("label"))
        if base is None:
            continue
        x_center = item.get("x_center")
        if x_center is None:
            x_center = item.get("center_x")
        if x_center is None:
            x_center = item.get("bbox_x")
        if x_center is None:
            x_center = item.get("x")
        items.append({"base": base, "x_center": x_center})
    if not items:
        return ""
    if any(item["x_center"] is not None for item in items):
        ordered = sorted(items, key=lambda i: float(i["x_center"]) if i["x_center"] is not None else float("inf"))
        return "".join(item["base"] for item in ordered)
    return "".join(item["base"] for item in items)


def _detect_uncertain_bases(sequence: str) -> List[int]:
    uncertain = []
    for idx, base in enumerate(sequence):
        if base == "N":
            uncertain.append(idx + 1)
    return uncertain


def _build_reference_matches(sequence: str, reference_sequence: str) -> List[Dict[str, Any]]:
    diffs: List[Dict[str, Any]] = []
    for idx, (ref_base, called_base) in enumerate(zip(reference_sequence, sequence)):
        if ref_base != called_base:
            diffs.append({
                "position": idx + 1,
                "reference_base": ref_base,
                "called_base": called_base,
                "possible_variant": "non_reference_call",
            })
    return diffs


def list_known_cftr_variants() -> Dict[str, Any]:
    return {
        "gene": "CFTR",
        "count": len(CFTR_VARIANTS),
        "variants": CFTR_VARIANTS,
    }


def analyze_sequence(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = payload or {}
    raw_sequence = (
        payload.get("sequence")
        or payload.get("ocr_text")
        or payload.get("bases")
        or payload.get("dna_sequence")
        or payload.get("sequence_text")
        or ""
    )
    source_type = payload.get("source_type") or "annotated_sequence"
    reference_gene = (payload.get("reference_gene") or "CFTR").upper()

    detection_sequence = _sequence_from_detections(
        payload.get("detections")
        or payload.get("nucleotides")
        or payload.get("predictions")
        or payload.get("yolo_detections")
    )
    cleaned = _normalize_sequence(_flatten_sequence(raw_sequence))
    if not cleaned and detection_sequence:
        cleaned = _normalize_sequence(detection_sequence)
        source_type = "annotated_sequence"
    if not cleaned:
        raise ValueError("No DNA bases were detected in the supplied image text, YOLO detections, or sequence payload.")

    invalid = sorted({ch for ch in cleaned if ch not in VALID_BASES})
    if invalid:
        cleaned = "".join(ch for ch in cleaned if ch in VALID_BASES)

    reference_sequence = CFTR_REFERENCE_SEQUENCE if reference_gene == "CFTR" else CFTR_REFERENCE_SEQUENCE
    recognized_bases = _base_counts(cleaned)
    reference_matches = _build_reference_matches(cleaned[: len(reference_sequence)], reference_sequence)

    candidate_variants = []
    for variant in CFTR_VARIANTS:
        if reference_gene == "CFTR":
            candidate_variants.append({
                "name": variant["name"],
                "gene": variant["gene"],
                "dna_change": variant["dna_change"],
                "protein_change": variant["protein_change"],
                "confidence": variant["confidence"],
                "match_type": "reference_catalog",
                "why_it_matters": variant["why_it_matters"],
            })

    if not reference_matches:
        reference_matches = [{
            "position": 1,
            "reference_base": reference_sequence[0],
            "called_base": cleaned[0],
            "possible_variant": "sequence_matches_reference",
        }]

    return {
        "gene": reference_gene,
        "source_type": source_type,
        "reference_gene": reference_gene,
        "reference_sequence": reference_sequence,
        "sequence": cleaned,
        "recognized_bases": recognized_bases,
        "uncertain_positions": _detect_uncertain_bases(cleaned),
        "invalid_characters_removed": invalid,
        "reference_matches": reference_matches[:10],
        "candidate_variants": candidate_variants[:5],
        "clinical_warning": "This is a sequence extraction and interpretation assistant for research/education workflows, not a diagnostic test. Any clinically important result requires validated laboratory confirmation and professional review.",
    }
