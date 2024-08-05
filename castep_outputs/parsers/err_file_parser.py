"""
Parse the following castep outputs:

- .err
"""
from typing import List, TextIO, TypedDict


class ErrFileInfo(TypedDict):
    """
    Error file information.
    """
    message: str
    stack: List[str]


def parse_err_file(err_file: TextIO) -> ErrFileInfo:
    """
    Parse castep .cell and param files.

    Parameters
    ----------
    cell_param_file : ~typing.TextIO
        Open handle to file to parse.

    Returns
    -------
    ErrFileInfo
        Parsed info.
    """
    accum: ErrFileInfo = {"message": "", "stack": []}

    while "Current trace stack" not in (line := err_file.readline()):
        accum["message"] += line
    accum["message"] = accum["message"].strip()

    for line in err_file:
        accum["stack"].append(line.strip())

    return accum
