"""Parse castep .phonon files."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, TextIO

from ..utilities.filewrapper import Block
from ..utilities.utility import fix_data_types, log_factory
from .parse_utilities import parse_regular_header


def parse_phonon_file(phonon_file: TextIO) -> dict[str, Any]:
    """Parse castep .phonon file."""
    # pylint: disable=too-many-locals
    logger = log_factory(phonon_file)
    phonon_info = defaultdict(list)
    evals = []
    evecs = []

    for line in phonon_file:
        if block := Block.from_re(line, phonon_file, "BEGIN header", "END header"):

            data = parse_regular_header(block)
            phonon_info.update(data)
            phonon_info.pop("", None)
            eigenvectors_endblock = (format(phonon_info["branches"], ">4") +
                                     format(phonon_info["ions"], ">4"))

        elif block := Block.from_re(line, phonon_file, "q-pt", "Phonon Eigenvectors"):

            logger("Found eigenvalue block")
            for line in block:
                if "q-pt" in line:
                    _, _, posx, posy, posz, *weight = line.split()
                    qdata = {"pos": [posx, posy, posz], "weight": weight}
                    fix_data_types(qdata, {"pos": float,
                                           "weight": float})
                    phonon_info["qpt_pos"].append(qdata["pos"])

                elif "Eigenvectors" not in line:
                    _, e_val, *_ = line.split()
                    qdata = {"eval": e_val}
                    fix_data_types(qdata, {"eval": float})
                    evals.append(qdata["eval"])
                    if len(evals) == phonon_info["branches"]:
                        phonon_info["evals"].append(evals)
                        evals = []

        elif block := Block.from_re(line, phonon_file, "Mode Ion", eigenvectors_endblock):

            logger("Found eigenvector block")
            for line in block:
                if "Mode" not in line:
                    _, _, *vectors = line.split()

                    qdata = {"evec": vectors}
                    fix_data_types(qdata, {"evec": float})
                    qdata["evec"] = [complex(qdata["evec"][i],
                                             qdata["evec"][i+1])
                                     for i in range(0, len(vectors), 2)]
                    evecs.append(qdata["evec"])

                    if len(evecs) == phonon_info["branches"]*phonon_info["ions"]:
                        phonon_info["evecs"].append(evecs)
                        evecs = []

    return phonon_info
