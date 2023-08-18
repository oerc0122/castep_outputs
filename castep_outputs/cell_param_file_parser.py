"""
Parse castep .cell and .param files
"""
from typing import Dict, TextIO, List, Union, Tuple
from collections import defaultdict
import re

import castep_outputs.castep_res as REs
from .utility import (log_factory, to_type, determine_type, atreg_to_index)
from .castep_res import get_block
from .constants import AtomIndex, ThreeByThreeMatrix, ThreeVector


def parse_cell_param_file(cell_param_file: TextIO) -> List[Dict[str, Union[str, Dict[str, str]]]]:
    """ Parse .cell/.param files into dict ready to JSONise """

    logger = log_factory(cell_param_file)
    curr = {}

    for line in cell_param_file:
        # Strip comments
        line = re.split("[#!]", line)[0]

        if block := get_block(line, cell_param_file,
                              re.compile(r"^\s*%block ", re.IGNORECASE),
                              re.compile(r"^\s*%endblock", re.IGNORECASE)):

            block_title = next(block).split()[1].lower()

            logger("Found block %s", block_title)

            curr[block_title] = _PARSERS.get(block_title, _parse_general)(block)

        elif match := REs.PARAM_VALUE_RE.match(line):
            key, val, unit = match.group("key", "val", "unit")
            key = key.strip().lower()
            logger("Found param %s", key)

            if " " in val.strip():
                val = to_type(val.split(), determine_type(val))
            else:
                val = to_type(val, determine_type(val))
            if unit:
                unit = unit.strip()
                curr[key] = (val, unit)
            else:
                curr[key] = val

    return [curr]


parse_cell_file = parse_cell_param_file
parse_param_file = parse_cell_param_file


def _parse_devel_code_block(in_block: TextIO) -> Dict[str, Union[str, float, int]]:
    """ Parse devel_code block to dict """

    in_block = in_block.read()
    in_block = " ".join(in_block.splitlines())
    matches = re.finditer(REs.DEVEL_CODE_BLOCK_GENERIC_RE, in_block, re.IGNORECASE | re.MULTILINE)
    devel_code_parsed = {}

    # Get groups
    for blk in matches:
        block_title = blk.group(1)
        block_str = blk.group(0).split(":")[1]
        block = {}
        for par in re.finditer(REs.DEVEL_CODE_VAL_RE, block_str,
                               re.IGNORECASE | re.MULTILINE):

            key, val = re.split("[:=]", par.group(0))
            typ = determine_type(val)
            block[key] = to_type(val, typ)
            block_str = block_str.replace(par.group(0), "")

        if block_str.strip():
            block["data"] = []

        for par in block_str.split():
            block["data"].append(to_type(par, determine_type(par)))

        devel_code_parsed[block_title.lower()] = block

        # Remove matched to get remainder
        in_block = in_block.replace(blk.group(0), "")

    # Catch remainder
    for par in re.finditer(REs.DEVEL_CODE_VAL_RE, in_block):
        key, val = re.split("[:=]", par.group(0))
        typ = determine_type(val)
        devel_code_parsed[key] = to_type(val, typ)

    return devel_code_parsed


def _parse_ionic_constraints(block: TextIO) -> Dict[AtomIndex, Tuple[float, float, float]]:
    accum = defaultdict(list)

    for line in block:
        if match := REs.IONIC_CONSTRAINTS_RE.match(line):
            ind = atreg_to_index(match)

            accum[ind].append(to_type(match["val"].split(), float))

    return accum


def _parse_nonlinear_constraints(block: TextIO):
    accum = []

    for line in block:
        if re.match(r"^\s*%endblock", line, re.IGNORECASE):
            continue

        key, line = line.split(maxsplit=1)
        cons = {"key": key,
                "atoms": {atreg_to_index(match): to_type(match.group("x", "y", "z"), int)
                          for match in REs.ATDAT3VEC.finditer(line)}}
        accum.append(cons)

    return accum


def _parse_positions(block: TextIO) -> Dict[AtomIndex, Tuple[float, float, float]]:
    accum = {}
    cnt = defaultdict(lambda: 0)

    for line in block:
        if match := REs.POSITIONS_LINE_RE.match(line):
            spec = match["spec"]
            cnt[spec] += 1
            ind = (spec, cnt[spec])
            pos = to_type(match["pos"].split(), float)

            accum[ind] = {"pos": pos}

            if match := REs.POSITIONS_SPIN_RE.search(line):
                accum[ind]["spin"] = to_type(match["spin"], float)

            if match := REs.POSITIONS_MIXTURE_RE.search(line):
                accum[ind]["mixed"] = to_type(match["mix"], int)
                accum[ind]["ratio"] = to_type(match["ratio"], float)

    return accum


def _parse_hubbard_u(block: TextIO) -> Dict[Union[str, AtomIndex], Dict[str, float]]:
    accum = {}

    for line in block:
        if re.match(r"^\s*%endblock", line, re.IGNORECASE):
            continue

        if match := re.match(rf"^\s*({REs.ATOM_NAME_RE})\s*(\d+)?", line):
            spec = (match[1], int(match[2])) if match.lastindex == 2 else match[1]
            accum[spec] = {}

            line = line.replace(match[0], "")
            for key, val in re.findall(r"\b(?P<key>\S+)\s*:\s*(?P<val>\S+)\b", line):
                val = to_type(val, determine_type(val))
                accum[spec][key] = val
        else:
            accum["units"] = line.strip()

    return accum


def _parse_sedc(block: TextIO) -> Dict[str, Dict[str, float]]:
    accum = {}
    for line in block:
        if re.match(r"^\s*%endblock", line, re.IGNORECASE):
            continue

        spec, line = line.strip().split(maxsplit=1)
        accum[spec] = {}

        for key, val in re.findall(r"\b(?P<key>\S+)\s*:\s*(?P<val>\S+)\b", line):
            val = to_type(val, determine_type(val))
            accum[spec][key] = val

    return accum


def _parse_symops(block: TextIO) -> List[Dict[str, Union[ThreeByThreeMatrix, ThreeVector]]]:

    accum = []
    tmp = [to_type(numbers, float)
           for line in block
           if (numbers := REs.FLOAT_RAT_RE.findall(line))]

    accum = [{'r': tmp[i:i+3],
              't': tmp[i+3]}
             for i in range(0, len(tmp), 4)]

    return accum


def _parse_general(block: TextIO) -> Dict[str, Union[str, float]]:
    block_data = {"data": []}
    for line in block:
        line = re.split("[#!]", line)[0]

        if REs.SPEC_PROP_RE.match(line):
            if isinstance(block_data["data"], list):
                block_data["data"] = {}

            spec, val = line.strip().split(maxsplit=1)
            val = to_type(val, determine_type(val))

            block_data["data"][spec] = val

        elif numbers := REs.FLOAT_RAT_RE.findall(line):
            block_data["data"].append(to_type(numbers, float))

        elif re.match(r"^\s*%endblock", line, re.IGNORECASE):
            pass

        else:
            block_data["units"] = line.strip()

    return block_data


_PARSERS = {"devel_code": _parse_devel_code_block,
            "ionic_constraints": _parse_ionic_constraints,
            "nonlinear_constraints": _parse_nonlinear_constraints,
            "positions_abs": _parse_positions,
            "positions_frac": _parse_positions,
            "positions_abs_intermediate": _parse_positions,
            "positions_frac_intermediate": _parse_positions,
            "positions_abs_product": _parse_positions,
            "positions_frac_product": _parse_positions,
            "sedc_custom_params": _parse_sedc,
            "hubbard_u": _parse_hubbard_u,
            "symmetry_ops": _parse_symops}
