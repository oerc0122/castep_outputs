"""
Parse the following castep outputs:
.magres
"""
from collections import defaultdict
from typing import Dict, TextIO, Tuple, TypedDict, Union

import castep_outputs.utilities.castep_res as REs

from ..utilities.castep_res import get_numbers
from ..utilities.datatypes import AtomIndex, ThreeByThreeMatrix, ThreeVector
from ..utilities.filewrapper import Block
from ..utilities.utility import normalise_key, to_type


class AtomsInfo(TypedDict):
    """
    Per atom magres information.
    """
    #: Susceptability anisotropy.
    anisotropy: float
    #: Isotropic susceptability.
    isotropic: float
    #: Asymmetry ratio.
    asymmetry: float
    #: Atom coordinates.
    coords: ThreeVector
    #: Eigenvalues in :math:`\sigma_{\alpha\alpha}`.
    eigenvalue: ThreeVector
    #: Eigenvectors in :math:`\sigma_{\alpha\alpha}`.
    eigenvector: ThreeByThreeMatrix


def parse_magres_file(magres_file: TextIO) -> Dict[str, float]:
    """ Parse .magres file to dict """
    accum = defaultdict(dict)

    for line in magres_file:
        if block := Block.from_re(line, magres_file, r"^\s*\[\w+\]\s*$", r"^\s*\[/\w+\]\s*$"):

            block_name = next(block).strip().strip("[").strip("]")

            if block_name == "calculation":
                accum['calc'] = _process_calculation_block(block)
            elif block_name == "atoms":
                accum['atoms'] = _process_atoms_block(block)
            elif block_name == "magres":
                accum['magres'] = _process_magres_block(block)
            elif block_name == "magres_old":
                (accum["total_shielding"],
                 accum["atom_info"]) = _process_magres_old_block(block, accum)

    return accum


def _process_calculation_block(block: Block) -> Dict[str, str]:
    """
    Process a calculation parameters block.

    Parameters
    ----------
    block : Block
        Block to process

    Returns
    -------
    dict[str, str]
        Processed data.
    """
    calc = {}
    for line in block:
        if line.startswith("["):
            continue
        key, *val = line.strip().split(maxsplit=1)

        if val:
            # Strip `calc_`
            calc[key[5:]] = val[0]
    return calc


def _process_atoms_block(block: Block) -> Dict[AtomIndex, ThreeVector]:
    """
    Process the atoms block.

    Parameters
    ----------
    block : Block
        Block to process

    Returns
    -------
    dict[str, str]
        Processed data.
    """
    accum = {"units": {}, "coords": {}}
    for line in block:
        if line.startswith("lattice"):

            key, *val = line.split()
            accum[key] = to_type(val, float)

        elif line.startswith("atom"):

            key, _, spec, ind, *pos = line.split()
            accum["coords"][(spec, int(ind))] = to_type(pos, float)

        elif line.startswith("units"):
            _, key, val = line.split()
            accum["units"][key] = val
    return accum


def _process_magres_block(block: Block) -> Dict[str, Union[str, ThreeByThreeMatrix]]:
    """
    Process the main magres block.

    Parameters
    ----------
    block : Block
        Block to process

    Returns
    -------
    dict[str, str]
        Processed data.
    """
    accum = {"units": {}, "ms": {}}
    for line in block:
        if line.startswith("ms"):

            key, spec, ind, *val = line.split()
            accum[key][(spec, int(ind))] = to_type(val, float)

        elif line.startswith("units"):
            _, key, val = line.split()
            accum["units"][key] = val

    return accum


def _process_magres_old_block(
        block: Block, accum: dict
) -> Tuple[ThreeByThreeMatrix, Dict[AtomIndex, AtomsInfo]]:
    """
    Process the magres_old block.

    Parameters
    ----------
    block : Block
        Block to process.

    Returns
    -------
    ThreeByThreeMatrix
        Total shielding tensor.
    dict[AtomIndex, AtomsInfo]
        Processed atomic data.
    """
    atom_info = {atreg: defaultdict(list) for atreg in accum['atoms']['coords']}
    for atreg, pos in accum['atoms']['coords'].items():
        atom_info[atreg]['coords'] = pos

    total_shielding = None

    for line in block:
        if sub_blk := Block.from_re(line, block, "TOTAL Shielding Tensor",
                                    REs.EMPTY, n_end=2):
            total_shielding = [to_type(numbers, float)
                               for sub_line in sub_blk
                               if (numbers := get_numbers(sub_line))]
        elif Block.from_re(line, block, "^=+$", "^=+$"):
            pass
        elif line.strip() and "[" not in line:
            spec, ind, key, *val = line.split()
            atreg = spec, int(ind)
            if key == "Eigenvalue":
                atom_info[atreg]['eigvenvalue'].append(float(val[1]))
            elif key == "Eigenvector":
                atom_info[atreg]['eigvenvector'].append(to_type(val[1:], float))
            elif ":" in key:
                atom_info[atreg][normalise_key(key)] = float(val[0])

    return total_shielding, atom_info
