"""
Drug candidate scoring — real RDKit molecular descriptors, plus a seeded
(deterministic, not random-random) affinity placeholder. This mirrors the
frontend's seededScore()/Lipinski check exactly so both sides produce
identical numbers for the same compound/gene pair.

IMPORTANT: "affinity_score" is NOT real docking or AlphaFold-grade binding
prediction. It's a deterministic hash-based placeholder used purely so the
demo has a stable, explorable ranking. Real virtual screening needs
AutoDock Vina / DiffDock against an actual target structure.
"""
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski

from ..data.compound_db import COMPOUND_SMILES


def compute_descriptors(name: str, smiles: str):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES for {name}: {smiles}")
    return {
        "name": name,
        "smiles": smiles,
        "mw": round(Descriptors.MolWt(mol), 1),
        "logp": round(Descriptors.MolLogP(mol), 2),
        "hbd": Lipinski.NumHDonors(mol),
        "hba": Lipinski.NumHAcceptors(mol),
        "tpsa": round(Descriptors.TPSA(mol), 1),
        "rotb": Descriptors.NumRotatableBonds(mol),
    }


def lipinski_pass(d: dict) -> bool:
    return d["mw"] <= 500 and d["logp"] <= 5 and d["hbd"] <= 5 and d["hba"] <= 10


def seeded_score(name: str, target_gene: str) -> int:
    """Deterministic hash identical to the frontend's seededScore(): a 31-multiplier
    rolling hash over `name + target`, folded into a 30-97 range."""
    s = name + target_gene
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return 30 + (h % 68)


def rank_compounds(target_gene: str):
    ranked = []
    for name, info in COMPOUND_SMILES.items():
        desc = compute_descriptors(name, info["smiles"])
        desc["tags"] = info["tags"]
        desc["relevant"] = target_gene in info["tags"]
        desc["ro5_pass"] = lipinski_pass(desc)
        desc["affinity_score"] = seeded_score(name, target_gene)
        ranked.append(desc)
    ranked.sort(key=lambda c: (c["relevant"], c["affinity_score"]), reverse=True)
    return ranked


def score_custom_compound(name: str, smiles: str, target_gene: str):
    desc = compute_descriptors(name, smiles)
    desc["ro5_pass"] = lipinski_pass(desc)
    desc["affinity_score"] = seeded_score(name, target_gene)
    return desc
