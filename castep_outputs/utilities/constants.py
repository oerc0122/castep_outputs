"""Module for constants used in castep_outputs."""

from typing import Literal

#: Atomic orbitals.
SHELLS = ("s", "p", "d", "f")

#: First order cartesian directions.
FST_D = ("x", "y", "z")

#: Second order cartesian directions in Voigt notation.
SND_D = ("xx", "yy", "zz", "yz", "xz", "xy")

#: Valid CASTEP minimisers.
MINIMISERS = ("bfgs", "lbfgs", "fire", "tpsd", "dmd", "di")

#: Valid CASTEP pair potentials.
PAIR_POTS = ("LJ", "BUCK", "COUL", "DZ", "POL", "BB", "SHO",
             "SW", "MORS", "POLM", "LJ_S", "PES", "BU_S", "TIP4", "QUIP")

#: Aliases in .geom/.md files to fill names.
TAG_ALIASES = {"E": "energy",
               "T": "temperature",
               "P": "pressure",
               "h": "lattice_vectors",
               "hv": "lattice_velocity",
               "S": "stress",
               "R": "position",
               "V": "velocity",
               "F": "force"}

#: Input/output types used in transition state searches.
TS_TYPES = {"REA": "reagent",
            "PRO": "product",
            "TST": "test"}

#: Valid formats castep_outputs can dump to.
OutFormats = Literal["json", "pprint", "print", "ruamel", "yaml"]
