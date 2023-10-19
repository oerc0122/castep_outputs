"""
Module to assist processing of parsed outputs.
"""

from typing import NamedTuple
from .castep_res import get_atom_parts


class Label(NamedTuple):
    """
    Standard castep atom label
    """
    species: str
    index: int
    label: str = ""

    @staticmethod
    def from_str(string: str):
        """ Build a label from a key-string """
        return Label(**get_atom_parts(string))
