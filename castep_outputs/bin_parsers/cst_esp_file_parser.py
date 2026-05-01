"""Parser for cst_esp files."""
from __future__ import annotations

from typing import Any, BinaryIO, TypedDict, cast

from castep_outputs.utilities.utility import file_or_path, to_type

from .fortran_bin_parser import FortranBinaryReader


class ESPData(TypedDict):
    """Data from electrostatic potential."""

    #: Number of spins in run.
    n_spins: int
    #: Grid size sampled at.
    grid: int
    #: ESP Data.
    esp: tuple[tuple[tuple[complex, ...], ...], ...]
    #: MGGA
    mgga: tuple[tuple[tuple[complex, ...], ...], ...]


@file_or_path(mode="rb")
def parse_cst_esp_file(cst_esp_file: BinaryIO) -> ESPData:
    """Parse castep `cst_esp` files.

    Parameters
    ----------
    cst_esp_file : BinaryIO
        File to parse.

    Returns
    -------
    ESPData
        Parsed data.
    """
    dtypes = {"n_spins": int, "grid": (int, ...)}

    reader = FortranBinaryReader(cst_esp_file)
    accum: dict[str, Any] = reader.get_dtype_dict(dtypes)

    prev_nx = None
    curr = []
    accum["esp"] = []
    for datum in reader:
        nx, _ny = to_type(datum[:8], (int, ...))
        if prev_nx != nx and curr:
            accum["esp"].append(curr)
            curr = []
        curr.append(to_type(datum[8:], (complex, ...)))
        prev_nx = nx

    accum["esp"].append(curr)

    size = accum["grid"][0]
    if len(accum["esp"]) > size:  # Have MGGA pot
        accum["esp"], accum["mgga"] = accum["esp"][:size], accum["esp"][size:]

    return cast("ESPData", accum)
