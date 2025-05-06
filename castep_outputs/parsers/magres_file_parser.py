"""Parse castep .magres files."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal, TextIO, TypedDict

import castep_outputs.utilities.castep_res as REs

from ..utilities.castep_res import get_numbers
from ..utilities.datatypes import AtomIndex, ThreeByThreeMatrix, ThreeVector
from ..utilities.filewrapper import Block
from ..utilities.utility import (
    add_aliases,
    determine_type,
    file_or_path,
    normalise_key,
    to_type,
)


class AtomsInfo(TypedDict):
    """Per atom magres information."""

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


class UnitsInfo(TypedDict):
    """Information on magres units."""

    #: Position units.
    atom: str
    #: Lattice length units.
    lattice: str
    #: Magnetic reponse units.
    ms: str


class MagresInfo(TypedDict):
    """NMR Magnetic reponse information."""

    #: Atom coordinates
    atoms: dict[AtomIndex, ThreeVector]
    calc_code: Literal["CASTEP"]
    calc_code_hgversion: str
    calc_code_platform: str
    calc_code_version: str
    calc_cutoffenergy: str
    calc_kpoint_mp_grid: str
    calc_kpoint_mp_offset: str
    calc_name: str
    calc_pspot: str
    calc_xcfunctional: str
    #: Crystal lattice.
    lattice: tuple[float, float, float, float, float, float, float, float, float]
    #: Magnetic susceptibility tensor.
    ms: dict[AtomIndex, list[float]]
    units: UnitsInfo


@file_or_path(mode="r")
def parse_magres_file(magres_file: TextIO) -> MagresInfo:
    """
    Parse castep .magres file.

    Parameters
    ----------
    magres_file
        Open handle to file to parse.

    Returns
    -------
    MagresInfo
        Parsed info.
    """
    # pylint: disable=too-many-branches

    accum = defaultdict(dict)

    for line in magres_file:
        if block := Block.from_re(line, magres_file, r"^\s*\[\w+\]\s*$", r"^\s*\[/\w+\]\s*$"):
            block_name = next(block).strip().strip("[").strip("]")

            if block_name == "calculation":
                accum["calc"] = _process_calculation_block(block)
                version = int(accum["calc"]["code_version"].split(".")[0])
            elif block_name == "atoms":
                accum["atoms"] = _process_atoms_block(block)
            elif block_name == "magres":
                accum["magres"] = _process_magres_block(block, version)
            elif block_name == "magres_old":
                (accum["total_shielding"], accum["atom_info"]) = _process_magres_old_block(
                    block, accum,
                )

    return accum


def _process_calculation_block(block: Block) -> dict[str, str]:
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


def _process_atoms_block(block: Block) -> dict[AtomIndex, ThreeVector]:
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
            accum["coords"][spec, int(ind)] = to_type(pos, float)

        elif line.startswith("units"):
            _, key, val = line.split()
            accum["units"][key] = val
    return accum


def _process_magres_block(block: Block, version: int) -> dict[str, str | ThreeByThreeMatrix]:
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
    accum = defaultdict(dict)

    munge_fix = 3 if version < 22 else 5

    for line in block:
        if line.startswith("units"):
            _, key, val = line.split()
            accum["units"][key] = val

        elif (words := line.split())[0] in {"ms", "efg", "efg_local", "efg_nonlocal"}:
            key, spec, ind, *val = words

            if determine_type(ind) is float:  # Have a munged spec-ind
                val.insert(0, ind)
                spec, ind = spec[:-munge_fix], spec[-munge_fix:]

            accum[key][spec, int(ind)] = to_type(val, float)

        elif words[0].startswith("isc"):  # ISC props explicitly have spaces!
            key, speca, inda, specb, indb, *val = words

            accum[key][(speca, int(inda)), (specb, int(indb))] = to_type(val, float)

    add_aliases(
        accum,
        {
            "ms": "magnetic_resonance_shielding",
            "efg": "electric_field_gradient",
            "efg_local": "local_electric_field_gradient",
            "efg_nonlocal": "nonlocal_electric_field_gradient",
            "isc_fc": "j_coupling_fc",
            "isc_orbital_p": "j_coupling_orbital_p",
            "isc_orbital_d": "j_coupling_orbital_d",
            "isc_spin": "j_coupling_spin",
            "isc": "j_coupling_k_total",
        },
    )

    return accum


def _process_magres_old_block(
    block: Block,
    accum: dict,
) -> tuple[ThreeByThreeMatrix, dict[AtomIndex, AtomsInfo]]:
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
    atom_info = {atreg: defaultdict(list) for atreg in accum["atoms"]["coords"]}
    for atreg, pos in accum["atoms"]["coords"].items():
        atom_info[atreg]["coords"] = pos

    total_shielding = None

    for line in block:
        if sub_blk := Block.from_re(line, block, "TOTAL Shielding Tensor", REs.EMPTY, n_end=2):
            total_shielding = [
                to_type(numbers, float)
                for sub_line in sub_blk
                if (numbers := get_numbers(sub_line))
            ]
        elif Block.from_re(line, block, "^=+$", "^=+$"):
            pass
        elif line.strip() and "[" not in line:
            spec, ind, key, *val = line.split()
            atreg = spec, int(ind)
            if key == "Eigenvalue":
                atom_info[atreg]["eigvenvalue"].append(float(val[1]))
            elif key == "Eigenvector":
                atom_info[atreg]["eigvenvector"].append(to_type(val[1:], float))
            elif ":" in key:
                atom_info[atreg][normalise_key(key)] = float(val[0])

    return total_shielding, atom_info
