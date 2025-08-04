"""Parse castep .magres files."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal, TextIO, TypedDict

import castep_outputs.utilities.castep_res as REs

from ..utilities.datatypes import AtomIndex, ThreeByThreeMatrix, ThreeVector
from ..utilities.filewrapper import Block
from ..utilities.utility import (
    add_aliases,
    determine_type,
    file_or_path,
    to_type,
)

MAGRES_ALIASES = {
        "ms": "magnetic_shielding",
        "efg": "electric_field_gradient",
        "efg_local": "local_electric_field_gradient",
        "efg_nonlocal": "nonlocal_electric_field_gradient",
        "isc_fc": "j_coupling_fc",
        "isc_orbital_p": "j_coupling_orbital_p",
        "isc_orbital_d": "j_coupling_orbital_d",
        "isc_spin": "j_coupling_spin",
        "isc": "j_coupling_k_total",
        "hf": "hyperfine",
    }

MAGRES_DEFAULT_UNITS = {
    "atom": "Angstrom",
    "lattice": "Angstrom",
    "ms": "ppm",
    "efg": "au",
    "isc": "10^19.T^2.J^-1",
    "isc_fc": "10^19.T^2.J^-1",
    "isc_spin": "10^19.T^2.J^-1",
    "isc_orbital_p": "10^19.T^2.J^-1",
    "isc_orbital_d": "10^19.T^2.J^-1",
    "hf": "au",
}

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

    atom: str  #: Position units.
    lattice: str  #: Lattice length units.
    ms: str  #: Magnetic response units.
    efg: str  #: Electric field gradient units.
    isc: str  #: J-coupling units.
    isc_fc: str  #: Fermi contact J-coupling units.
    isc_spin: str  #: Spin dipole J-coupling units.
    isc_orbital_p: str  #: Orbital paramagnetic J-coupling units.
    isc_orbital_d: str  #: Orbital diamagnetic J-coupling units.
    hyperfine: str  #: Hyperfine coupling units.


class MagresInfo(TypedDict):
    """NMR Magnetic response information."""

    atoms: dict[AtomIndex, ThreeVector]  #: Atom coordinates.
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
    magres_file : TextIO
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
        Block to process.

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
        Block to process.

    Returns
    -------
    dict[AtomIndex, ThreeVector]
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
        Block to process.
    version : int
        CASTEP version number.

    Returns
    -------
    dict[str, str | ThreeByThreeMatrix]
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
            accum[key][((speca, int(inda)), (specb, int(indb)))] = _list_to_threebythree(val)

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
    dict[str, str | ThreeByThreeMatrix]
        Processed data.
    """
    data = {"atoms": {"units": {}, "coords": {}}, "magres": {"units": {}}}
    data["atoms"]["units"]["atom"] = "Angstrom"

    found_atoms = set()
    coords = REs.MAGRES_OLD_RE["coords"].findall(str(block))
    for label, i, x, y, z in coords:
        index = (label, int(i))
        if index not in found_atoms:
            data["atoms"]["coords"][index] = (float(x), float(y), float(z))
            found_atoms.add(index)

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

    # The magres_old blocks have data in these atom blocks
    for atom in atoms:
        index = atom[1], int(atom[2])
        _process_tensors(atom[3], index, data, "ms" )
        _process_tensors(atom[3], index, data, "efg")
        _process_tensors(atom[3], index, data, "hf")
        _process_jcoupling_tensors(atom[3], index, perturbing_index, data)

    return data


def _process_tensors(atom_data: str, index: AtomIndex, data: dict, tensor_type: str):
    """Process tensors from magres_old blocks."""
    tensors = REs.MAGRES_OLD_RE[f"{tensor_type}_tensor"].findall(atom_data)
    if not tensors:
        return

    # Add default units from MAGRES_DEFAULT_UNITS if not present
    if tensor_type not in data["magres"]["units"]:
        data["magres"]["units"][tensor_type] = MAGRES_DEFAULT_UNITS.get(tensor_type, "")



    # Ensure tensor dictionary exists
    if tensor_type not in data["magres"]:
        data["magres"][tensor_type] = {}

    # Store tensors
    for tensor in tensors:
        data["magres"][tensor_type][index] = _list_to_threebythree(tensor[1:])

def _process_jcoupling_tensors(
        atom_data: str,
        index: AtomIndex,
        perturbing_index: AtomIndex,
        data: dict):
    """Process J-coupling tensors from magres_old blocks."""
    jc_tensors = REs.MAGRES_OLD_RE["isc_tensor"].findall(atom_data)
    if not jc_tensors:
        return

    for tensor in jc_tensors:
        tag = _get_jcoupling_tag(tensor[0])
        if tag not in data["magres"]:
            data["magres"][tag] = {}
        data["magres"][tag][perturbing_index, index] = _list_to_threebythree(tensor[1:])

    # For any isc tensor tags, add the units if not present
    for tag in ("isc", "isc_fc", "isc_spin", "isc_orbital_p", "isc_orbital_d"):
        if tag in data["magres"] and tag not in data["magres"]["units"]:
            data["magres"]["units"][tag] = MAGRES_DEFAULT_UNITS.get(tag, "")


def _get_jcoupling_tag(tensor_type: str) -> str:
    """Get the J-coupling tag based on tensor type.

    These are the tags used in the magres_old blocks.
    """
    TENSOR_TAG_LOOKUP = {
        "Fermi Contact": "isc_fc",
        "Spin Dipole": "isc_spin",
        "Diamagnetic": "isc_orbital_d",
        "Paramagnetic": "isc_orbital_p",
        "Total": "isc",
    }

    try:
        return TENSOR_TAG_LOOKUP[tensor_type]
    except KeyError as err:
        raise ValueError(f"Unknown J-coupling tensor type: {tensor_type}") from err


def _list_to_threebythree(lst: list[float] | list[str]) -> ThreeByThreeMatrix:
    """List of 9 floats to 3x3 matrix.

    Order is:
    ::

        [a, b, c,
         d, e, f,
         g, h, i]
    """
    # Convert to floats if necessary
    lst = [float(i) for i in lst]

    return (
        (lst[0], lst[1], lst[2]),
        (lst[3], lst[4], lst[5]),
        (lst[6], lst[7], lst[8]),
    )
