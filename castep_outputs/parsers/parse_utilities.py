# pylint: disable=too-many-lines, too-many-branches, too-many-statements
"""Functions generally used in parsing castep files."""
from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence

from ..utilities import castep_res as REs
from ..utilities.castep_res import get_numbers
from ..utilities.filewrapper import Block
from ..utilities.utility import (
    atreg_to_index,
    fix_data_types,
    stack_dict,
    to_type,
)


def parse_regular_header(block: Block,
                         extra_opts: Sequence[str] = ()) -> dict[str, float | int]:
    """
    Parse (semi-)standard castep file header block (given as iterable over lines).

    Parameters
    ----------
    block
        Block to parse.
    extra_opts
        Extra regexes to match (stored as floats).

    Returns
    -------
    dict[str, float | int]
        Parsed header block.
    """
    data = {}
    coords = defaultdict(list)
    for line in block:
        if line.strip().startswith("Number of"):
            _, _, *key, val = line.split()
            data[" ".join(key)] = int(float(val))
        elif "Unit cell vectors" in line:
            data["unit_cell"] = [to_type(next(block).split(), float)
                                 for _ in range(3)]

        elif match := REs.ATOMIC_DATA_3VEC.search(line):
            ind = atreg_to_index(match)
            coords[ind] = to_type(match.group("x", "y", "z"), float)

        elif match := REs.FRACCOORDS_RE.match(line):
            stack_dict(coords, match.groupdict())

        elif match := re.search(f"({'|'.join(extra_opts)})", line):
            data[match.group(0)] = to_type(get_numbers(line), float)

    fix_data_types(coords, {"index": int,
                            "u": float,
                            "v": float,
                            "w": float,
                            "mass": float})
    data["coords"] = coords
    return data
