"""
Synthetic data generation — patient cohorts and sequencing reads. No real
patients, no real PII, ever. Seeded RNG for reproducibility on request.
"""
import random


def generate_cohort(n: int = 6, seed: int = 42, dose_label: str = "Single ascending dose"):
    rng = random.Random(seed)
    cohort = []
    for i in range(1, n + 1):
        cohort.append({
            "id": f"PT-{i:03d}",
            "age": rng.randint(22, 66),
            "sex": rng.choice(["F", "M"]),
            "consented": rng.random() > 0.15,
            "dose": dose_label,
            "ae": [],
        })
    return cohort


def generate_reads(reference: list, n_samples: int = 6, error_rate: float = 0.04, seed: int = 7):
    """Simulate short sequencing reads by injecting random single-base errors
    into copies of the reference sequence — a deliberately simplified stand-in
    for a real variant caller (e.g. GATK, DeepVariant)."""
    rng = random.Random(seed)
    bases = ["A", "T", "C", "G"]
    reads = []
    for i in range(n_samples):
        read = []
        for b in reference:
            if rng.random() < error_rate:
                alts = [x for x in bases if x != b]
                read.append(rng.choice(alts))
            else:
                read.append(b)
        reads.append({"id": f"READ-{i+1:02d}", "bases": read})
    return reads
