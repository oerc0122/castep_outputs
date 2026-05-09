"""Parser for elnes_bin files."""

from __future__ import annotations

from typing import BinaryIO, TypedDict, cast

from castep_outputs.utilities.utility import file_or_path, mass_product

from .fortran_bin_parser import FortranBinaryReader


class ELNESData(TypedDict):
    """Parsed .elnes_bin data."""

    file_ver: float
    header: str
    max_eigenvalues: int
    n_core_projectors: int
    n_kpoints: int
    n_spins: int
    n_orbitals: int
    n_bands: int

    core_orbital_species: tuple[int, ...]
    core_orbital_ion: tuple[int, ...]
    core_orbital_n: tuple[int, ...]
    core_orbital_lm: tuple[int, ...]
    elnes: list[list[list[list[list[complex]]]]]


@file_or_path(mode="rb")
def parse_elnes_bin_file(elnes_bin_file: BinaryIO) -> ELNESData:
    """Parse castep `elnes_bin` files.

    Parameters
    ----------
    elnes_bin_file
        File to parse.

    Returns
    -------
    :
        Parsed data.
    """
    dtypes = {
        "file_ver": float,
        "header": str,
        "n_orbitals": int,
        "n_bands": int,
        "n_kpoints": int,
        "n_spins": int,
        "core_orbital_species": (int, ...),
        "core_orbital_ion": (int, ...),
        "core_orbital_n": (int, ...),
        "core_orbital_lm": (int, ...),
    }

    reader = FortranBinaryReader(elnes_bin_file)
    accum = cast("ELNESData", reader.get_dtype_dict(dtypes))

    n_kpoints = accum["n_kpoints"]
    n_spins = accum["n_spins"]
    n_orbitals = accum["n_orbitals"]
    n_bands = accum["n_bands"]

    elnes = accum["elnes"] = [[[[[0j] * n_spins] * n_kpoints] * 3] * n_bands] * n_orbitals

    # Determine format
    old_format = len(next(reader)) == 16
    reader.rewind(1)

    if old_format:
        for datum, (nk, ns, index, orb, nb) in zip(
            reader.get_dtype_cycle((complex,)),
            mass_product(n_kpoints, n_spins, 3, n_orbitals, n_bands),
            strict=True,
        ):
            elnes[orb][nb][index][nk][ns] = datum[0]

        return accum

    for data, (nk, ns) in zip(
        reader.get_dtype_cycle(((complex, ...),)),
        mass_product(n_kpoints, n_spins),
        strict=True,
    ):
        for (orb, nb, index), datum in zip(
            mass_product(n_orbitals, n_bands, 3),
            data[0],
            strict=True):
            elnes[orb][nb][index][nk][ns] = datum

    return accum
