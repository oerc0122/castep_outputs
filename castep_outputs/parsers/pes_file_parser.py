"""Parse castep .pes files."""

from __future__ import annotations

from typing import TextIO, TypedDict

from ..utilities.datatypes import ThreeByThreeMatrix, ThreeVector
from ..utilities.filewrapper import Block
from ..utilities.utility import file_or_path, to_type


class PESData(TypedDict):
    """PES sample points."""

    pos: ThreeVector
    e: float
    f_opt: float | None


class PESFileInfo(TypedDict, total=False):
    """Full pes file information."""

    probe_species: str
    probe_method: str
    cell: ThreeByThreeMatrix
    date_started: str
    data: list[PESData]
    units: dict[str, str]
    samples: dict[str, int]


def _parse_header(header: Block) -> PESFileInfo:
    accum: PESFileInfo = {"units": {}, "samples": {}, "data": []}

    header = map(str.strip, header)

    for line in header:
        if line.startswith("Job:"):
            _, accum["probe_method"] = line.split(": ")
        elif line.startswith("Probe species:"):
            _, accum["probe_species"] = line.split(": ")
        elif "unit:" in line:
            typ_, _, unit = line.split()
            accum["units"][typ_.lower()] = unit
        elif line.startswith("Number of samples"):
            *_, direc, count = line.split()
            accum["samples"][direc.strip(":")] = int(count)
        elif line.startswith("Cell Vectors"):
            *_, unit = line.split()
            accum["units"]["cell"] = unit.strip("()")
            accum["cell"] = tuple(to_type(cell.split(), float)
                                  for cell, _ in zip(header, range(3)))
        elif line.startswith("Date"):
            _, accum["date_started"] = line.split(": ", maxsplit=1)

    return accum


@file_or_path(mode="r")
def parse_pes_file(pes_file: TextIO) -> PESFileInfo:
    """Parse castep .pes file.

    Parameters
    ----------
    pes_file
        A handle to a CASTEP .pes file.

    Returns
    -------
    PESFileInfo
        Parsed data.
    """
    line = next(pes_file)
    block = Block.from_re(line, pes_file, "BEGIN header", "END header")

    accum = _parse_header(block)

    line = next(pes_file)
    block = Block.from_re(line, pes_file, " BLOCK DATA", "ENDBLOCK DATA")
    block.remove_bounds(1, 1)

    data = accum["data"]

    for line in block:
        a, b, c, e, *extra = to_type(line.split(), float)

        curr = {}
        curr["pos"] = a, b, c
        curr["e"] = e
        curr["f_opt"] = extra[0] if extra else None

        data.append(curr)

    return accum
