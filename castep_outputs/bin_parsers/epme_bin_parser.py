"""Parse castep .epme bin files."""

from __future__ import annotations

from itertools import product
from math import isqrt
from typing import TYPE_CHECKING, BinaryIO, TypedDict, cast

from castep_outputs.bin_parsers.fortran_bin_parser import FortranBinaryReader, binary_file_reader
from castep_outputs.utilities.utility import file_or_path, to_type

if TYPE_CHECKING:
    from castep_outputs.utilities.datatypes import AtomIndex, ThreeVector

HEADER_DTYPES = {
    "FILE_TYPE": str,
    "version": int,
    "HEADER": str,
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

    #: Initial k-point index.
    kpt_i: int
    #: Final k-point index.
    kpt_f: int
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
    reader : FortranBinaryReader
        Reader to check.
    test : bytes
        Value to check against.

    Raises
    ------
    ValueError
        If test doesn't match.

    Examples
    --------
    >>> from io import BytesIO
    >>> raw = BytesIO(b"\x00\x00\x00\x06HEADER\x00\x00\x00\x06")
    >>> data = binary_file_reader(raw)
    >>> _check_header(data, b"HEADER")
    >>> raw = BytesIO(b"\x00\x00\x00\x06HEADER\x00\x00\x00\x06")
    >>> data = binary_file_reader(raw)
    >>> _check_header(data, b"NOT")
    Traceback (most recent call last):
    ValueError: Unexpected data (b'HEADER') in epme file, expected b'NOT'.
    """
    if (x := next(reader)) != test:
        reader.send(-2)
        raise ValueError(f"Unexpected data ({x}) in epme file, expected {test}.")


def _parse_header(reader: FortranBinaryReader, accum: dict) -> None:
    """Parse header based on ``HEADER_DTYPES``.

    Parameters
    ----------
    reader : FortranBinaryReader
        Reader
    accum : dict
        Data destination.
    """
    for (key, typ), datum in zip(HEADER_DTYPES.items(), reader, strict=False):
        if not key.isupper():
            accum[key] = to_type(datum, typ)


def _parse_atoms(reader: FortranBinaryReader, accum: dict) -> None:
    """Parse ATOMS block.

    Parameters
    ----------
    reader : FortranBinaryReader
        Reader
    accum : dict
        Data destination.
    """
    _check_header(reader, b"ATOM")

    accum["n_ions"] = to_type(next(reader), int)
    accum["real_lattice"] = to_type(next(reader), float)
    accum["ions"] = {}

    for _ in range(accum["n_ions"]):
        ind = to_type(next(reader), int)
        spec = to_type(next(reader), str).strip()
        pos = to_type(next(reader), float)

        accum["ions"][spec, ind] = pos


def _parse_kpoint(reader: FortranBinaryReader, accum: dict) -> None:
    """Parse KPOINT block.

    Parameters
    ----------
    reader : FortranBinaryReader
        Reader
    accum : dict
        Data destination.
    """
    _check_header(reader, b"KPOINT")

    accum["n_kpoint_pairs"] = to_type(next(reader), int) // 2
    accum["n_bands"] = to_type(next(reader), int)
    accum["kpoints"] = {}

    for ns, _nq, _k in product(
        range(1, accum["n_spins"] + 1),
        range(accum["n_kpoint_pairs"]),
        range(2),
    ):
        _ns = to_type(next(reader), int)
        nk = to_type(next(reader), int)
        kpoint = accum["kpoints"][ns, nk] = {}
        kpoint["n_bands"] = to_type(next(reader), int)
        kpoint["min_band"] = to_type(next(reader), int)

        kpoint["eigenvalues"] = to_type(next(reader), float)
        kpoint["velocities"] = to_type(next(reader), float)


def _parse_phonons(reader: FortranBinaryReader, accum: dict) -> None:
    """Parse ``EPCOUPLING`` block.

    Parameters
    ----------
    reader : FortranBinaryReader
        Reader
    accum : dict
        Data destination.

    Raises
    ------
    ValueError
        Data don't match.
    """
    _check_header(reader, b"EPCOUPLING")

    n_kpoint_pairs = to_type(next(reader), int)
    n_bands = isqrt(to_type(next(reader), int))

    if "n_kpoint_pairs" in accum and n_kpoint_pairs != accum["n_kpoint_pairs"]:
        raise ValueError("Number of kpoint pairs doesn't match between EPCOUPLING and KPOINTS.")

    if "n_bands" in accum and n_bands != accum["n_bands"]:
        raise ValueError("Number of bands doesn't match between EPCOUPLING and KPOINTS.")

    accum.setdefault("n_kpoint_pairs", n_kpoint_pairs)
    accum.setdefault("n_bands", n_bands)
    accum["phonons"] = []

    for index in range(n_kpoint_pairs):
        phonon = {}

        _nq = next(reader)
        _n_bands = next(reader)
        _n_bands = next(reader)
        phonon["kpt_i"], phonon["kpt_f"] = to_type(next(reader), int)

        phonon["index"] = index
        phonon["frequencies"] = to_type(next(reader), float)
        phonon["modes"] = to_type(next(reader), complex)
        phonon["matrix_elements"] = to_type(next(reader), complex)
        accum["phonons"].append(phonon)


@file_or_path(mode="rb")
def parse_epme_bin_file(epme_file: BinaryIO) -> EPMEBinData:
    """Parse castep `epme_bin` files.

    Parameters
    ----------
    epme_file : BinaryIO
        File to parse.

    Returns
    -------
    EPMEBinData
        Parsed data.
    """
    reader = binary_file_reader(epme_file)

    data = {}
    _parse_header(reader, data)
    _parse_atoms(reader, data)
    _parse_kpoint(reader, data)
    _parse_phonons(reader, data)

    return cast("EPMEBinData", data)
