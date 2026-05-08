"""Parse castep .hug files."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TextIO, TypedDict

from castep_outputs.utilities.castep_res import labelled_floats
from castep_outputs.utilities.type_conv import fix_data_types
from castep_outputs.utilities.utility import file_or_path, stack_dict


class HugFileInfo(TypedDict):
    """Hugoniot information."""

    #: Percentage change in lattice parameters.
    compression: tuple[float, ...]
    #: Temperature at given compression.
    temperature: tuple[float, ...]
    #: Pressure at given compression.
    pressure: tuple[float, ...]
    #: Total energy at given compression.
    energy: tuple[float, ...]


@file_or_path(mode="r")
def parse_hug_file(hug_file: TextIO) -> HugFileInfo:
    """
    Parse castep .hug file.

    Parameters
    ----------
    hug_file
        Open handle to file to parse.

    Returns
    -------
    :
        Parsed info.
    """
    cols = ("compression", "temperature", "pressure", "energy")
    data = defaultdict(list)
    for line in hug_file:
        if match := re.search(labelled_floats(cols), line):
            stack_dict(data, match.groupdict())

    fix_data_types(data, dict.fromkeys(cols, float))
    return data
