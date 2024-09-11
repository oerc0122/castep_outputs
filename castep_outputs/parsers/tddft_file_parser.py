"""Parse castep .tddft files."""
from __future__ import annotations

import re
from typing import Dict, Literal, TextIO, Tuple, TypedDict, Union

from ..utilities import castep_res as REs
from ..utilities.castep_res import get_numbers, labelled_floats
from ..utilities.datatypes import ComplexThreeVector, StandardHeader
from ..utilities.filewrapper import Block
from ..utilities.utility import to_type
from .parse_utilities import parse_regular_header

#: Overlap type
TDDFTOverlap = Dict[Union[Tuple[int, int], Literal["total"]], float]


class TDDFTSpectroData(TypedDict):
    """Spectroscopic data for single excitation."""

    #: Excitation character.
    characterisation: Literal["Singlet", "Doublet", "unknown"]
    #: Whether excitation is converged.
    converged: bool
    #: Dipole vectors.
    dipoles: ComplexThreeVector
    #: Energy of excitation.
    energy: float


class TDDFTFileInfo(StandardHeader, total=False):
    """TDDFT state occupation info."""

    #: Band overlap for excitations.
    overlap: list[TDDFTOverlap]
    #: Spectroscopic data of excitations.
    spectroscopic_data: list[TDDFTSpectroData]


def parse_tddft_file(tddft_file: TextIO) -> TDDFTFileInfo:
    """
    Parse castep .tddft file.

    Parameters
    ----------
    tddft_file
        Open handle to file to parse.

    Returns
    -------
    TDDFTFileInfo
        Parsed info.
    """
    tddft_info = {}

    for line in tddft_file:
        if block := Block.from_re(line, tddft_file, "BEGIN header", "END header"):
            data = parse_regular_header(block, ("Higest occupied band",))
            tddft_info.update(data)

        elif block := Block.from_re(line, tddft_file,
                                    "BEGIN Characterisation of states as Kohn-Sham bands",
                                    "END Characterisation of states as Kohn-Sham bands"):

            tddft_info["overlap"] = []
            curr = {}

            for blk_line in block:
                if match := REs.TDDFT_STATE_RE.match(blk_line):
                    curr[(int(match["occ"]), int(match["unocc"]))] = float(match["overlap"])

                elif match := re.match(r"\s*Total overlap for state", blk_line):
                    curr["total"] = float(get_numbers(blk_line)[-1])
                    tddft_info["overlap"].append(curr)
                    curr = {}

        elif block := Block.from_re(line, tddft_file,
                                    "BEGIN TDDFT Spectroscopic Data",
                                    "END TDDFT Spectroscopic Data"):

            tddft_info["spectroscopic_data"] = []

            for blk_line in block:
                if match := re.match(rf"\s*\d+\s*{labelled_floats(('energy',))}"
                                     r"\s*(?P<characterisation>\w+)\s*"
                                     r"(?P<converged>Yes|No)\s*(?P<dipoles>.*)", blk_line):

                    match = match.groupdict()
                    match["converged"] = match["converged"] == "Yes"
                    match["energy"] = float(match["energy"])

                    dip = list(to_type(get_numbers(match["dipoles"]), float))
                    dip = [complex(real, imag) for real, imag in zip(dip[0::2], dip[1::2])]
                    match["dipoles"] = dip
                    tddft_info["spectroscopic_data"].append(match)

    return tddft_info
