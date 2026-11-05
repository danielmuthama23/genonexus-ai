"""
CRISPR editing logic — gRNA design, PAM search, cut simulation, and repair
strategies (HDR / NHEJ / base editing / prime editing). This mirrors the JS
implementation in the frontend 1:1 so both sides agree on behavior; it is a
teaching-grade simplification, not a real design tool.
"""
import random
from typing import List, Literal

RepairStrategy = Literal["hdr", "nhej", "base", "prime"]


def design_grna(sequence: List[str], pos: int):
    """Return the 20nt guide window and the position of the nearest downstream
    PAM (NGG) site, mirroring the frontend's window/search logic exactly."""
    start = max(0, pos - 17)
    upstream = "".join(sequence[start:pos + 3])
    pam_found = None
    for i in range(pos, min(len(sequence) - 2, pos + 6)):
        if sequence[i + 1] == "G" and sequence[i + 2] == "G":
            pam_found = i + 1
            break
    return {"grna_window": upstream, "pam_position": pam_found}


def cut(sequence: List[str], pos: int):
    """Cas9 double-strand cut at `pos` — returns a copy annotated with the cut
    index; no bases change yet (repair happens separately, same as the UI)."""
    return {"sequence": list(sequence), "cut_index": pos}


def is_transition(mutant: str, normal: str) -> bool:
    transitions = {("A", "G"), ("C", "T"), ("G", "A"), ("T", "C")}
    return (mutant, normal) in transitions


def repair(sequence: List[str], pos: int, normal: str, mutant: str,
           strategy: RepairStrategy, rng: random.Random = None):
    """Apply a repair strategy at `pos`. Returns (new_sequence, message)."""
    rng = rng or random.Random()
    seq = list(sequence)

    if strategy == "hdr":
        seq[pos] = normal
        msg = f"HDR template repaired position {pos + 1} \u2192 {normal} (precise)"

    elif strategy == "nhej":
        success = rng.random() > 0.5
        seq[pos] = normal if success else "N"
        msg = (f"NHEJ closed the break cleanly at position {pos + 1}" if success
               else f"NHEJ introduced a small indel at position {pos + 1} (imprecise repair)")

    elif strategy == "base":
        if is_transition(mutant, normal):
            seq[pos] = normal
            msg = f"Base editor converted {mutant}\u2192{normal} at position {pos + 1} without a double-strand break"
        else:
            msg = (f"Base editing can't perform {mutant}\u2192{normal} directly "
                   f"(needs a transition, not transversion) \u2014 try HDR or prime editing")

    elif strategy == "prime":
        seq[pos] = normal
        msg = f"Prime editor (pegRNA + reverse transcriptase) precisely wrote {normal} at position {pos + 1}"

    else:
        raise ValueError(f"Unknown repair strategy: {strategy}")

    return seq, msg
