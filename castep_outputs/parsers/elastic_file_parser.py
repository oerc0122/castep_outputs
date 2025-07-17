"""Parse castep .elastic files."""
from __future__ import annotations

from collections import defaultdict
from typing import TextIO

from ..utilities.castep_res import ELASTIC_BLOCK_RE, ELASTIC_INTERNAL_STRAIN_RE, get_numbers
from ..utilities.filewrapper import Block
from ..utilities.utility import atreg_to_index, file_or_path, normalise_key, to_type
from .parse_utilities import parse_regular_header


@file_or_path(mode="r")
def parse_elastic_file(elastic_file: TextIO) -> dict[str, list[list[float]]]:
    """
    Parse castep .elastic files.

    Parameters
    ----------
    elastic_file
        Open handle to file to parse.

    Returns
    -------
    dict[str, list[list[float]]]
        Parsed info.
    """
    accum = {}

    for line in elastic_file:
        if block := Block.from_re(line, elastic_file,
                                  "BEGIN header", "END header"):
            accum.update(parse_regular_header(block))
            accum.pop("")

        elif block := Block.from_re(line, elastic_file,
                                    "BEGIN Internal Strain", "END"):
            match = ELASTIC_BLOCK_RE.match(next(block))
            key = normalise_key(match["key"]).removesuffix("_xx_yy_zz_yz_zx_xy")
            accum[key] = defaultdict(list)
            accum[key]["units"] = match["unit"]

            block.remove_bounds(fore=0, back=1)
            for blk_line in block:
                match = ELASTIC_INTERNAL_STRAIN_RE.match(blk_line).groupdict()
                atom = atreg_to_index(match)
                accum[key][atom].append(to_type(get_numbers(blk_line), float))

        elif block := Block.from_re(line, elastic_file,
                                    "BEGIN", "END"):
            match = ELASTIC_BLOCK_RE.match(next(block))
            key = normalise_key(match["key"]).removesuffix("_xx_yy_zz_yz_zx_xy")

            accum[key] = {"units": match["unit"]}
            accum[key]["val"] = tuple(to_type(numbers, float)
                                      for blk_line in block
                                      if (numbers := get_numbers(blk_line)))

    return accum
