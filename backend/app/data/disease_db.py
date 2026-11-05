"""
Disease reference table — mirrors DISEASE_DB in the frontend exactly so the
backend and browser app always agree on positions/mutations. This is a small,
hand-written table (6 entries) for teaching purposes, NOT a ClinVar/OMIM/gnomAD
lookup.
"""

REFERENCE_SEQUENCE = list("ATGGTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTG")  # 40 bp

DISEASE_DB = [
    {
        "id": "sca", "name": "Sickle Cell Disease", "gene": "HBB", "chrom": "11p15.4",
        "pos": 6, "normal": "A", "mutant": "T",
        "mut_type": "Missense (Glu→Val)", "severity": "high",
        "inheritance": "Autosomal recessive", "freq": "~1/365 (African ancestry)",
        "note": "A single base change alters codon 6 of beta-globin, causing "
                "hemoglobin to polymerize under low oxygen.",
    },
    {
        "id": "cf", "name": "Cystic Fibrosis (\u0394F508-like)", "gene": "CFTR", "chrom": "7q31.2",
        "pos": 15, "normal": "G", "mutant": "C",
        "mut_type": "Frameshift-adjacent", "severity": "high",
        "inheritance": "Autosomal recessive", "freq": "~1/2,500 (European ancestry)",
        "note": "Disrupts chloride channel folding, thickening mucus in lungs and pancreas.",
    },
    {
        "id": "thal", "name": "Beta Thalassemia", "gene": "HBB", "chrom": "11p15.4",
        "pos": 22, "normal": "A", "mutant": "G",
        "mut_type": "Splice-site", "severity": "med",
        "inheritance": "Autosomal recessive", "freq": "~1/100,000 globally",
        "note": "Reduces beta-globin production, causing anemia of varying severity.",
    },
    {
        "id": "hd", "name": "Huntington Disease (marker)", "gene": "HTT", "chrom": "4p16.3",
        "pos": 28, "normal": "T", "mutant": "C",
        "mut_type": "Regulatory-region marker", "severity": "high",
        "inheritance": "Autosomal dominant", "freq": "~1/10,000-20,000",
        "note": "Real HD is caused by CAG repeat expansion; this position is a "
                "simplified stand-in for demo purposes.",
    },
    {
        "id": "brca", "name": "BRCA1-associated risk", "gene": "BRCA1", "chrom": "17q21.31",
        "pos": 33, "normal": "C", "mutant": "T",
        "mut_type": "Missense", "severity": "med",
        "inheritance": "Autosomal dominant", "freq": "~1/400 carriers",
        "note": "Elevates lifetime risk of breast and ovarian cancer; penetrance varies by variant.",
    },
    {
        "id": "g6pd", "name": "G6PD Deficiency", "gene": "G6PD", "chrom": "Xq28",
        "pos": 38, "normal": "G", "mutant": "A",
        "mut_type": "Missense", "severity": "low",
        "inheritance": "X-linked recessive", "freq": "~400M people worldwide",
        "note": "Reduces red blood cell resistance to oxidative stress; usually mild, "
                "triggered by certain drugs/foods.",
    },
]


def find_disease(disease_id: str):
    return next((d for d in DISEASE_DB if d["id"] == disease_id), None)
