"""Parse castep .md or .geom files."""
from __future__ import annotations

from collections import defaultdict
from typing import TextIO, TypedDict

from ..utilities.castep_res import ATOMIC_DATA_TAG, TAG_RE, get_numbers
from ..utilities.constants import FST_D, TAG_ALIASES
from ..utilities.datatypes import AtomIndex, ThreeByThreeMatrix, ThreeVector
from ..utilities.filewrapper import Block
from ..utilities.utility import add_aliases, atreg_to_index, to_type


class MDAtomProps(TypedDict):
    """Atom properties on MD and GeomOpt."""

    #: Force on atom in Ha/Bohr.
    force: ThreeVector
    #: Position of atom in Bohr.
    position: ThreeVector
    #: Velocity of atom in Bohr/aut.
    velocity: ThreeVector
    #: Alias of :attr:`force`
    F: ThreeVector
    #: Alias of :attr:`position`
    R: ThreeVector
    #: Alias of :attr:`velocity`
    V: ThreeVector


class MDGeomTimestepInfo(TypedDict, total=False):
    """
    MD and GeomOpt output info.

    Notes
    -----
    Also contains :any:`AtomIndex` keys to per-atom information.
    """

    #: Elapsed MD Time.
    time: float
    #: Current energies: total, potential, kinetic.
    energy: tuple[float, float, float]
    #: Instantaneous temperature.
    temperature: tuple[float]
    #: Hydrostatic pressure.
    pressure: tuple[float]
    #: Current cell vectors.
    lattice_vectors: ThreeByThreeMatrix
    #: Current cell changes.
    lattice_velocity: ThreeByThreeMatrix
    #: Current stresses.
    stress: ThreeByThreeMatrix
    #: Atomic properties
    ions: dict[AtomIndex, MDAtomProps]

    #: Alias of :attr:`energy`.
    E: list[float]
    #: Alias of :attr:`temperature`.
    T: list[float]
    #: Alias of :attr:`pressure`.
    P: list[float]
    #: Alias of :attr:`lattice_vectors`.
    h: ThreeByThreeMatrix
    #: Alias of :attr:`lattice_velocity`.
    hv: ThreeByThreeMatrix
    #: Alias of :attr:`stress`.
    S: ThreeByThreeMatrix


def parse_md_geom_frame(block: Block) -> MDGeomTimestepInfo:
    """
    Parse a single frame of a .md/.geom file.

    Parameters
    ----------
    block
        Block containing frame of data.

    Returns
    -------
    MDGeomTimestepInfo
        Parsed frame of data.
    """
    curr: MDGeomTimestepInfo = defaultdict(list)
    curr["ions"] = {}

    for line in block:
        if not line.strip():
            pass
        elif not TAG_RE.search(line):  # Timestep
            curr["time"] = to_type(get_numbers(line)[0], float)

        elif match := ATOMIC_DATA_TAG.match(line):
            ion = atreg_to_index(match)
            curr["ions"].setdefault(ion, {})
            curr["ions"][ion][match.group("tag")] = to_type([match.group(d) for d in FST_D], float)

        elif match := TAG_RE.search(line):
            curr[match.group("tag")].append([*to_type(get_numbers(line), float)])

    add_aliases(curr, TAG_ALIASES)
    for ion in curr["ions"].values():
        add_aliases(ion, TAG_ALIASES)

    return curr

def parse_md_geom_file(md_geom_file: TextIO) -> list[MDGeomTimestepInfo]:
    """
    Parse standard .md and .geom files.

    Parameters
    ----------
    md_geom_file
        Open handle to file to parse.

    Returns
    -------
    list[MDGeomTimestepInfo]
        Step-by-step Parsed info.
    """
    while "END header" not in md_geom_file.readline():
        pass
    md_geom_file.readline()
    steps = []
    while block := Block.from_re("", md_geom_file, "", "^$", eof_possible=True):
        steps.append(parse_md_geom_frame(block))

    return steps


# Aliases
parse_md_file = parse_md_geom_file
parse_geom_file = parse_md_geom_file
