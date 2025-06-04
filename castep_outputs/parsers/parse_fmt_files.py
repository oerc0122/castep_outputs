"""
Parse the following castep outputs.

- .elf_fmt
- .chdiff_fmt
- .pot_fmt
- .den_fmt
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import TextIO, TypedDict, cast

from ..utilities.utility import file_or_path, stack_dict, to_type


class ElfFileInfo(TypedDict, total=False):
    """Electron localisation function information."""

    #: :math:`q`-point sample.
    q: list[tuple[int, int, int]]
    #: Spin-split alpha channel localisation
    chi_alpha: tuple[float, ...]
    #: Spin-split beta channel localisation
    chi_beta: tuple[float, ...]
    #: Electron localisation function
    chi: tuple[float, ...]


class ChDiffFileInfo(TypedDict):
    """Charge difference information."""

    #: :math:`q`-point sample.
    q: list[tuple[int, int, int]]
    #: Difference between charge density and superposition of atomic densities.
    charge: tuple[float, ...]


class DenFileInfo(TypedDict):
    """Charge density information."""

    #: :math:`q`-point sample.
    q: list[tuple[int, int, int]]
    #: Charge density at point.
    charge: tuple[float, ...]


class PotFileInfo(TypedDict):
    """Potential information."""

    #: :math:`q`-point sample.
    q: list[tuple[int, int, int]]
    #: Charge density at point.
    pot: tuple[float, ...]


@file_or_path(mode="r")
def _parse_kpt_info(
        inp: TextIO,
) -> dict[str, list[int | float]]:
    """
    Parse standard form of kpt related .*_fmt files.

    Parameters
    ----------
    inp : TextIO
        File to parse.

    Returns
    -------
    dict[str, list[int | float]]
        Parsed data.
    """
    # Skip header
    while "END header" not in (line := inp.readline()):
        pass

    cols = re.search(r'"([^"]+)"', line).group(1)
    prop = tuple(cols.split()[3:]) if len(cols) > 3 else cols[3]

    qdata = defaultdict(list)

    for line in inp:
        if not line.strip():
            continue
        if isinstance(prop, str):
            *qpt, val = line.split()
            qpt = to_type(qpt, int)
            val = to_type(val, float)
            stack_dict(qdata, {"q": qpt, prop: val})
        elif isinstance(prop, tuple):
            words = line.split()
            qpt = to_type(words[0:3], int)
            val = to_type(words[3:], float)
            stack_dict(qdata, {"q": qpt, **dict(zip(prop, val))})

    return qdata


def parse_elf_fmt_file(elf_file: TextIO) -> ElfFileInfo:
    """
    Parse castep .elf_fmt file.

    Parameters
    ----------
    elf_file : ~typing.TextIO
        Open handle to file to parse.

    Returns
    -------
    ElfFileInfo
        Parsed info.
    """
    return cast(ElfFileInfo, _parse_kpt_info(elf_file))


def parse_chdiff_fmt_file(chdiff_file: TextIO) -> ChDiffFileInfo:
    """
    Parse castep .chdiff_fmt file.

    Parameters
    ----------
    chdiff_file : ~typing.TextIO
        Open handle to file to parse.

    Returns
    -------
    ChDiffFileInfo
        Parsed info.
    """
    return cast(ChDiffFileInfo, _parse_kpt_info(chdiff_file))


def parse_pot_fmt_file(pot_file: TextIO) -> PotFileInfo:
    """
    Parse castep .pot_fmt file.

    Parameters
    ----------
    pot_file : ~typing.TextIO
        Open handle to file to parse.

    Returns
    -------
    PotFileInfo
        Parsed info.
    """
    return cast(PotFileInfo, _parse_kpt_info(pot_file))


def parse_den_fmt_file(den_file: TextIO) -> DenFileInfo:
    """
    Parse castep .den_fmt file.

    Parameters
    ----------
    den_file : ~typing.TextIO
        Open handle to file to parse.

    Returns
    -------
    DenFileInfo
        Parsed info.
    """
    return cast(DenFileInfo, _parse_kpt_info(den_file))
