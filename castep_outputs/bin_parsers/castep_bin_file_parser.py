"""Parser for cst_esp files."""

from __future__ import annotations

from typing import Any, BinaryIO

from castep_outputs.bin_parsers.checkpoint.optional import (
    parse_density,
    parse_occ,
    parse_optional,
    parse_wave,
)

from ..utilities.utility import file_or_path
from .checkpoint.cell import parse_cell_dump, parse_cell_global
from .checkpoint.params import parse_parameters_dump
from .fortran_bin_parser import FortranBinaryReader


@file_or_path(mode="rb")
def parse_check_castep_bin_file(castep_bin_file: BinaryIO) -> dict[str, Any]:
    """Parse check/castep_bin files.

    Parameters
    ----------
    castep_bin_file
        File to parse.

    Returns
    -------
    :
        Parsed file.
    """
    reader = FortranBinaryReader(castep_bin_file)

    castep_bin = reader.get(str) == "CASTEP_BIN"

    accum = parse_parameters_dump(reader)
    accum["castep_bin"] = castep_bin

    accum["cell"] = parse_cell_dump(reader)
    accum["cell_global"] = parse_cell_global(reader)

    accum["orig_cell"] = parse_cell_dump(reader)
    accum["orig_cell_global"] = parse_cell_global(reader)

    accum.update(
        reader.get_dtype_dict(
            {
                "found_ground_state_wvfn": bool,
                "found_ground_state_den": bool,
                "total_energy": float,
                "fermi_energy": float,
            },
        ),
    )
    accum["n_bands"], accum["n_spins"] = reader.get((int, ...))

    if not castep_bin:
        accum["wavefn"] = parse_wave(reader, accum["version"])

    accum["occupancies"], accum["eigenvalues"] = parse_occ(
        reader,
        accum["cell_global"]["nkpts"],
        accum["n_spins"],
    )

    _found_ground_state_den = reader.get(bool)
    accum["ng_fine"] = reader.get((int, ...))

    accum["den_charge"], accum["den_spin"] = parse_density(
        reader,
        accum["ng_fine"],
        accum["n_spins"],
    )

    accum["optional"] = parse_optional(reader, accum)

    return accum


parse_check_file = parse_check_castep_bin_file
parse_castep_bin_file = parse_check_castep_bin_file
