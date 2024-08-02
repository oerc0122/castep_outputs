# pylint: disable=too-many-lines, too-many-branches, too-many-statements
"""
Functions generally used in parsing castep files
"""

import re
from collections import defaultdict
from typing import Any, Dict, List, Sequence, TextIO, Tuple, Union

from ..utilities import castep_res as REs
from ..utilities.utility import (atreg_to_index, determine_type,
                                 fix_data_types, normalise_key, stack_dict,
                                 to_type)


def parse_regular_header(block: TextIO,
                         extra_opts: Sequence[str] = tuple()) -> Dict[str, Union[float, int]]:
    """ Parse (semi-)standard castep file header block (given as iterable over lines) """
    val: Any
    key: Union[str, Sequence[str]]

    data = {}
    coords = defaultdict(list)
    for line in block:
        if line.strip().startswith("Number of"):
            _, _, *key, val = line.split()
            key = normalise_key(" ".join(key))
            data[key] = int(float(val))
        elif "Unit cell vectors" in line:
            data['unit_cell'] = [to_type(next(block).split(), float)
                                 for _ in range(3)]

        elif match := REs.ATDAT3VEC.search(line):
            ind = atreg_to_index(match)
            coords[ind] = to_type(match.group("x", "y", "z"), float)

        elif match := REs.FRACCOORDS_RE.match(line):
            val = match.groupdict()
            ind = atreg_to_index(val)
            fix_data_types(val, {'u': float,
                                 'v': float,
                                 'w': float,
                                 'mass': float})
            coords[ind] = val

        elif extra_opts and (match := re.search(f"({'|'.join(extra_opts)})", line)):
            key = normalise_key(match.group(0))
            val = line[match.end():].split()
            if len(val) == 1:
                data[key] = to_type(val[0], determine_type(val[0]))
            else:
                data[key] = to_type(val, determine_type(val[0]))

    if coords:
        data['coords'] = coords

    return data


def parse_kpt_info(inp: TextIO, prop: Union[str, Tuple[str]]) -> Dict[str, List[Union[int, float]]]:
    """ Parse standard form of kpt related .*_fmt files """

    # Skip header
    while "END header" not in inp.readline():
        pass

    qdata = defaultdict(list)
    for line in inp:
        if not line.strip():
            continue
        if isinstance(prop, str):
            *qpt, val = line.split()
            qpt = to_type(qpt, int)
            val = to_type(val, float)
            stack_dict(qdata, {'q': qpt, prop: val})
        elif isinstance(prop, tuple):
            words = line.split()
            qpt = to_type(words[0:3], int)
            val = to_type(words[3:], float)
            stack_dict(qdata, {'q': qpt, **dict(zip(prop, val))})

    return qdata
