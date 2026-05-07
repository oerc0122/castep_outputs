"""Parse castep .cell and .param files."""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from functools import partial
from typing import TYPE_CHECKING, Any, Literal, TextIO, TypeAlias, TypedDict, cast

import castep_outputs.utilities.castep_res as REs
from castep_outputs.utilities.constants import SHELLS
from castep_outputs.utilities.datatypes import (
    AtomIndex,
    MaybeSequence,
    PSPotBFG,
    PSPotStrInfo,
    ThreeByThreeMatrix,
    ThreeVector,
)
from castep_outputs.utilities.filewrapper import Block
from castep_outputs.utilities.type_conv import determine_type, fix_data_types, to_type
from castep_outputs.utilities.utility import (
    atreg_to_index,
    file_or_path,
    log_factory,
    normalise_key,
    strip_comments,
    strip_nones,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


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


class XCDefParams(TypedDict, total=False):
    """XC definition params."""

    nlxc_screening_length: float
    nlxc_screening_function: str
    nlxc_ppd_int: bool
    nlxc_divergence_corr: bool


class XCDef(TypedDict):
    """Information from XC definitions block."""

    params: XCDefParams
    xc: dict[str, float]


DevelElem = MaybeSequence[str | float | dict[str, str | float]]
DevelBlock: TypeAlias = dict[str, DevelElem | dict[str, DevelElem]]
HubbardU: TypeAlias = dict[str | AtomIndex, str | dict[str, float]]
CellParamData: TypeAlias = dict[
    str,
    str | float | tuple[float, str] | dict[str, Any] | HubbardU | DevelBlock | XCDef,
]
GeneralBlock: TypeAlias = dict[
    str,
    list[str | float] | dict[str, MaybeSequence[float]],
]


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


@file_or_path(mode="r")
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
        line = re.split(r"[#!]", line)[0]

        if block := Block.from_re(
            line,
            cell_param_file,
            re.compile(r"^\s*%block ", re.IGNORECASE),
            re.compile(r"^\s*%endblock", re.IGNORECASE),
        ):
            block_title = next(block).split()[1].lower()

            block = strip_comments(block, remove_inline=True)
            logger("Found block %s", block_title)

            curr[block_title] = _PARSERS.get(block_title, _parse_general)(block)

        elif match := REs.PARAM_VALUE_RE.match(line):
            if match["str"] is not None:
                key, val = match.group("key", "str")
                curr[key.strip().lower()] = to_type(val.strip(), determine_type(val))

                logger("Found param %s", key)
                continue

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


def _parse_beta_function(string: str, *, debug: bool = False) -> PSPotBFG:
    """Parse a beta function group into its components.

    Parameters
    ----------
    string : str
        Input beta_function group.

    Returns
    -------
    PSPotBFG
        Parsed data.

    Raises
    ------
    ValueError
        If unable to parse.

    Examples
    --------
    >>> from pprint import pprint
    >>> pprint(_parse_beta_function("30U2.1U+1.1"))
    {'orbital': 3,
     'projectors': [{'beta_rc': 2.1, 'type': 'U'}, {'beta_e': 1.1, 'type': 'U'}],
     'shell': 's',
     'shell_ind': 0}
    >>> pprint(_parse_beta_function("31UU"))
    {'orbital': 3,
     'projectors': [{'type': 'U'}, {'type': 'U'}],
     'shell': 'p',
     'shell_ind': 1}
    >>> _parse_beta_function("32")
    {'orbital': 3, 'shell': 'd', 'shell_ind': 2, 'projectors': []}
    """
    logging.debug("Full beta_Function: %s", string)

    projectors = []

    # Parse from proj_type (NUHLGP) -> next one (exclusive)
    for projector in re.findall(f"[{REs.PROJ_TYPES}][^{REs.PROJ_TYPES}]*", string[2:]):
        logging.debug("Projector: %s", projector)

        if not (match := REs.PSPOT_PROJ_RE.match(projector)):
            logging.error("Failed parsing %s", projector)
            raise ValueError(f"Attempt to parse {string!r} as PSPot failed.")

        proj_data = match.groupdict()

        logging.debug("Components: %s", proj_data)
        if not debug:
            strip_nones(proj_data, include=("beta_delta", "beta_e", "beta_rc"))

        fix_data_types(proj_data, {"beta_delta": float, "beta_e": float, "beta_rc": float})
        projectors.append(proj_data)

    return {
        "orbital": int(string[0]),
        "shell": SHELLS[int(string[1])],
        "shell_ind": int(string[1]),
        "projectors": projectors,
    }


def _parse_pspot_string(string: str, *, debug: bool = False) -> PSPotStrInfo:
    """Parse PSPot strings to their components.

    Parameters
    ----------
    string : str
        String to be parsed.
    debug : bool
        Whether to maintain ``None`` s in unmatched output.

    Returns
    -------
    PSPotStrInfo
        Processed information.

    Raises
    ------
    ValueError
        Unable to parse string as PSPot.
    """
    logging.debug("%s", string)

    pspot: dict[str, Any] = {
        "print": "[" in string,
        "poly_fit": "-" in string[: string.find("|")],
        "beta_functions": [],
        "string": string,
    }

    # Remove polyfit `-` from string
    string = re.sub(r"^([^|]*)-([^|]*)\|", r"\g<1>\g<2>|", string, count=1)

    for label, mark, regex in (
        ("adjustment", "{", REs.PSPOT_ADJ_RE),
        ("testing", "[", REs.PSPOT_TEST_RE),
        ("flags", "(", REs.PSPOT_FLAG_RE),
    ):
        if mark in string:
            logging.debug("Found %s", label)
            if not (match := regex.search(string)):
                logging.error("Failed parsing %s.", label)
                raise ValueError(f"Attempt to parse {string!r} as PSPot failed.")

            pspot[label] = match[1].split(",")
            string = string[: match.start()] + string[match.end() :]
        else:
            pspot[label] = None

    if not (match := REs.PSPOT_INFO_RE.match(string)):
        logging.error("Failed parsing pspot definition string.")
        raise ValueError(f"Attempt to parse {string!r} as PSPot failed.")

    logging.debug("Main: %s", match.groupdict())

    pspot.update(match.groupdict())
    string = string[: match.start()] + string[match.end() :]
    pspot["beta_function_string"] = string
    pspot["beta_functions"] = [
        _parse_beta_function(beta_function_group, debug=debug)
        for beta_function_group in string.split(":")
    ]

    if not debug:
        strip_nones(
            pspot,
            include=("local_energy", "beta_radius", "r_inner", "adjustment", "testing", "flags"),
        )

    fix_data_types(
        pspot,
        {
            "beta_radius": float,
            "coarse": float,
            "core_radius": float,
            "fine": float,
            "local_channel": float,
            "local_energy": float,
            "medium": float,
            "r_inner": float,
        },
    )
    return cast("PSPotStrInfo", pspot)


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
    main_block = re.sub(r"%endblock\s+devel_code", "", main_block, flags=re.IGNORECASE)

    matches = re.finditer(REs.DEVEL_CODE_BLOCK_GENERIC_RE, main_block, re.IGNORECASE | re.MULTILINE)
    devel_code_parsed: DevelBlock = {}
    par: re.Match[str] | str

    # Get groups
    for blk in matches:
        block_title = normalise_key(blk.group(1))
        block_str = blk.group(0).split(":")[1]
        block: DevelBlock = {}
        for par in re.finditer(REs.DEVEL_CODE_VAL_RE, block_str, re.IGNORECASE | re.MULTILINE):
            key, val = re.split(r"[:=]", par.group(0))
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
            devel_code_parsed[block_title].update(block)
        else:
            devel_code_parsed[block_title] = block

        # Remove matched to get remainder
        main_block = main_block.replace(blk.group(0), "")

    # Catch remainder
    for par in re.finditer(REs.DEVEL_CODE_VAL_RE, main_block):
        key, val = re.split(r"[:=]", par.group(0))
        key = normalise_key(key)
        typ = determine_type(val)

        if key in devel_code_parsed:  # Var has same name as block
            key = f"_{key}"

        devel_code_parsed[key] = to_type(val, typ)

    # Catch present components
    present_code_re = re.compile(r"""
        (?<![:=])        # Does not follow : or =
        \b[A-Za-z_-]+\b  # One "word"
        (?![:=])         # Not followed by : or =
    """, re.VERBOSE)

    for par in re.finditer(present_code_re, main_block):
        key = normalise_key(par.group(0))

        if key in devel_code_parsed:  # Var has same name as block
            key = f"_{key}"

        devel_code_parsed[key] = None

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
            "atoms": {
                atreg_to_index(match): to_type(match.group("x", "y", "z"), int)
                for match in REs.ATOMIC_DATA_3VEC.finditer(line)
            },
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
            accum[spec] = {
                key: to_type(val, determine_type(val))
                for key, val in REs.COLON_SEP_RE.findall(line)
            }

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

    accum["units"] = {
        "energy": units[0],
        "distance": units[1],
    }

    for line in block:
        if re.match(r"^\s*%endblock", line, re.IGNORECASE):
            continue

        spec, line = line.strip().split(maxsplit=1)
        accum[spec] = {
            key: to_type(val, determine_type(val)) for key, val in REs.COLON_SEP_RE.findall(line)
        }

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
    tmp = [to_type(numbers, float) for line in block if (numbers := REs.FLOAT_RAT_RE.findall(line))]

    return [
        {
            "r": tmp[i : i + 3],
            "t": tmp[i + 3],
        }
        for i in range(0, len(tmp), 4)
    ]


def _parse_xc_definition(block: Block) -> dict[str, float]:
    """
    Parse xc_definition block to dict.

    Parameters
    ----------
    block
        Input block to parse.

    Returns
    -------
    dict[str, float]
        Parsed info.
    """
    block_data = {"xc": {}, "params": {}}
    block.remove_bounds(fore=0, back=1)

    for line in strip_comments(block):
        key, val = line.split(maxsplit=1)
        key = normalise_key(key)

        if key == "nlxc_screening_length":
            block_data["params"][key] = float(val)
        elif key == "nlxc_screening_function":
            block_data["params"][key] = val
        elif key in {"nlxc_ppd_int", "nlxc_divergence_corr"}:
            block_data["params"][key] = val.upper() == "ON"
        else:
            block_data["xc"][key] = float(val)

    return block_data


def _parse_species_pot(block: Block) -> dict[str, str | PSPotStrInfo]:
    """Parse species pot block.

    Parameters
    ----------
    block : Block
        Input block to parse.

    Returns
    -------
    dict[str, str | PSPotStrInfo]
        Processed block if PSPot string, otherwise bare string.
    """
    block_data = {}
    block.remove_bounds(fore=0, back=1)

    for line in block:
        match line.split(maxsplit=1):
            case [spec]:
                block_data[None] = spec
            case [spec, pot]:
                if REs.PSPOT_FULL_LAZY.search(pot):  # We have pspot definition
                    pot = _parse_pspot_string(pot)
                block_data[spec] = pot

    return block_data


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
        line = re.split(r"[#!]", line)[0]

        if REs.SPEC_PROP_RE.match(line):
            if isinstance(block_data["data"], list):
                block_data["data"] = cast("dict[str, MaybeSequence[float | str]]", {})

            spec, val = line.strip().split(maxsplit=1)
            val = to_type(val, determine_type(val))

            val = cast(MaybeSequence[float | str], val)

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
_PARSERS: dict[str, Callable] = {
    "devel_code": _parse_devel_code_block,
    "ionic_constraints": _parse_ionic_constraints,
    "nonlinear_constraints": _parse_nonlinear_constraints,
    "positions_frac": _parse_positions_frac,
    "positions_frac_intermediate": _parse_positions,
    "positions_frac_product": _parse_positions,
    "positions_abs": _parse_positions_abs,
    "positions_abs_intermediate": _parse_positions,
    "positions_abs_product": _parse_positions,
    "positions_aspectral_intermediate": _parse_positions,
    "positions_aspectral_product": _parse_positions,
    "species_pot": _parse_species_pot,
    "sedc_custom_params": _parse_sedc,
    "hubbard_u": _parse_hubbard_u,
    "symmetry_ops": _parse_symops,
    "xc_definition": _parse_xc_definition,
}
