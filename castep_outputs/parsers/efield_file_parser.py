"""Parse castep .efield files."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TextIO, TypedDict

from ..utilities import castep_res as REs
from ..utilities.castep_res import labelled_floats
from ..utilities.constants import SND_D
from ..utilities.filewrapper import Block
from ..utilities.utility import file_or_path, fix_data_types, log_factory, stack_dict
from .parse_utilities import parse_regular_header


class EFieldTensor(TypedDict):
    """Standard efield tensor of Voigt components + frequency."""

    xx: list[float]
    yy: list[float]
    zz: list[float]
    xy: list[float]
    xz: list[float]
    yz: list[float]
    freq: list[float]


class EFieldInfo(TypedDict, total=False):
    """Electronic field response information."""

    #: Number of ions in system.
    ions: int
    #: Number of phonon branches.
    branches: int
    #: Number of frequencies.
    frequencies: int
    #: Oscillator Q.?
    oscillator_Q: list[float]
    #: Oscillator strengths in (D/A)**2 / amu.
    oscillator_strengths: EFieldTensor
    #: Electrical permittivity.
    permittivity: EFieldTensor


@file_or_path(mode="r")
def parse_efield_file(efield_file: TextIO) -> EFieldInfo:
    """
    Parse castep .efield file.

    Parameters
    ----------
    efield_file : ~typing.TextIO
        Open handle to file to parse.

    Returns
    -------
    EFieldInfo
        Parsed info.
    """
    # pylint: disable=too-many-branches,redefined-outer-name

    efield_info: EFieldInfo = defaultdict(list)
    logger = log_factory(efield_file)

    for line in efield_file:
        if block := Block.from_re(line, efield_file, "BEGIN header", "END header"):
            data = parse_regular_header(block, ("Oscillator Q",))
            efield_info.update(data)

        elif block := Block.from_re(
            line, efield_file, "BEGIN Oscillator Strengths", "END Oscillator Strengths",
        ):
            logger("Found Oscillator Strengths")

            osc = defaultdict(list)
            block.remove_bounds(1, 2)
            for line in block:
                match = re.match(rf"\s*(?P<freq>{REs.INTNUMBER_RE})" + labelled_floats(SND_D), line)
                stack_dict(osc, match.groupdict())

            if osc:
                fix_data_types(osc, {"freq": float, **dict.fromkeys(SND_D, float)})
                efield_info["oscillator_strengths"].append(osc)

        elif block := Block.from_re(line, efield_file, "BEGIN permittivity", "END permittivity"):
            logger("Found permittivity")

            perm = defaultdict(list)
            block.remove_bounds(1, 2)
            for line in block:
                match = re.match(labelled_floats(["freq", *SND_D]), line)
                stack_dict(perm, match.groupdict())

            if perm:
                fix_data_types(perm, {"freq": float, **dict.fromkeys(SND_D, float)})
                efield_info["permittivity"].append(perm)

    return efield_info
