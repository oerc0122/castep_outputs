"""Parser for pdos_bin files."""
from __future__ import annotations

from typing import Any, BinaryIO, TypedDict, cast

from castep_outputs.utilities.utility import file_or_path

from .fortran_bin_parser import FortranBinaryReader


class PDOSData(TypedDict):
    """Data from partial density of states."""

    file_ver: float
    header: str
    n_kpoints: int
    n_spins: int
    n_popn_orb: int
    max_eigenvalues: int
    orbital_species: tuple[int, ...]
    orbital_ion: tuple[int, ...]
    orbital_l: tuple[int, ...]

    #: Kpoint index, spin index, eigenvalue index -> complex * n_orbitals
    pdos_weights: dict[tuple[int, int, int], tuple[complex, ...]]


@file_or_path(mode="rb")
def parse_pdos_bin_file(pdos_bin_file: BinaryIO) -> PDOSData:
    """Parse castep `pdos_bin` files.

    Parameters
    ----------
    pdos_bin_file
        File to parse.

    Returns
    -------
    :
        Parsed data.
    """
    dtypes = {
        "file_ver": float,
        "header": str,
        "n_kpoints": int,
        "n_spins": int,
        "n_popn_orb": int,
        "max_eigenvalues": int,
        "orbital_species": (int, ...),
        "orbital_ion": (int, ...),
        "orbital_l": (int, ...),
    }

    reader = FortranBinaryReader(pdos_bin_file)
    accum: dict[str, Any] = reader.get_dtype_dict(dtypes)
    accum["pdos_weights"] = {}

    for _nk in range(accum["n_kpoints"]):
        k_ind, *_n_kpt_grp = reader.get((int, ...))

        for ns in range(accum["n_spins"]):
            _ns, n_eigenvalues = reader.get_dtype_iter((int, int))

            for ne in range(n_eigenvalues):
                accum["pdos_weights"][k_ind, ns, ne] = reader.get((complex, ...))

    return cast("PDOSData", accum)
