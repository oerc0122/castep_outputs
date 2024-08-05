"""
Parse the following castep outputs:
.phonon_dos
"""
import re
from collections import defaultdict
from typing import Any, Dict, TextIO

from ..utilities import castep_res as REs
from ..utilities.castep_res import labelled_floats
from ..utilities.filewrapper import Block
from ..utilities.utility import fix_data_types, log_factory, stack_dict
from .parse_utilities import parse_regular_header


def parse_phonon_dos_file(phonon_dos_file: TextIO) -> Dict[str, Any]:
    """ Parse castep .phonon_dos file """
    # pylint: disable=too-many-branches,redefined-outer-name
    logger = log_factory(phonon_dos_file)
    phonon_dos_info = defaultdict(list)

    for line in phonon_dos_file:
        if block := Block.from_re(line, phonon_dos_file, "BEGIN header", "END header"):
            data = parse_regular_header(block)
            phonon_dos_info.update(data)

        elif block := Block.from_re(line, phonon_dos_file, "BEGIN GRADIENTS", "END GRADIENTS"):

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

        elif block := Block.from_re(line, phonon_dos_file, "BEGIN DOS", "END DOS"):

            logger("Found DOS block")

            dos = defaultdict(list)
            # First chunk is " BEGIN DOS   Freq (cm-1)  g(f)", thus need the 5th on
            species = block[0].split()[5:]
            headers = ('freq', 'g', *species)
            rows = re.compile(labelled_floats(headers))

            block.remove_bounds(1, 2)

            for line in block:
                match = rows.match(line)
                stack_dict(dos, match.groupdict())

            if dos:
                fix_data_types(dos, {key: float for key in headers})
                phonon_dos_info['dos'].append(dos)

    return phonon_dos_info
