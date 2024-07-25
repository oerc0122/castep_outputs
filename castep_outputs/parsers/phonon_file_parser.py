"""
Parse the following castep outputs:

- .phonon
"""
from collections import defaultdict
from typing import TextIO

from ..utilities.datatypes import PhononFileInfo, PhononFileQPoint
from ..utilities.filewrapper import Block
from ..utilities.utility import log_factory, to_type
from .parse_utilities import parse_regular_header


def parse_phonon_file(phonon_file: TextIO) -> PhononFileInfo:
    """Parse castep .phonon file.

    Parameters
    ----------
    phonon_file
        A handle to a CASTEP .phonon file.

    Returns
    -------
    PhononFileInfo
        Parsed data.
    """
    # pylint: disable=too-many-locals

    logger = log_factory(phonon_file)
    phonon_info: PhononFileInfo = defaultdict(list)

    for line in phonon_file:
        if block := Block.from_re(line, phonon_file, "BEGIN header", "END header"):

            data = parse_regular_header(block)
            phonon_info.update(data)
            del phonon_info[""]
            eigenvectors_endblock = (format(phonon_info["branches"], ">4") +
                                     format(phonon_info["ions"], ">4"))

        elif block := Block.from_re(line, phonon_file, "q-pt", "Phonon Eigenvectors"):

            logger("Found eigenvalue block")

            _, _, posx, posy, posz, weight, *qpoint_dir = line.split()
            qdata: PhononFileQPoint = defaultdict(list)

            qdata["qpt"] = to_type((posx, posy, posz), float)
            qdata["weight"] = float(weight)

            if qpoint_dir:
                qdata["dir"] = to_type(qpoint_dir, float)

            if len(block) - 2 != phonon_info["branches"]:
                raise IOError("Malformed phonon frequencies. "
                              f"Expected {phonon_info['branches']} branches, "
                              f"received {len(block)-2}")

            block.remove_bounds(1, 1)

            for line in block:
                # Line columns taken from phonon.f90
                eigenvalue, ir_intensity, raman_intensity = (line[8:23],
                                                             line[31:46],
                                                             line[55:70])
                qdata["eigenvalues"].append(float(eigenvalue))
                if ir_intensity.strip():
                    qdata["ir_intensity"].append(float(ir_intensity))
                if raman_intensity.strip():
                    qdata["raman_intensity"].append(float(raman_intensity))

        elif block := Block.from_re(line, phonon_file, "Mode Ion", eigenvectors_endblock):

            logger("Found eigenvector block")

            total_samp = phonon_info["branches"] * phonon_info["ions"]
            if len(block) - 1 != total_samp:
                raise IOError("Malformed eigenvectors. "
                              f"Expected {total_samp} branches, "
                              f"received {len(block)-1}")

            block.remove_bounds(1, 0)

            for line in block:
                _, _, *eigenvectors = line.split()
                eigenvectors = to_type(eigenvectors, float)
                eigenvectors = map(complex, eigenvectors[::2], eigenvectors[1::2])
                qdata["eigenvectors"].append(tuple(eigenvectors))

            phonon_info["qpts"].append(qdata)

    return phonon_info
