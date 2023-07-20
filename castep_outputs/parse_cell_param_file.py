"""
Parse castep .cell and .param files
"""

import re
from .utility import get_block


def _parse_devel_code_block(in_block):
    """ Parse devel_code block to dict """

    val_re = '[A-Za-z0-9_]+[:=]\S+'
    block_re = f'([A-Za-z0-9_]+):(?:\s*{val_re}\s*)*:end\S+'

    matches = re.finditer(block_re, in_block, re.IGNORECASE | re.MULTILINE)

    devel_code_parsed = {}

    # Get groups
    for blk in matches:
        block_title = blk.group(1)
        block = {}
        for par in re.finditer(val_re, blk.group(0), re.IGNORECASE | re.MULTILINE):

            key, val = re.split('[:=]', par.group(0))
            block[key] = val

        devel_code_parsed[block_title] = block

        # Remove matched to get remainder
        in_block = in_block.replace(blk.group(0), '')

    # Catch remainder
    for par in re.finditer(val_re, in_block):
        key, val = re.split('[:=]', par.group(0))
        devel_code_parsed[key] = val

    return devel_code_parsed


def parse_cell_param_file(cell_param_file, verbose=False):
    """ Parse .cell/.param files into dict ready to JSONise """

    curr = {}

    for line in cell_param_file:
        # Strip comments
        line = re.split('[#!]', line)[0]

        if block := get_block(line, cell_param_file,
                              re.compile('^%block ', re.IGNORECASE),
                              re.compile('^%endblock', re.IGNORECASE)):

            block_title = block.splitlines()[0].split()[1].lower()

            if verbose:
                print(f"Found block {block_title}")

            if block_title == 'devel_code':
                curr['devel_code'] = _parse_devel_code_block(block)
            else:
                block = block.splitlines()
                curr[block_title] = [*map(lambda x: x.strip().split(), block[1:-1])]
        elif line := line.strip():

            key, val = re.split('\s*[ :=]+\s*', line, maxsplit=1)

            key = key.lower()
            if verbose:
                print(f"Found param {key}")

            curr[key] = val
    return [curr]
