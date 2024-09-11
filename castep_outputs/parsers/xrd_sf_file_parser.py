"""Parse castep .xrd_sf files."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import TextIO, TypedDict

from ..utilities import castep_res as REs
from ..utilities.castep_res import labelled_floats
from ..utilities.datatypes import ThreeVector
from ..utilities.utility import stack_dict, to_type


class XRDSFFileInfo(TypedDict):
    """X-Ray Structure Factor computation."""

    #: Structure factor contribution due to the all-electron valence
    #: augmentation charge.
    f_aug: list[complex]
    #: Indepedent atom model structure factor; electron density formed
    #: from superposition of atomic electron densities obtained by
    #: numerically solving the Koelling-Harmon equation.
    f_iam: list[complex]
    #: DFT structure factor with all-electron augmentation charge.
    f_paw: list[complex]
    #: DFT structure factor with pseudised (inaccurate) augmentation charge
    f_pp: list[complex]
    #: Structure factor contribution to `f_paw` due to the (frozen) core electrons.
    f_core: list[complex]
    #: Structure factor contribution to `f_paw` due to the soft valence
    #: charge (where augmentation charge contribute is removed).
    f_soft: list[complex]
    #: Reciprocal lattice directions of structure factor calculation.
    qvec: list[ThreeVector]


def parse_xrd_sf_file(xrd_sf_file: TextIO) -> XRDSFFileInfo:
    """
    Parse castep .xrd_sf file.

    Parameters
    ----------
    xrd_sf_file
        Open handle to file to parse.

    Returns
    -------
    XRDSFFileInfo
        Parsed info.
    """
    # Get headers from first line
    headers = xrd_sf_file.readline().split()[3:]
    # Turn Re(x) into x_re
    headers = [(head[3:-1]+"_"+head[0:2]).lower() for head in headers]
    headers_wo = {head[:-3] for head in headers}

    xrd_re = re.compile(rf"(?P<qvec>(?:\s*{REs.INTNUMBER_RE}){{3}})" +
                        labelled_floats(headers))

    xrd: XRDSFFileInfo = defaultdict(list)
    for line in xrd_sf_file:
        match = xrd_re.match(line).groupdict()
        accum = {head: complex(float(match[f"{head}_re"]),
                               float(match[f"{head}_im"]))
                 for head in headers_wo}
        accum["qvec"] = to_type(match["qvec"].split(), int)
        stack_dict(xrd, accum)

    return xrd
