"""
Molecule Construction Lab — backend counterpart to the frontend's interactive
3D molecule builder. Atoms and bonds the user places are assembled into a
REAL RDKit molecule (RWMol), sanitized (which validates chemical valence and
fills in implicit hydrogens exactly like a real cheminformatics toolkit),
and then scored with the same descriptor pipeline used for the compound
library. Invalid structures (e.g. a carbon with 5 bonds) are rejected with a
real chemistry error, not silently accepted.

This does NOT predict binding, synthesizability, or real-world efficacy —
it tells you whether what you built is a valid molecule and what its basic
physicochemical profile looks like.
"""
from typing import List, Tuple
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors

from .drug_service import lipinski_pass, seeded_score

ATOMIC_NUM = {"C": 6, "N": 7, "O": 8, "S": 16, "F": 9, "Cl": 17, "Br": 35, "P": 15, "H": 1}
BOND_MAP = {1: Chem.BondType.SINGLE, 2: Chem.BondType.DOUBLE, 3: Chem.BondType.TRIPLE}


class InvalidMoleculeError(Exception):
    pass


def build_and_score(atoms: List[str], bonds: List[Tuple[int, int, int]],
                     name: str = "Custom molecule", target_gene: str = None):
    """
    atoms: element symbols in placement order, e.g. ["C","C","O"]
    bonds: (atom_index_a, atom_index_b, bond_order) triples, 0-indexed,
           bond_order in {1,2,3}
    """
    if not atoms:
        raise InvalidMoleculeError("Place at least one atom before scoring.")

    mol = Chem.RWMol()
    for el in atoms:
        if el not in ATOMIC_NUM:
            raise InvalidMoleculeError(f"Unsupported element: {el}")
        mol.AddAtom(Chem.Atom(ATOMIC_NUM[el]))

    for (i, j, order) in bonds:
        if i >= len(atoms) or j >= len(atoms):
            raise InvalidMoleculeError(f"Bond references an atom that doesn't exist ({i}-{j}).")
        mol.AddBond(i, j, BOND_MAP.get(order, Chem.BondType.SINGLE))

    plain_mol = mol.GetMol()
    try:
        Chem.SanitizeMol(plain_mol)
    except Exception as e:
        raise InvalidMoleculeError(
            f"That arrangement isn't a valid molecule: {str(e)}"
        )

    smiles = Chem.MolToSmiles(plain_mol)
    formula = rdMolDescriptors.CalcMolFormula(plain_mol)

    result = {
        "name": name,
        "smiles": smiles,
        "formula": formula,
        "mw": round(Descriptors.MolWt(plain_mol), 2),
        "logp": round(Descriptors.MolLogP(plain_mol), 2),
        "hbd": Lipinski.NumHDonors(plain_mol),
        "hba": Lipinski.NumHAcceptors(plain_mol),
        "tpsa": round(Descriptors.TPSA(plain_mol), 1),
        "rotb": Descriptors.NumRotatableBonds(plain_mol),
        "num_heavy_atoms": plain_mol.GetNumHeavyAtoms(),
        "ro5_pass": lipinski_pass({
            "mw": Descriptors.MolWt(plain_mol),
            "logp": Descriptors.MolLogP(plain_mol),
            "hbd": Lipinski.NumHDonors(plain_mol),
            "hba": Lipinski.NumHAcceptors(plain_mol),
        }),
    }
    if target_gene:
        result["target_gene"] = target_gene
        result["affinity_score"] = seeded_score(name, target_gene)
    return result
