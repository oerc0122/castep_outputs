"""Parse castep .epme bin files."""

from __future__ import annotations

from math import isqrt
from typing import TYPE_CHECKING, BinaryIO, TypedDict, cast

from castep_outputs.bin_parsers.fortran_bin_parser import FortranBinaryReader
from castep_outputs.utilities.utility import file_or_path, filter_underscore

if TYPE_CHECKING:
    from castep_outputs.utilities.datatypes import AtomIndex, ThreeVector

HEADER_DTYPES = {
    "_FILE_TYPE": str,
    "version": int,
    "_HEADER": str,
    "n_spins": int,
    "fermi_energy": float,
}


class EPMEBinKPoint(TypedDict):
    """**k**-point information from EPME file."""

    #: Number of bands in k-point.
    n_bands: int
    #: Minimum band in k-point.
    min_band: int
    #: k-point eigenvalues.
    eigenvalues: tuple[float, ...]
    #: k-point velocities.
    velocities: tuple[float, ...]


class EPMEBinPhonon(TypedDict):
    """Phonon and matrix element data."""

    #: Initial and final k-point index.
    kpts: tuple[int, int]
    #: Phonon index
    index: int

    #: Frequencies.
    frequencies: tuple[float, ...]
    #: Modes.
    modes: tuple[complex, ...]
    #: Matrix elements.
    matrix_elements: tuple[complex, ...]


class EPMEBinData(TypedDict):
    """Full epme_bin file data."""

    #: File version.
    version: int

    #: Number of ions in cell.
    n_ions: int
    #: Number of bands.
    n_bands: int
    #: Number of spins in system.
    n_spins: int
    #: Number of k-point transition pairs.
    n_kpoint_pairs: int

    #: Fermi energy.
    fermi_energy: float
    #: Unit cell matrix.
    real_lattice: tuple[float, float, float, float, float, float, float, float, float]

    #: Ion positions in cell.
    ions: dict[AtomIndex, ThreeVector]
    #: KPoints in cell.
    kpoints: dict[tuple[int, int], EPMEBinKPoint]
    #: Phonon specific information.
    phonons: list[EPMEBinPhonon]


def _check_header(reader: FortranBinaryReader, test: bytes) -> None:
    r"""Check if next line is ``test`` or raise standard error.

    Parameters
    ----------
    reader
        Reader to check.
    test
        Value to check against.

    Raises
    ------
    ValueError
        If test doesn't match.

    Examples
    --------
    >>> from io import BytesIO
    >>> raw = BytesIO(b"\x00\x00\x00\x06HEADER\x00\x00\x00\x06")
    >>> data = FortranBinaryReader(raw)
    >>> _check_header(data, b"HEADER")
    >>> raw = BytesIO(b"\x00\x00\x00\x06HEADER\x00\x00\x00\x06")
    >>> data = FortranBinaryReader(raw)
    >>> _check_header(data, b"NOT")
    Traceback (most recent call last):
    ValueError: Unexpected data (b'HEADER') in epme file, expected b'NOT'.
    """
    if (x := next(reader)) != test:
        reader.rewind(2)
        raise ValueError(f"Unexpected data ({x}) in epme file, expected {test}.")


def _parse_header(reader: FortranBinaryReader, accum: dict) -> None:
    """Parse header based on ``HEADER_DTYPES``.

    Parameters
    ----------
    reader
        Reader
    accum
        Data destination.
    """
    accum.update(filter_underscore(reader.get_dtype_dict(HEADER_DTYPES)))


def _parse_atoms(reader: FortranBinaryReader, accum: dict) -> None:
    """Parse ATOMS block.

    Parameters
    ----------
    reader
        Reader
    accum
        Data destination.
    """
    _check_header(reader, b"ATOM")

    n_ion = accum["n_ions"] = reader.get(int)
    accum["real_lattice"] = reader.get((float, ...))
    accum["ions"] = {}

    for ind, spec, pos in reader.get_dtype_cycle((int, str, (float, ...)), n=n_ion):
        accum["ions"][spec.strip(), ind] = pos


def _parse_kpoint(reader: FortranBinaryReader, accum: dict) -> None:
    """Parse KPOINT block.

    Parameters
    ----------
    reader
        Reader
    accum
        Data destination.
    """
    _check_header(reader, b"KPOINT")

    accum["n_kpoint_pairs"] = reader.get(int) // 2
    accum["n_bands"] = reader.get(int)
    accum["kpoints"] = {}

    total = accum["n_spins"] * accum["n_kpoint_pairs"] * 2
    dtypes = {
        "ns": int,
        "nk": int,
        "n_bands": int,
        "min_band": int,
        "eigenvalues": (float, ...),
        "velocities": (float, ...),
    }

    for data in reader.get_dtype_cycle(dtypes, n=total):
        ns = data.pop("ns")
        nk = data.pop("nk")
        accum["kpoints"][ns, nk] = data


def _parse_phonons(reader: FortranBinaryReader, accum: dict) -> None:
    """Parse ``EPCOUPLING`` block.

    Parameters
    ----------
    reader
        Reader
    accum
        Data destination.

    Raises
    ------
    ValueError
        Data don't match.
    """
    _check_header(reader, b"EPCOUPLING")

    n_kpoint_pairs = reader.get(int)
    n_bands = isqrt(reader.get(int))

    accum.setdefault("n_kpoint_pairs", n_kpoint_pairs)
    accum.setdefault("n_bands", n_bands)

    if n_kpoint_pairs != accum["n_kpoint_pairs"]:
        raise ValueError("Number of kpoint pairs doesn't match between EPCOUPLING and KPOINTS.")

    if n_bands != accum["n_bands"]:
        raise ValueError("Number of bands doesn't match between EPCOUPLING and KPOINTS.")

    dtypes = {
        "_nq": int,
        "_nb": int,
        "_nb2": int,
        "kpts": (int, ...),
        "frequencies": (float, ...),
        "modes": (complex, ...),
        "matrix_elements": (complex, ...),
    }

    accum["phonons"] = [
        filter_underscore(proc) for proc in reader.get_dtype_cycle(dtypes, n=n_kpoint_pairs)
    ]


@file_or_path(mode="rb")
def parse_epme_bin_file(epme_file: BinaryIO) -> EPMEBinData:
    """Parse castep `epme_bin` files.

    Parameters
    ----------
    epme_file
        File to parse.

    Returns
    -------
    :
        Parsed data.
    """
    reader = FortranBinaryReader(epme_file)

    data = {}
    _parse_header(reader, data)
    _parse_atoms(reader, data)
    _parse_kpoint(reader, data)
    _parse_phonons(reader, data)

    return cast("EPMEBinData", data)
