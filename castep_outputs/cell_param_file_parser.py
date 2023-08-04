"""
Parse castep .cell and .param files
"""
from typing import Dict, TextIO, List, Union
import re
from .utility import log_factory
from .castep_res import get_block, DEVEL_CODE_BLOCK_RE, DEVEL_CODE_VAL_RE


def _parse_devel_code_block(in_block: str) -> Dict[str, str]:
    """ Parse devel_code block to dict """

    matches = re.finditer(DEVEL_CODE_BLOCK_RE, in_block, re.IGNORECASE | re.MULTILINE)

    devel_code_parsed = {}

    # Get groups
    for blk in matches:
        block_title = blk.group(1)
        block = {}
        for par in re.finditer(DEVEL_CODE_VAL_RE, blk.group(0),
                               re.IGNORECASE | re.MULTILINE):

            key, val = re.split('[:=]', par.group(0))
            block[key] = val

        devel_code_parsed[block_title] = block

        # Remove matched to get remainder
        in_block = in_block.replace(blk.group(0), '')

    # Catch remainder
    for par in re.finditer(DEVEL_CODE_VAL_RE, in_block):
        key, val = re.split('[:=]', par.group(0))
        devel_code_parsed[key] = val

    return devel_code_parsed


def parse_cell_param_file(cell_param_file: TextIO) -> List[Dict[str, Union[str, Dict[str, str]]]]:
    """ Parse .cell/.param files into dict ready to JSONise """

    logger = log_factory(cell_param_file)
    curr = {}

    for line in cell_param_file:
        # Strip comments
        line = re.split('[#!]', line)[0]

        if block := get_block(line, cell_param_file,
                              re.compile('^%block ', re.IGNORECASE),
                              re.compile('^%endblock', re.IGNORECASE),
                              out_fmt=str):

            block_title = block.splitlines()[0].split()[1].lower()

            logger("Found block %s", block_title)

            if block_title == 'devel_code':
                curr['devel_code'] = _parse_devel_code_block(block)
            else:
                block = block.splitlines()
                curr[block_title] = [*map(lambda x: x.strip().split(), block[1:-1])]
        elif line := line.strip():

            key, val = re.split(r'\s*[ :=]+\s*', line, maxsplit=1)

            key = key.lower()
            logger("Found param %s", key)

            curr[key] = val
    return [curr]


parse_cell_file = parse_cell_param_file
parse_param_file = parse_cell_param_file
