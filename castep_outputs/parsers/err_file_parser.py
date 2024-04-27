"""
Parse the following castep outputs:
.err
"""
from typing import Dict, List, TextIO, Union


def parse_err_file(err_file: TextIO) -> Dict[str, Union[str, List[str]]]:
    """ Parse .err file to dict """
    accum = {"message": "", "stack": []}

    while "Current trace stack" not in (line := err_file.readline()):
        accum["message"] += line
    accum["message"] = accum["message"].strip()

    for line in err_file:
        accum["stack"].append(line.strip())

    return accum
