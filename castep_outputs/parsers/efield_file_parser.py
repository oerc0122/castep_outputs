"""
Parse the following castep outputs:
.efield
"""
import re
from collections import defaultdict
from typing import Dict, TextIO, Union

from ..utilities import castep_res as REs
from ..utilities.castep_res import get_block, labelled_floats
from ..utilities.constants import SND_D
from ..utilities.utility import fix_data_types, log_factory, stack_dict
from .parse_utilities import parse_regular_header


def parse_efield_file(efield_file: TextIO) -> Dict[str, Union[float, int]]:
    """ Parse castep .efield file """
    # pylint: disable=too-many-branches,redefined-outer-name

    efield_info = defaultdict(list)
    logger = log_factory(efield_file)

    for line in efield_file:
        if block := get_block(line, efield_file, "BEGIN header", "END header"):
            data = parse_regular_header(block, ('Oscillator Q',))
            efield_info.update(data)

        elif block := get_block(line, efield_file, "BEGIN Oscillator Strengths",
                                "END Oscillator Strengths",
                                out_fmt=list):

            logger("Found Oscillator Strengths")

            osc = defaultdict(list)
            for line in block[1:-2]:
                match = re.match(rf"\s*(?P<freq>{REs.INTNUMBER_RE})" +
                                 labelled_floats([*(f'S{d}' for d in SND_D)]), line)
                stack_dict(osc, match.groupdict())

            if osc:
                fix_data_types(osc, {'freq': float,
                                     **{f'S{d}': float for d in SND_D}})
                efield_info['oscillator_strengths'].append(osc)

        elif block := get_block(line, efield_file, "BEGIN permittivity", "END permittivity",
                                out_fmt=list):

            logger("Found permittivity")

            perm = defaultdict(list)
            for line in block[1:-2]:
                match = re.match(labelled_floats(['freq',
                                                  *(f'e_r_{d}' for d in SND_D)]), line)
                stack_dict(perm, match.groupdict())

            if perm:
                fix_data_types(perm, {'freq': float,
                                      **{f'e_r_{d}': float for d in SND_D}})
                efield_info['permittivity'].append(perm)

    return efield_info
