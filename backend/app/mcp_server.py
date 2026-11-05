"""
CRISPR-X Nexus MCP server — exposes the same backend capabilities (disease
scanning, CRISPR editing, drug ranking, molecule building, survival
simulation, audit ledger, and genomic-risk workflows) as MCP tools using the
official `mcp` Python SDK's FastMCP interface, so any MCP-compatible client
(Claude, or another agent) can drive this platform directly instead of only a
human clicking buttons.

Run standalone for local testing (stdio transport):
    python -m app.mcp_server

Or mount it alongside the FastAPI app / register it with an MCP-aware host.
"""
from typing import List, Optional, Tuple

from mcp.server.fastmcp import FastMCP

from .data.disease_db import DISEASE_DB, REFERENCE_SEQUENCE, find_disease
from .data import synthetic
from .services import genome_service, disease_service, drug_service, molecule_lab_service, survival_service
from .services.ledger_service import ledger

mcp = FastMCP(
    name="crispr-x-nexus",
    instructions=(
        "Tools for the CRISPR-X Nexus genomic risk intelligence platform. "
        "All data is synthetic/illustrative unless a user provides their own approved data source."
    ),
)


@mcp.tool()
def get_reference_sequence() -> dict:
    """Return the 40bp simplified reference DNA sequence used throughout the demo."""
    return {"sequence": "".join(REFERENCE_SEQUENCE), "length": len(REFERENCE_SEQUENCE)}


@mcp.tool()
def list_diseases() -> list:
    """List the 6 hand-written disease/mutation reference entries (not ClinVar/OMIM)."""
    return DISEASE_DB


@mcp.tool()
def scan_sequence_for_mutations(sequence: str) -> list:
    """Scan a DNA sequence (string of A/T/C/G) against the disease reference
    table and report which known mutation positions match."""
    return disease_service.scan(list(sequence))


@mcp.tool()
def design_grna(sequence: str, position: int) -> dict:
    """Design a guide RNA window and locate the nearest downstream PAM (NGG)
    site for a Cas9 cut at `position` (0-indexed) in `sequence`."""
    return genome_service.design_grna(list(sequence), position)


@mcp.tool()
def crispr_repair(sequence: str, position: int, normal_base: str, mutant_base: str,
                   strategy: str) -> dict:
    """Simulate a CRISPR repair at `position`. `strategy` is one of:
    hdr (precise), nhej (imprecise indel risk), base (single transition edit),
    prime (precise multi-base). Returns the edited sequence and outcome message."""
    seq, msg = genome_service.repair(list(sequence), position, normal_base, mutant_base, strategy)
    return {"sequence": "".join(seq), "message": msg}


@mcp.tool()
def rank_drug_candidates(target_gene: str) -> list:
    """Rank the fictional 8-compound library against a target gene using real
    RDKit descriptors (MW, LogP, HBD, HBA, TPSA, rotatable bonds) plus a
    deterministic placeholder affinity score. NOT real docking/AlphaFold."""
    return drug_service.rank_compounds(target_gene)


@mcp.tool()
def build_custom_molecule(atoms: List[str], bonds: List[Tuple[int, int, int]],
                           name: str = "Custom molecule", target_gene: Optional[str] = None) -> dict:
    """Build a real molecule from atoms (element symbols, e.g. ['C','C','O'])
    and bonds (atom_index_a, atom_index_b, bond_order) using RDKit, which
    validates chemical valence and computes real descriptors. Raises a
    chemistry error if the structure is invalid (e.g. a carbon with 5 bonds)."""
    try:
        return molecule_lab_service.build_and_score(atoms, bonds, name, target_gene)
    except molecule_lab_service.InvalidMoleculeError as e:
        return {"error": str(e)}


@mcp.tool()
def run_survival_simulation(efficacy: float, n_per_arm: int = 40, followup_months: int = 24,
                             seed: Optional[int] = None) -> dict:
    """Run a Kaplan-Meier + log-rank simulation comparing a treatment arm
    (hazard reduced by `efficacy`, 0-1) against a control arm. Survival times
    are SIMULATED (exponential distribution), not real patient outcomes."""
    return survival_service.run_simulation(efficacy=efficacy, n_per_arm=n_per_arm,
                                            followup_months=followup_months, seed=seed)


@mcp.tool()
def generate_synthetic_cohort(n: int = 6, seed: int = 42) -> list:
    """Generate a synthetic (non-real) patient cohort for trial simulation."""
    return synthetic.generate_cohort(n=n, seed=seed)


@mcp.tool()
def ledger_append_action(action: str, data: dict) -> dict:
    """Append a new block to the local SHA-256 hash-chain audit ledger."""
    return ledger.append(action, data)


@mcp.tool()
def ledger_verify_chain() -> dict:
    """Recompute every hash in the audit ledger and confirm the chain is unbroken."""
    return ledger.verify()


@mcp.tool()
def ledger_history() -> list:
    """Return the full audit ledger."""
    return ledger.chain


if __name__ == "__main__":
    mcp.run()
