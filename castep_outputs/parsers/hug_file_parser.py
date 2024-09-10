"""
Parse the following castep outputs:
.hug
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import TextIO

from ..utilities.castep_res import labelled_floats
from ..utilities.utility import fix_data_types, stack_dict


def parse_hug_file(hug_file: TextIO) -> dict[str, list[float]]:
    """ Parse castep .hug file """

    cols = ("compression", "temperature", "pressure", "energy")
    data = defaultdict(list)
    for line in hug_file:
        if match := re.search(labelled_floats(cols), line):
            stack_dict(data, match.groupdict())

    fix_data_types(data, {dt: float for dt in cols})
    return data
