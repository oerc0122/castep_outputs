"""Parser for cst_esp files."""
from __future__ import annotations

from typing import BinaryIO, TypedDict

from ..utilities.utility import file_or_path, to_type
from .fortran_bin_parser import binary_file_reader


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
    dtypes = {"n_spins": int, "grid": int}

    accum = {"esp": []}

    reader = binary_file_reader(cst_esp_file)
    for (key, typ), datum in zip(dtypes.items(), reader):
        accum[key] = to_type(datum, typ)

    prev_nx = None
    curr = []
    for datum in reader:
        nx, _ny = to_type(datum[:8], int)
        if prev_nx != nx and curr:
            accum["esp"].append(curr)
            curr = []
        curr.append(to_type(datum[8:], complex))
        prev_nx = nx

    accum["esp"].append(curr)

    size = accum["grid"][0]
    if len(accum["esp"]) > size:  # Have MGGA pot
        accum["esp"], accum["mgga"] = accum["esp"][:size], accum["esp"][size:]

    return accum
