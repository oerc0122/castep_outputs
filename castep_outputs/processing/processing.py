"""
Module to assist processing of parsed outputs.
"""

from typing import NamedTuple

from ..utilities.castep_res import get_atom_parts


class AtomLabel(NamedTuple):
    """
    Standard castep atom label
    """
    species: str
    index: int
    tag: str = ""
    label: str = ""

    @staticmethod
    def from_str(string: str):
        """ Build a label from a key-string """
        return AtomLabel(**get_atom_parts(string))
