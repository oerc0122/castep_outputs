"""Parse castep .magres files."""
from __future__ import annotations

from collections import defaultdict
from typing import Literal, TextIO, TypedDict

from ..utilities.datatypes import AtomIndex, ThreeVector
from ..utilities.filewrapper import Block
from ..utilities.utility import to_type


class UnitsInfo(TypedDict):
    """Information on magres units."""

    #: Position units.
    atom: str
    #: Lattice length units.
    lattice: str
    #: Magnetic reponse units.
    ms: str


class MagresInfo(TypedDict):
    """NMR Magnetic reponse information."""

    #: Atom coordinates
    atoms: dict[AtomIndex, ThreeVector]
    calc_code: Literal["CASTEP"]
    calc_code_hgversion: str
    calc_code_platform: str
    calc_code_version: str
    calc_cutoffenergy: str
    calc_kpoint_mp_grid: str
    calc_kpoint_mp_offset: str
    calc_name: str
    calc_pspot: str
    calc_xcfunctional: str
    #: Crystal lattice.
    lattice: tuple[float, float, float,
                   float, float, float,
                   float, float, float]
    #: Magnetic susceptibility tensor.
    ms: dict[AtomIndex, list[float]]
    units: UnitsInfo


def parse_magres_file(magres_file: TextIO) -> MagresInfo:
    """
    Parse castep .magres file.

    Parameters
    ----------
    magres_file
        Open handle to file to parse.

    Returns
    -------
    MagresInfo
        Parsed info.
    """
    # pylint: disable=too-many-branches

    accum = defaultdict(dict)

    for line in magres_file:
        if block := Block.from_re(line, magres_file, r"^\s*\[\w+\]\s*$", r"^\s*\[/\w+\]\s*$"):

            block_name = next(block).strip().strip("[").strip("]")

            if block_name == "calculation":
                for blk_line in block:
                    if blk_line.startswith("["):
                        continue

                    key, *val = blk_line.strip().split(maxsplit=1)

                    if val:
                        accum[key] = val[0]

            elif block_name == "atoms":
                for blk_line in block:
                    if blk_line.startswith("lattice"):

                        key, *val = blk_line.split()
                        accum[key] = to_type(val, float)

                    elif blk_line.startswith("atom"):

                        key, _, spec, ind, *pos = blk_line.split()
                        accum["atoms"][(spec, int(ind))] = to_type(pos, float)

                    elif blk_line.startswith("units"):
                        _, key, val = blk_line.split()
                        accum["units"][key] = val

            elif block_name == "magres":
                for blk_line in block:
                    if blk_line.startswith("ms"):

                        key, spec, ind, *val = blk_line.split()
                        accum[key][(spec, int(ind))] = to_type(val, float)

                    elif blk_line.startswith("units"):
                        _, key, val = blk_line.split()
                        accum["units"][key] = val

    return accum
