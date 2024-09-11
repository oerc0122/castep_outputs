"""Parse castep .phonon_dos files."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import TextIO, TypedDict

from ..utilities import castep_res as REs
from ..utilities.castep_res import labelled_floats
from ..utilities.datatypes import StandardHeader, ThreeVector
from ..utilities.filewrapper import Block
from ..utilities.utility import fix_data_types, log_factory, stack_dict
from .parse_utilities import parse_regular_header


class GradientInfo(TypedDict, total=False):
    """Info on phonon DOS gradients."""

    #: :math:`q`-point weight.
    pth: list[float]
    #: :math:`q`-point.
    qpt: ThreeVector
    #: Branch index.
    n: list[int]
    #: :math:`f` at point.
    f: list[float]
    #: :math:`\nabla_{q} \cdot f` at :math:`q`-point.
    Grad_qf: list[float]


class DOSInfo(TypedDict, total=False):
    """
    Density of states contribution.

    Notes
    -----
    Also includes per-species contributions whose keys are
    the species.
    """

    #: Frequencies.
    freq: list[float]
    #: Density out to Frequncy.
    g: list[float]


class PhononDosFileInfo(StandardHeader, total=False):
    """Phonon Density of states info."""

    #: Number of ions in system.
    ions: int
    #: Number of species in system.
    species: int
    #: Number of phonon branches.
    branches: int
    #: Phonon density of states information.
    dos: list[DOSInfo]
    #: Phonon DoS gradients information.
    gradients: list[GradientInfo]


def parse_phonon_dos_file(phonon_dos_file: TextIO) -> PhononDosFileInfo:
    """
    Parse castep .phonon_dos file.

    Parameters
    ----------
    phonon_dos_file
        Open handle to file to parse.

    Returns
    -------
    PhononDosFileInfo
        Parsed info.
    """
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
                fix_data_types(qdat, {"qpt": float,
                                      "pth": float,
                                      "n": int,
                                      "f": float,
                                      "Grad_qf": float})

            for line in block:
                if match := REs.PHONON_PHONON_RE.match(line):
                    if qdata:
                        fix(qdata)
                        phonon_dos_info["gradients"].append(qdata)

                    qdata = defaultdict(list)

                    for key, val in match.groupdict().items():
                        qdata[key] = val.split()

                elif match := REs.PROCESS_PHONON_PHONON_RE.match(line):
                    stack_dict(qdata, match.groupdict())

            if qdata:
                fix(qdata)
                phonon_dos_info["gradients"].append(qdata)

        elif block := Block.from_re(line, phonon_dos_file, "BEGIN DOS", "END DOS"):

            logger("Found DOS block")

            dos = defaultdict(list)
            # First chunk is " BEGIN DOS   Freq (cm-1)  g(f)", thus need the 5th on
            species = block[0].split()[5:]
            headers = ("freq", "g", *species)
            rows = re.compile(labelled_floats(headers))

            block.remove_bounds(1, 2)

            for line in block:
                match = rows.match(line)
                stack_dict(dos, match.groupdict())

            if dos:
                fix_data_types(dos, {key: float for key in headers})
                phonon_dos_info["dos"].append(dos)

    return phonon_dos_info
