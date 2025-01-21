"""Parse castep .cell and .param files."""
from __future__ import annotations

import re
import typing
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from functools import partial
from typing import Any, Dict, List, Literal, TextIO, Tuple, TypedDict, Union

import castep_outputs.utilities.castep_res as REs

from ..utilities.datatypes import (
    AtomIndex,
    MaybeSequence,
    ThreeByThreeMatrix,
    ThreeVector,
)
from ..utilities.filewrapper import Block
from ..utilities.utility import (
    atreg_to_index,
    determine_type,
    log_factory,
    normalise_key,
    strip_comments,
    to_type,
)


class PositionsInfo(TypedDict, total=False):
    """Information from positions block."""

    #: Units.
    units: str
    #: Atomic position.
    pos: ThreeVector
    #: Ion spin.
    spin: float
    #: Mixture index.
    mix_index: int
    #: Mixture weight.
    weight: float

class NonLinearConstraint(TypedDict):
    """Non-linear constraint information."""

    #: Type of non-linear constraint.
    key: Literal["distance", "bend", "torsion"]
    #: Atoms and constraint definition.
    atoms: dict[AtomIndex, ThreeVector]

DevelElem = MaybeSequence[Union[str, float, Dict[str, Union[str, float]]]]
DevelBlock = Dict[str, Union[DevelElem, Dict[str, DevelElem]]]
HubbardU = Dict[Union[str, AtomIndex], Union[str, Dict[str, float]]]
CellParamData = Dict[str, Union[str, float, Tuple[float, str],
                                Dict[str, Any], HubbardU, DevelBlock]]
GeneralBlock = Dict[str, Union[
    List[Union[str, float]],
    Dict[str, MaybeSequence[float]],
]]


def _get_block_units(block: Block, default: str) -> str:
    """Get units from a block.

    Consume the units line if present else rewind.

    Parameters
    ----------
    block
        Block to search for units.
    default
        Unit to use if not present.

    Returns
    -------
    str
        Units.
    """
    test = next(block)
    if match := re.match(r"^\s*(\S+)\s*$", test):
        units = match[1]
    else:
        block.rewind()
        units = default

    return units


def parse_cell_param_file(cell_param_file: TextIO) -> list[CellParamData]:
    """
    Parse castep .cell and param files.

    Parameters
    ----------
    cell_param_file
        Open handle to file to parse.

    Returns
    -------
    list[dict[str, str | dict[str, str]]]
        Parsed info.
    """
    logger = log_factory(cell_param_file)
    curr: CellParamData = {}

    for line in cell_param_file:
        # Strip comments
        line = re.split("[#!]", line)[0]

        if block := Block.from_re(line, cell_param_file,
                                  re.compile(r"^\s*%block ", re.IGNORECASE),
                                  re.compile(r"^\s*%endblock", re.IGNORECASE)):

            block_title = next(block).split()[1].lower()

            block = strip_comments(block, remove_inline=True)
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


def _parse_devel_code_block(in_block: Block) -> DevelBlock:
    """
    Parse devel_code block to dict.

    Parameters
    ----------
    in_block
        Input block to parse.

    Returns
    -------
    dict[str, str | float]
        Parsed info.
    """
    main_block = " ".join(map(str.strip, in_block))

    matches = re.finditer(REs.DEVEL_CODE_BLOCK_GENERIC_RE, main_block, re.IGNORECASE | re.MULTILINE)
    devel_code_parsed: DevelBlock = {}
    par: re.Match[str] | str

    # Get groups
    for blk in matches:
        block_title = normalise_key(blk.group(1))
        block_str = blk.group(0).split(":")[1]
        block: DevelBlock = {}
        for par in re.finditer(REs.DEVEL_CODE_VAL_RE, block_str,
                               re.IGNORECASE | re.MULTILINE):
            key, val = re.split("[:=]", par.group(0))
            key = normalise_key(key)
            typ = determine_type(val)
            block[key] = to_type(val, typ)
            block_str = block_str.replace(par.group(0), "")


        if block_str.strip():
            block["data"] = []
            for par in block_str.split():
                assert isinstance(block["data"], list)
                block["data"].append(to_type(par, determine_type(par)))

        if block_title in devel_code_parsed:
            devel_code_parsed[block_title].update(block) # type: ignore
        else:
            devel_code_parsed[block_title] = block # type: ignore

        # Remove matched to get remainder
        main_block = main_block.replace(blk.group(0), "")

    # Catch remainder
    for par in re.finditer(REs.DEVEL_CODE_VAL_RE, main_block):
        key, val = re.split("[:=]", par.group(0))
        key = normalise_key(key)
        typ = determine_type(val)

        if key in devel_code_parsed:  # Var has same name as block
            key = f"_{key}"

        devel_code_parsed[key] = to_type(val, typ)

    return devel_code_parsed


def _parse_ionic_constraints(block: Block) -> dict[AtomIndex, Sequence[ThreeVector]]:
    """
    Parse ionic constraints to dict.

    Parameters
    ----------
    block
        Input block to parse.

    Returns
    -------
    dict[AtomIndex, ThreeVector]
        Parsed info.
    """
    accum = defaultdict(list)

    for line in block:
        if match := REs.IONIC_CONSTRAINTS_RE.match(line):
            ind = atreg_to_index(match)
            elem: ThreeVector = to_type(match["val"].split(), float)
            accum[ind].append(elem)

    return dict(accum)

def _parse_nonlinear_constraints(block: Block) -> list[NonLinearConstraint]:
    """
    Parse nonlinear constraints to dict.

    Parameters
    ----------
    block
        Input block to parse.

    Returns
    -------
    dict[AtomIndex, ThreeVector]
        Parsed info.
    """
    accum = []

    for line in block:
        if re.match(r"^\s*%endblock", line, re.IGNORECASE):
            continue

        key, line = line.split(maxsplit=1)
        cons: NonLinearConstraint = {
            "key": key,
            "atoms": {atreg_to_index(match): to_type(match.group("x", "y", "z"), int)
                      for match in REs.ATOMIC_DATA_3VEC.finditer(line)},
        }
        accum.append(cons)

    return accum


def _parse_positions(block: Block, *, absolute: bool = False) -> dict[AtomIndex, PositionsInfo]:
    """
    Parse positions to dict.

    Parameters
    ----------
    block
        Input block to parse.

    Returns
    -------
    dict[AtomIndex, ThreeVector]
        Parsed info.
    """
    accum = {}
    count: Counter = Counter()

    if absolute:
        units = _get_block_units(block, "Ang")

    for line in block:
        if match := REs.POSITIONS_LINE_RE.match(line):
            spec: str = match["spec"]
            count[spec] += 1
            ind = (spec, count[spec])
            pos = to_type(match["pos"].split(), float)

            info: PositionsInfo = {"pos": pos}
            if absolute:
                info["units"] = units

            if match := REs.POSITIONS_SPIN_RE.search(line):
                info["spin"] = to_type(match["spin"], float)

            if match := REs.POSITIONS_MIXTURE_RE.search(line):
                info["mix_index"] = to_type(match["mix"], int)
                info["weight"] = to_type(match["ratio"], float)

            accum[ind] = info

    return accum

def _parse_hubbard_u(block: Block) -> HubbardU:
    """
    Parse Hubbard U block to dict.

    Parameters
    ----------
    block
        Input block to parse.

    Returns
    -------
    dict[str | AtomIndex, dict[str, float]]
        Parsed info.
    """
    accum: HubbardU = {"units": _get_block_units(block, "eV")}

    for line in block:
        if re.match(r"^\s*%endblock", line, re.IGNORECASE):
            continue

        if match := re.match(rf"^\s*({REs.ATOM_NAME_RE})\s*(\d+)?", line):
            spec = (match[1], int(match[2])) if match.lastindex == 2 else match[1]
            line = line.replace(match[0], "")
            accum[spec] = {key: to_type(val, determine_type(val))
                           for key, val in REs.COLON_SEP_RE.findall(line)}

    return accum


def _parse_sedc(block: Block) -> dict[str, dict[str, float]]:
    """
    Parse Semi-empirical dispersion correction block to dict.

    Parameters
    ----------
    block
        Input block to parse.

    Returns
    -------
    dict[str, dict[str, float]]
        Parsed info.
    """
    accum = {}

    test = next(block)
    if len(units := test.split()) == 2:
        units = tuple(units)
    else:
        block.rewind()
        units = ("eV", "Ang")

    for line in block:
        if re.match(r"^\s*%endblock", line, re.IGNORECASE):
            continue

        spec, line = line.strip().split(maxsplit=1)
        accum[spec] = {key: to_type(val, determine_type(val))
                       for key, val in REs.COLON_SEP_RE.findall(line)}

    return accum


def _parse_symops(block: Block) -> list[dict[str, ThreeByThreeMatrix | ThreeVector]]:
    """
    Parse symmetry operations block to dict.

    Parameters
    ----------
    block
        Input block to parse.

    Returns
    -------
    list[dict[str, ThreeByThreeMatrix | ThreeVector]]
        Parsed info.
    """
    tmp = [to_type(numbers, float)
           for line in block
           if (numbers := REs.FLOAT_RAT_RE.findall(line))]

    return [{"r": tmp[i:i+3],  # type: ignore
             "t": tmp[i+3]}
            for i in range(0, len(tmp), 4)]

def _parse_general(block: Block) -> GeneralBlock:
    """
    Parse general block to dict.

    Parameters
    ----------
    block
        Input block to parse.

    Returns
    -------
    dict[str, str | float]
        Parsed info.
    """
    block_data: GeneralBlock = {"data": []}

    for line in block:
        line = re.split("[#!]", line)[0]

        if REs.SPEC_PROP_RE.match(line):
            if isinstance(block_data["data"], list):
                block_data["data"] = {}
                typing.cast(Dict[str, MaybeSequence[Union[float, str]]],
                            block_data["data"])

            spec, val = line.strip().split(maxsplit=1)
            val = to_type(val, determine_type(val))

            typing.cast(MaybeSequence[Union[float, str]], val)

            block_data["data"][spec] = val

        elif numbers := REs.FLOAT_RAT_RE.findall(line):
            assert isinstance(block_data["data"], list)
            block_data["data"].append(to_type(numbers, float))

        elif re.match(r"^\s*%endblock", line, re.IGNORECASE):
            pass

        else:
            block_data["units"] = line.strip()

    return block_data

_parse_positions_abs = partial(_parse_positions, absolute=True)
_parse_positions_frac = partial(_parse_positions, absolute=False)

#: Cell/Param subparsers.
_PARSERS: dict[str, Callable] = {"devel_code": _parse_devel_code_block,
            "ionic_constraints": _parse_ionic_constraints,
            "nonlinear_constraints": _parse_nonlinear_constraints,
            "positions_abs": _parse_positions_abs,
            "positions_frac": _parse_positions_frac,
            "positions_abs_intermediate": _parse_positions,
            "positions_frac_intermediate": _parse_positions,
            "positions_abs_product": _parse_positions,
            "positions_frac_product": _parse_positions,
            "sedc_custom_params": _parse_sedc,
            "hubbard_u": _parse_hubbard_u,
            "symmetry_ops": _parse_symops}
