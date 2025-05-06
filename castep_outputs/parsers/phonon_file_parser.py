"""Parse castep .phonon files."""
from __future__ import annotations

from collections import defaultdict
from typing import TextIO

from ..utilities.datatypes import ComplexThreeVector, QData, StandardHeader, ThreeVector
from ..utilities.filewrapper import Block
from ..utilities.utility import file_or_path, log_factory, to_type
from .parse_utilities import parse_regular_header


class PhononFileQPoint(QData, total=False):
    """Q-point info from a phonon file."""

    #: Direction to next Q-point
    dir: ThreeVector
    #: Eigenvalues of Q-point.
    eigenvalues: list[float]
    #: Eigenvectors of Q-point.
    eigenvectors: list[ComplexThreeVector]


class PhononFileInfo(StandardHeader, total=False):
    """Full phonon file information."""

    #: Number of ions in system.
    ions: int
    #: Number of phonon branches.
    branches: int
    #: Number of wavevectors in calculation.
    wavevectors: int
    #: Per Q-point information.
    qpts: list[PhononFileQPoint]


@file_or_path(mode="r")
def parse_phonon_file(phonon_file: TextIO) -> PhononFileInfo:
    """Parse castep .phonon file.

    Parameters
    ----------
    phonon_file
        A handle to a CASTEP .phonon file.

    Raises
    ------
    ValueError
        Branches count doesn't match expected.

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
                raise ValueError("Malformed phonon frequencies. "
                                 f"Expected {phonon_info['branches']} branches, "
                                 f"received {len(block) - 2}")

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

            expected_n_eigenvec = phonon_info["branches"] * phonon_info["ions"]
            if len(block) - 1 != expected_n_eigenvec:
                raise ValueError("Malformed eigenvectors. "
                                 f"Expected {expected_n_eigenvec} branches, "
                                 f"received {len(block) - 1}")

            block.remove_bounds(1, 0)

            for line in block:
                _, _, *eigenvectors = line.split()
                eigenvectors = to_type(eigenvectors, float)
                eigenvectors = map(complex, eigenvectors[::2], eigenvectors[1::2])
                qdata["eigenvectors"].append(tuple(eigenvectors))

            phonon_info["qpts"].append(qdata)

    return phonon_info
