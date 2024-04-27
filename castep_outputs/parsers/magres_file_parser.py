"""
Parse the following castep outputs:
.magres
"""
from collections import defaultdict
from typing import Dict, TextIO

from ..utilities.castep_res import get_block
from ..utilities.utility import to_type


def parse_magres_file(magres_file: TextIO) -> Dict[str, float]:
    """ Parse .magres file to dict """
    # pylint: disable=too-many-branches

    accum = defaultdict(dict)

    for line in magres_file:
        if block := get_block(line, magres_file, r"^\s*\[\w+\]\s*$", r"^\s*\[/\w+\]\s*$"):

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
