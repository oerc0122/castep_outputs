"""
Module for constants used in castep_outputs
"""

from typing import Literal, Tuple

SHELLS = ('s', 'p', 'd', 'f')
FST_D = ('x', 'y', 'z')
SND_D = ('xx', 'yy', 'zz', 'yz', 'zx', 'xy')
MINIMISERS = ('bfgs', 'lbfgs', 'fire', 'tpsd', 'dmd', 'di')
PAIR_POTS = ('LJ', 'BUCK', 'COUL', 'DZ', 'POL', 'BB', 'SHO',
             'SW', 'MORS', 'POLM', 'LJ_S', 'PES', 'BU_S', 'TIP4', 'QUIP')

TAG_ALIASES = {'E': 'energy',
               'T': 'temperature',
               'P': 'pressure',
               'h': 'lattice_vectors',
               'hv': 'lattice_velocity',
               'R': 'position',
               'V': 'velocity',
               'F': 'force'}

TS_TYPES = {"REA": "reagent",
            "PRO": "product",
            "TST": "test"}

OutFormats = Literal["json", "pprint", "print", "ruamel", "yaml"]
AtomIndex = Tuple[str, float]
ThreeVector = Tuple[float, float, float]
ThreeByThreeMatrix = Tuple[ThreeVector, ThreeVector, ThreeVector]
