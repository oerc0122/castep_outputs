"""Parse a castep binary check file."""

from __future__ import annotations

import json
from contextlib import suppress
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any, BinaryIO, Generator, Iterator
from pprint import pprint

import numpy as np
from fortran_bin_parser import binary_file_reader, FortranBinaryReader
from castep_outputs.utilities.utility import to_type

PARAMETERS_FILE = Path(__file__).parent / "parameters_definition.json"
with PARAMETERS_FILE.open() as file:
    PARAMETERS_DEF = json.load(file)

be_int = np.dtype(np.int32).newbyteorder(">")
be_flo = np.dtype(np.float64).newbyteorder(">")


DTYPES: dict[str, Callable] = {
    "float": lambda x: np.frombuffer(x, dtype=be_flo),
    "bool": lambda x: bool(int.from_bytes(x, "big")),
    "int": lambda x: np.frombuffer(x, dtype=be_int),
    "str": lambda x: x.decode(encoding="utf-8").strip(),
}

# CHECKFILE_MAJOR_SECTIONS = (
#     "PARAMETERS_DUMP",
#     "UNIT_CELL",
#     "ELECTRONIC",
#     "WAVE",
#     "EIGENVALUESOCC",
#     "GROUND_STATE",
#     "DENSITY",
#     "E_FERMI",
#     "OEP",
#     "DE_DLOGE",
#     "FORCES",
#     "STRESS",
#     "MD",
#     "PIMD",
#     "MD_HUG",
#     "MD_NOSE",
#     "MD_NOSE_2",
#     "BFGS",
#     "LBFGS",
#     "TPSD",
#     "DAMPED_MD",
#     "FIRE",
#     "VAR_CELL",
#     "PHONON",
#     "PHON_GAMMA",
#     "SECONDD",
#     "FORCE_CON",
#     "FINE_FREQ",
#     "PHONON_ADP",
#     "PHONON_DOS",
#     "BORN_CHGS",
#     "PART_CHGS",
#     "DIELECTRIC",
#     "NLO_D_MATR",
#     "RAMAN_TENS",
#     "RAMAN_ATOM",
#     "SHIELDING",
#     "EFG",
#     "GTENSOR",
#     "HYPERFINE",
#     "JCOUP",
#     "JCOUP_FC",
#     "JCOUP_SPIN",
#     "JCOUP_ORB",
#     "GENETIC",
#     "HUBBARD",
#     "TDDFT_EIG",
#     "TDDFT_FOR",
#     "EPCOUPLING",
#     "TSS",
#     "SOLVATION",
#     "ELASTIC",
#     "ELASTIC_FI",
#     "INT_STRAIN",
#     "PIEZO",
#     "PIEZO_FI",
# )

def _get_block_name(data: bytes, *, end: bool) -> str:
    return DTYPES["str"](data).lower().strip().removeprefix("end_" if end else "begin_")


def _get_param_info(param_info):
    param_version = to_type(param_info["version"].split("."), int)
    dtype = DTYPES[param_info["dtype"]]
    return param_version, dtype


def parse_check_file(file: BinaryIO) -> Generator[tuple[str, Any], None, None]:
    """
    Parse a CASTEP .check file.

    Notes
    -----
    This routine is a lazy generator since these files can be very large.
    """
    parsed = binary_file_reader(file)
    data = {}

    next(parsed) # BEGIN_PARAMETERS_DUMP
    version = to_type(DTYPES["str"](next(parsed)).strip("0 ").split("."), int)
    data["parameters"] = parse_block(parsed, version, "parameters_dump")
    pprint(data["parameters"])

    for datum in parsed:
        block = _get_block_name(datum, end=False)
        print(f"{block=}")
        data[block] = _PARSERS.get(block, parse_block)(parsed, version, block)

    return data


def parse_unit_cell(file: FortranBinaryReader, version: tuple[int, int], block: str):
    if version < (2, 2):
        return parse_raw_data(file, version, "unit_cell_old")
    return parse_prefixed(file, version, block)


def parse_prefixed(file: FortranBinaryReader, version: tuple[int, int], block: str):
    definitions = PARAMETERS_DEF[block]
    out = {}

    for data in file:
        name = DTYPES["str"](data).lower()
        name = name.split("%")[1] if "%" in name else name
        if name == f"end_{block}":
            break

        param_version, dtype = _get_param_info(definitions[name])

        if param_version > version:  # Should never happen
            raise ValueError(f"Weird version mismatch. Data ({name}) written which should not exist.")

        raw = next(file)
        out[name] = dtype(raw)

    return out


def parse_raw_data(file: FortranBinaryReader, version: tuple[int, int], block: str):
    """Parser for un-labelled, un-blocked data structures."""
    definitions = PARAMETERS_DEF[block]
    out = {}

    for param, param_info in definitions.items():
        param_version, dtype = _get_param_info(param_info)

        if param_version > version:
            break

        data = next(file)
        val = dtype(data)
        out[param] = val

    return out


def parse_block(file: FortranBinaryReader, version: tuple[int, int], block: str):
    """"""
    definitions = PARAMETERS_DEF[block]
    stack = [block]
    out = defaultdict(dict)

    for datum in file:
        block_name = _get_block_name(datum, end=False)

        if block_name.removeprefix("end_") == stack[-1]:
            stack.pop()
            break

        stack.append(block_name)

        for param, param_info in definitions[block_name].items():
            param_version, dtype = _get_param_info(param_info)

            if param_version > version:
                break

            data = next(file)
            with suppress(UnicodeDecodeError):
                if _get_block_name(data, end=True) == stack[-1]:
                    file.send(True)
                    break

            val = dtype(data)
            out[block_name][param] = val

        end_block_name = _get_block_name(next(file), end=True)
        if end_block_name != stack.pop():
            raise ValueError(f"Mismatched block titles: {block_name} != {end_block_name}")

        if not stack:
            break

    return out


_PARSERS = {
    "unit_cell": parse_unit_cell,
    "cell_global": parse_prefixed,
}


if __name__ == "__main__":
    print(parse_check_file(Path("Si8-md-NVE.check").open("rb")))
