"""
Module for constants used in castep_outputs
"""

SHELLS = ('s', 'p', 'd', 'f')
FST_D = ('x', 'y', 'z')
SND_D = ('xx', 'yy', 'zz', 'yz', 'zx', 'xy')
MINIMISERS = ('bfgs', 'lbfgs', 'fire', 'tpsd', 'dmd')
PAIR_POTS = ('LJ', 'BUCK', 'COUL', 'DZ', 'POL', 'BB', 'SHO',
             'SW', 'MORS', 'POLM', 'LJ_S', 'PES', 'BU_S', 'TIP4', 'QUIP')

CASTEP_OUTPUT_NAMES = (
    "castep",
    "param",
    "cell",
    "geom",
    "md",
    "bands",
    "hug",
    "phonon_dos",
    "efield",
    "xrd_sf",
    "elf_fmt",
    "chdiff_fmt",
    "pot_fmt",
    "den_fmt"
)
CASTEP_FILE_FORMATS = tuple(f".{typ}" for typ in CASTEP_OUTPUT_NAMES)
