"""
Fictional candidate molecules (NOT existing approved drugs) with valid,
computable SMILES structures. Real RDKit descriptors are computed at request
time in drug_service.py — nothing here is a hardcoded/made-up number.
"""

COMPOUND_SMILES = {
    "Voxelamine":   {"smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)NCCN",                       "tags": ["HBB", "CFTR"]},
    "Fentrostat":   {"smiles": "COc1ccc(cc1)CCNC(=O)c1ccc(Cl)cc1OC",                  "tags": ["CFTR"]},
    "Kerabinol":    {"smiles": "OCC1OC(O)C(O)C(O)C1O",                               "tags": ["HBB"]},
    "Ondaprexil":   {"smiles": "CC1=NN(C(=O)C1)c1ccc(cc1)S(=O)(=O)N1CCCCC1",          "tags": ["BRCA1"]},
    "Nucleoflavin": {"smiles": "Cc1cc2nc3c(nc(=O)[nH]c3=O)n(CC(O)C(O)C(O)CO)c2cc1C",  "tags": ["HTT", "BRCA1"]},
    "Thiazolamex":  {"smiles": "Cc1nc(cs1)C(=O)Nc1ccc(cc1)S(N)(=O)=O",                "tags": ["G6PD"]},
    "Corvexanide":  {"smiles": "CCN(CC)CCNC(=O)c1ccc(cc1)Nc1ncccn1",                   "tags": ["CFTR", "HBB"]},
    "Plicatannin":  {"smiles": "Oc1ccc(cc1)C1Oc2cc(O)cc(O)c2C(=O)C1O",                "tags": ["BRCA1", "HTT"]},
}
