"""Parse castep .magres files."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Literal, SupportsFloat, TextIO, TypedDict

import castep_outputs.utilities.castep_res as REs

from ..utilities.datatypes import AtomIndex, ThreeByThreeMatrix, ThreeVector
from ..utilities.filewrapper import Block
from ..utilities.utility import (
    add_aliases,
    atreg_to_index,
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

    #: Position units.
    atom: str
    #: Lattice length units.
    lattice: str
    #: Magnetic response units.
    ms: str
    #: Electric field gradient units.
    efg: str
    #: J-coupling units.
    isc: str
    #: Fermi contact J-coupling units.
    isc_fc: str
    #: Spin dipole J-coupling units.
    isc_spin: str
    #: Orbital paramagnetic J-coupling units.
    isc_orbital_p: str
    #: Orbital diamagnetic J-coupling units.
    isc_orbital_d: str
    #: Hyperfine coupling units.
    hyperfine: str


class MagresInfo(TypedDict):
    """NMR Magnetic response information."""

    #: Ion (atom) coordinates.
    ions: dict[AtomIndex, ThreeVector]
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
    magres_old = {}

    for line in magres_file:
        if block := Block.from_re(line, magres_file, r"^\s*\[\w+\]\s*$", r"^\s*\[/\w+\]\s*$"):
            block_name = next(block).strip().strip("[").strip("]")

            if block_name == "calculation":
                accum["calc"] = _process_calculation_block(block)
                version = int(accum["calc"]["code_version"].split(".")[0])
            elif block_name == "atoms":
                accum["ions"] = _process_atoms_block(block)
            elif block_name == "magres":
                accum["magres"] = _process_magres_block(block, version)
            elif block_name == "magres_old":
                (accum["total_shielding"], accum["atom_info"]) = _process_magres_old_block(
                    block, accum,
                )

    # Accum takes priority
    return magres_old | accum


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
            accum[key][(speca, int(inda)), (specb, int(indb))] = _list_to_threebythree(val)

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
    data = {"ions": {"units": {}, "coords": {}}, "magres": {"units": {}}}
    data["ions"]["units"]["atom"] = "Angstrom"

    found_ions = set()
    coords_matches = REs.MAGRES_OLD_RE["coords"].finditer(str(block))
    for match in coords_matches:
        index = atreg_to_index(match)
        if index not in found_ions:
            data["ions"]["coords"][index] = to_type(match["val"].split(), float)
            found_ions.add(index)

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
    for match in REs.MAGRES_OLD_RE["atom"].finditer(str(block)):
        index = atreg_to_index(match)
        sub_blk = match.groups()[3]
        _process_tensors(sub_blk, index, data, "ms")
        _process_tensors(sub_blk, index, data, "efg")
        _process_tensors(sub_blk, index, data, "hf")
        _process_jcoupling_tensors(sub_blk, index, perturbing_index, data)

    return data


def _process_tensors(atom_data: str, index: AtomIndex, data: dict, tensor_type: str) -> None:
    """Process tensors from magres_old blocks."""
    tensors = REs.MAGRES_OLD_RE[f"{tensor_type}_tensor"].findall(atom_data)
    if not tensors:
        return

    # Add defaults
    data["magres"]["units"].setdefault(tensor_type, MAGRES_DEFAULT_UNITS.get(tensor_type, ""))
    data["magres"].setdefault(tensor_type, {})

    # Store tensors
    for tensor in tensors:
        data["magres"][tensor_type][index] = _list_to_threebythree(tensor[1:])


def _process_jcoupling_tensors(
    atom_data: str, index: AtomIndex, perturbing_index: AtomIndex, data: dict,
) -> None:
    """Process J-coupling tensors from magres_old blocks."""
    jc_tensors = REs.MAGRES_OLD_RE["isc_tensor"].findall(atom_data)
    if not jc_tensors:
        return

    for tensor in jc_tensors:
        tag = _get_jcoupling_tag(tensor[0])
        data["magres"].setdefault(tag, {})
        data["magres"][tag][perturbing_index, index] = _list_to_threebythree(tensor[1:])

    # For any isc tensor tags, add the units if not present
    for tag in ("isc", "isc_fc", "isc_spin", "isc_orbital_p", "isc_orbital_d"):
        if tag in data["magres"] and tag not in data["magres"]["units"]:
            data["magres"]["units"][tag] = MAGRES_DEFAULT_UNITS.get(tag, "")


def _get_jcoupling_tag(tensor_type: str) -> str:
    """Get the J-coupling tag based on tensor type.

    These are the tags used in the magres_old blocks.

    Parameters
    ----------
    tensor_type : str
        Type of tensor to extract.

    Returns
    -------
    str
        Internal key.

    Raises
    ------
    ValueError
        If unrecognised tag.
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


def _list_to_threebythree(lst: Sequence[SupportsFloat]) -> ThreeByThreeMatrix:
    """Convert Sequence of 9 float-likes to 3x3 matrix.

    Parameters
    ----------
    lst : Sequence[SupportsFloat]
        Set of values to convert.

    Returns
    -------
    ThreeByThreeMatrix
        Converted values.

    Examples
    --------
    >>> _list_to_threebythree("1 2 3 4 5 6 7 8 9".split())
    ((1.0, 2.0, 3.0), (4.0, 5.0, 6.0), (7.0, 8.0, 9.0))
    >>> _list_to_threebythree([1, 2, 3, 4, 5, 6, 7, 8, 9])
    ((1.0, 2.0, 3.0), (4.0, 5.0, 6.0), (7.0, 8.0, 9.0))

    Notes
    -----
    Only takes first nine elements, subsequent elements are ignored.

    Order is:
    ::

        [a, b, c,
         d, e, f,
         g, h, i]
    """
    # Convert to floats if necessary
    lst = to_type(lst, float)

    return (
        (lst[0], lst[1], lst[2]),
        (lst[3], lst[4], lst[5]),
        (lst[6], lst[7], lst[8]),
    )
