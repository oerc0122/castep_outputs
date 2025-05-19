"""Module to assist processing of parsed outputs."""

from typing import NamedTuple, TypeVar

from ..utilities.castep_res import get_atom_parts

Self = TypeVar("Self", bound="AtomLabel")


class AtomLabel(NamedTuple):
    """Standard castep atom label."""

    #: Atom species.
    species: str
    #: Index into positions block.
    index: int
    #: Extra tag information.
    tag: str = ""
    #: Overridden internal name via label.
    label: str = ""

    @classmethod
    def from_str(cls, string: str) -> Self:
        """
        Build a label from a key-string.

        Parameters
        ----------
        string
            String to parse.

        Returns
        -------
        AtomLabel
            Processed string.
        """
        return cls(**get_atom_parts(string))
