"""Parse castep .err files."""
from __future__ import annotations

from typing import TextIO, TypedDict


class ErrFileInfo(TypedDict):
    """Error file information."""

    #: Message detailing cause of failure.
    message: str
    #: Backtrace at point of failure.
    stack: list[str]


def parse_err_file(err_file: TextIO) -> ErrFileInfo:
    """
    Parse castep .err files.

    Parameters
    ----------
    err_file
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
