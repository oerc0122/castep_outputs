"""Parse castep .bands files."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import TextIO, TypedDict

from ..utilities import castep_res as REs
from ..utilities.datatypes import ThreeVector
from ..utilities.filewrapper import Block
from ..utilities.utility import fix_data_types
from .parse_utilities import parse_regular_header


class BandsQData(TypedDict, total=False):
    """Per k-point info of band."""

    #: List of band eigenvalues.
    band: ThreeVector
    #: List of eigenvalues for up component of band.
    band_up: ThreeVector
    #: List of eigenvalues for down component of band.
    band_dn: ThreeVector
    #: Position in space.
    qpt: ThreeVector
    #: Current spin component.
    spin_comp: int
    #: K point weight.
    weight: float


class BandsFileInfo(TypedDict, total=False):
    """Bands eigenvalue info of a bands calculation."""

    #: Bands info in file.
    bands: list[BandsQData]


def parse_bands_file(bands_file: TextIO) -> BandsFileInfo:
    """
    Parse castep .bands file.

    Parameters
    ----------
    bands_file
        Open handle to file to parse.

    Returns
    -------
    BandsFileInfo
        Parsed info.
    """
    bands_info: BandsFileInfo = defaultdict(list)
    qdata = {}

    block = Block.from_re("", bands_file, "", REs.THREEVEC_RE, n_end=3)
    data = parse_regular_header(block, ("Fermi energy",))
    bands_info.update(data)

    for line in bands_file:
        if line.startswith("K-point"):
            if qdata:
                fix_data_types(qdata, {"qpt": float,
                                       "weight": float,
                                       "spin_comp": int,
                                       "band": float,
                                       "band_up": float,
                                       "band_dn": float,
                                       })
                bands_info["bands"].append(qdata)
            _, _, *qpt, weight = line.split()
            qdata = {"qpt": qpt, "weight": weight, "spin_comp": None, "band": []}

        elif line.startswith("Spin component"):
            qdata["spin_comp"] = line.split()[2]
            if qdata["spin_comp"] != "1":
                qdata["band_up"] = qdata.pop("band")
                if "band_dn" not in qdata:
                    qdata["band_dn"] = []

        elif re.match(rf"^\s*{REs.FNUMBER_RE}$", line.strip()):
            if qdata["spin_comp"] != "1":
                qdata["band_dn"].append(line)
            else:
                qdata["band"].append(line)

    if qdata:
        fix_data_types(qdata, {"qpt": float,
                               "weight": float,
                               "spin_comp": int,
                               "band": float,
                               "band_up": float,
                               "band_dn": float,
                               })
        bands_info["bands"].append(qdata)

    return bands_info
