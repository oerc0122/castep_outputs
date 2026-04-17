"""Parser for dome_bin files."""

from __future__ import annotations

from typing import BinaryIO, TypedDict, cast

from castep_outputs.utilities.utility import file_or_path

from .fortran_bin_parser import FortranBinaryReader

HEADER = {
    "file_ver": float,
    "header": str,
}


class DOMEData(TypedDict):
    """Data as parsed from dome_bin."""

    file_ver: float
    header: str
    data: tuple[tuple[float, ...], ...]


@file_or_path(mode="rb")
def parse_dome_bin_file(dome_bin_file: BinaryIO) -> DOMEData:
    """Parse castep `dome_bin` files.

    Parameters
    ----------
    dome_bin_file : BinaryIO
        File to parse.

    Returns
    -------
    DOMEData
        Parsed data.
    """
    reader = FortranBinaryReader(dome_bin_file)

    accum = reader.get_dtype_dict(HEADER)

    accum["data"] = []

    for data in reader.get_dtype_cycle((float,)):
        accum["data"].append(data)

    accum["data"] = tuple(accum["data"])
    return cast("DOMEData", accum)
