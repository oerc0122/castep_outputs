"""
Function for parsing xrd_sf files
"""

import re
from collections import defaultdict
from typing import Dict, TextIO, Union

from ..utilities import castep_res as REs
from ..utilities.castep_res import labelled_floats
from ..utilities.utility import stack_dict, to_type


def parse_xrd_sf_file(xrd_sf_file: TextIO) -> Dict[str, Union[int, float]]:
    """ Parse castep .xrd_sf file """

    # Get headers from first line
    headers = xrd_sf_file.readline().split()[3:]
    # Turn Re(x) into x_re
    headers = [(head[3:-1]+"_"+head[0:2]).lower() for head in headers]
    headers_wo = {head[:-3] for head in headers}

    xrd_re = re.compile(rf"(?P<qvec>(?:\s*{REs.INTNUMBER_RE}){{3}})" +
                        labelled_floats(headers))

    xrd = defaultdict(list)
    for line in xrd_sf_file:
        match = xrd_re.match(line).groupdict()
        accum = {head: complex(float(match[f"{head}_re"]),
                               float(match[f"{head}_im"]))
                 for head in headers_wo}
        accum["qvec"] = to_type(match["qvec"].split(), int)
        stack_dict(xrd, accum)

    return xrd
