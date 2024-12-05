"""Parse castep .ts files."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import TextIO, TypedDict

from ..utilities.castep_res import ATOMIC_DATA_TAG, TAG_RE, get_numbers, labelled_floats
from ..utilities.constants import FST_D, TAG_ALIASES, TS_TYPES
from ..utilities.datatypes import ThreeByThreeMatrix
from ..utilities.filewrapper import Block
from ..utilities.utility import add_aliases, atreg_to_index, to_type


class TSStructInfo(TypedDict, total=False):
    """
    Structure info of the intermediate states of a TSS.

    Notes
    -----
    Also contains atom index keys of {AtomIndex: dict}
    """

    #: Total Energy and Enthalpy of system in Ha.
    energy: tuple[float, float]
    #: Alias of :attr:`energy`.
    E: tuple[float, float]
    #: Cell vectors of system in Bohr.
    lattice_vectors: ThreeByThreeMatrix
    #: Alias of :attr:`lattice_vectors`.
    h: ThreeByThreeMatrix


class TSFileInfo(TypedDict):
    """Transition state search file info."""

    #: Calculation is TSS confirmation.
    confirmation: bool
    #: Reagent info.
    reagent: TSStructInfo
    #: Product info.
    product: TSStructInfo
    #: Test info.
    test: TSStructInfo


def parse_ts_file(ts_file: TextIO) -> TSFileInfo:
    """
    Parse castep .ts file.

    Parameters
    ----------
    ts_file
        Open handle to file to parse.

    Returns
    -------
    TSFileInfo
        Parsed info.
    """
    accum = defaultdict(list)

    for line in ts_file:
        if "TSConfirmation" in line:
            accum["confirmation"] = True

        elif block := Block.from_re(line, ts_file, "(REA|PRO|TST)", r"^\s*$", eof_possible=True):
            curr = defaultdict(list)
            match = re.match(r"\s*(?P<type>REA|PRO|TST)\s*\d+\s*" +
                             labelled_floats(("reaction_coordinate",)), line)
            key = TS_TYPES[match["type"]]
            curr["reaction_coordinate"] = to_type(match["reaction_coordinate"], float)

            for blk_line in block:
                if match := ATOMIC_DATA_TAG.search(blk_line):
                    ion = atreg_to_index(match)
                    if ion not in curr:
                        curr[ion] = {}
                    curr[ion][match.group("tag")] = to_type([*(match.group(d)
                                                               for d in FST_D)], float)
                    add_aliases(curr[ion], TAG_ALIASES)

                elif match := TAG_RE.search(blk_line):
                    curr[match.group("tag")].append([*to_type(get_numbers(blk_line), float)])

            add_aliases(curr, TAG_ALIASES)
            accum[key].append(curr)

    return accum
