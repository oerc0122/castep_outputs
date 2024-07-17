"""
Parse the following castep outputs:
.phonon_dos
"""
import re
from collections import defaultdict
from typing import Any, Dict, TextIO

from ..utilities import castep_res as REs
from ..utilities.castep_res import get_block, labelled_floats
from ..utilities.utility import fix_data_types, log_factory, stack_dict
from .parse_utilities import parse_regular_header


def parse_phonon_dos_file(phonon_dos_file: TextIO) -> Dict[str, Any]:
    """ Parse castep .phonon_dos file """
    # pylint: disable=too-many-branches,redefined-outer-name
    logger = log_factory(phonon_dos_file)
    phonon_dos_info = defaultdict(list)

    for line in phonon_dos_file:
        if block := get_block(line, phonon_dos_file, "BEGIN header", "END header"):
            data = parse_regular_header(block)
            phonon_dos_info.update(data)

        elif block := get_block(line, phonon_dos_file, "BEGIN GRADIENTS", "END GRADIENTS"):

            logger("Found gradient block")
            qdata = defaultdict(list)

            def fix(qdat):
                fix_data_types(qdat, {'qpt': float,
                                      'pth': float,
                                      'n': int,
                                      'f': float,
                                      'Grad_qf': float})

            for line in block:
                if match := REs.PHONON_PHONON_RE.match(line):
                    if qdata:
                        fix(qdata)
                        phonon_dos_info['gradients'].append(qdata)
                    qdata = defaultdict(list)

                    for key, val in match.groupdict().items():
                        qdata[key] = val.split()

                elif match := REs.PROCESS_PHONON_PHONON_RE.match(line):
                    stack_dict(qdata, match.groupdict())

            if qdata:
                fix(qdata)
                phonon_dos_info['gradients'].append(qdata)

        elif block := get_block(line, phonon_dos_file, "BEGIN DOS", "END DOS", out_fmt=list):

            logger("Found DOS block")

            dos = defaultdict(list)
            for line in block[1:-2]:
                match = re.match(labelled_floats(('freq', 'g', 'si')), line)
                stack_dict(dos, match.groupdict())

            if dos:
                fix_data_types(dos, {'freq': float,
                                     'g': float,
                                     'si': float})
                phonon_dos_info['dos'].append(dos)

    return phonon_dos_info
