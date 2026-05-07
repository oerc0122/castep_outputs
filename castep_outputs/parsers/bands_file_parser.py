"""Parse castep .bands files."""

from __future__ import annotations

import re
from typing import Literal, TextIO, TypedDict

from castep_outputs.utilities import castep_res as REs
from castep_outputs.utilities.datatypes import ThreeVector
from castep_outputs.utilities.filewrapper import Block
from castep_outputs.utilities.type_conv import to_type
from castep_outputs.utilities.utility import file_or_path

from .parse_utilities import parse_regular_header


class BandsQData(TypedDict, total=False):
    """Per k-point info of band."""

    #: List of band eigenvalues.
    band: ThreeVector
    #: List of eigenvalues for up component of band.
    band_up: ThreeVector
    #: List of eigenvalues for down component of band.
    band_down: ThreeVector
    #: Position in space.
    qpt: ThreeVector
    #: Current spin component.
    spin_comp: int
    #: K point weight.
    weight: float


BandsFileInfo = TypedDict("BandsFileInfo", {
    "eigenvalues": int,
    "electrons": int,
    "k-points": int,
    "spin components": int,
    "Fermi Energy": float,
    "coords": dict,
    "bands": list[BandsQData],
    })


@file_or_path(mode="r")
def parse_bands_file(bands_file: TextIO) -> BandsFileInfo:
    """
    Parse castep .bands file.

    Parameters
    ----------
    bands_file
        Open handle to file to parse.

    Returns
    -------
    :
        Parsed info.
    """
    bands_info: BandsFileInfo = {"bands": []}
    qdata: BandsQData = {}
    accum: list[str] = []
    current: Literal["band", "band_up", "band_down"] = "band"

    block = Block.from_re("", bands_file, "", REs.THREEVEC_RE, n_end=3)
    data = parse_regular_header(block, ("Fermi energy",))
    bands_info.update(data)

    for line in bands_file:
        if line.startswith("K-point"):
            if qdata:
                qdata[current] = to_type(accum, float)
                qdata["spin_comp"] = "band_down" in qdata
                bands_info["bands"].append(qdata)
                accum = []
                current = "band"
            _, _, *qpt, weight = line.split()
            qdata = {"qpt": to_type(qpt, float), "weight": float(weight)}

        elif line.startswith("Spin component"):
            spin_comp = int(line.split()[2])
            if spin_comp != 1:
                qdata["band_up"] = to_type(accum, float)
                accum = []
                current = "band_down"

        elif re.match(rf"^\s*{REs.FNUMBER_RE}$", line.strip()):
            accum.append(line.strip())

    if qdata:
        qdata[current] = to_type(accum, float)
        qdata["spin_comp"] = "band_down" in qdata
        bands_info["bands"].append(qdata)

    return bands_info
