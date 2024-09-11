"""Parse castep .elastic files."""
from __future__ import annotations

from collections import defaultdict
from typing import TextIO

from ..utilities.castep_res import get_numbers
from ..utilities.filewrapper import Block
from ..utilities.utility import to_type


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
    accum = defaultdict(list)

    for line in elastic_file:
        if block := Block.from_re(line, elastic_file,
                                  "^BEGIN Elastic Constants",
                                  "^END Elastic Constants"):

            accum["elastic_constants"] = [to_type(numbers, float)
                                          for blk_line in block
                                          if (numbers := get_numbers(blk_line))]

        elif block := Block.from_re(line, elastic_file,
                                    "^BEGIN Compliance Matrix",
                                    "^END Compliance Matrix"):
            next(block)  # Skip Begin line w/units

            accum["compliance_matrix"] = [to_type(numbers, float)
                                          for blk_line in block
                                          if (numbers := get_numbers(blk_line))]

    return accum
