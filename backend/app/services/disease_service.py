"""
Mutation scanning against the reference disease table — mirrors the
frontend's scanDiseases() logic exactly.
"""
from typing import List
from ..data.disease_db import DISEASE_DB


def scan(sequence: List[str]):
    results = []
    for d in DISEASE_DB:
        current = sequence[d["pos"]]
        is_match = current == d["mutant"]
        confidence = (88 + (d["pos"] % 9)) if is_match else 0
        results.append({
            **d,
            "current_base": current,
            "match": is_match,
            "confidence": confidence,
        })
    return results


def active_matches(sequence: List[str]):
    return [r for r in scan(sequence) if r["match"]]
