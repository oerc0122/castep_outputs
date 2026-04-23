"""Parser for ome_bin files."""

from __future__ import annotations

from typing import BinaryIO, TypedDict, cast

from castep_outputs.bin_parsers.fortran_bin_parser import FortranBinaryReader
from castep_outputs.utilities.utility import file_or_path

HEADER = {
    "file_ver": float,
    "header": str,
}


class OMEData(TypedDict):
    """Data from electrostatic potential."""

    #: Number of spins in run.
    n_spins: int
    #: Grid size sampled at.
    grid: int
    #: OME Data.
    data: tuple[tuple[tuple[complex, ...], ...], ...]


@file_or_path(mode="rb")
def parse_ome_bin_file(ome_bin_file: BinaryIO) -> OMEData:
    """Parse castep `ome_bin` files.

    Parameters
    ----------
    ome_bin_file
        File to parse.

    Returns
    -------
    :
        Parsed data.
    """
    reader = FortranBinaryReader(ome_bin_file)

    accum = reader.get_dtype_dict(HEADER)

    accum["data"] = []

    for data in reader.get_dtype_cycle([(complex, ...)]):
        accum["data"].append(data)

    accum["data"] = tuple(accum["data"])
    return cast("OMEData", accum)
