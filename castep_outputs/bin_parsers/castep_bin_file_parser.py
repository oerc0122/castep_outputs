"""Parser for cst_esp files."""

from __future__ import annotations

from typing import BinaryIO, TypedDict

from ..utilities.utility import file_or_path
from .fortran_bin_parser import FortranBinaryReader
from ._bin_params import parse_parameters_dump
from ._bin_cell import parse_cell_dump, parse_cell_global


def parse_wvfn(reader: FortranBinaryReader, version: tuple[int, int]):

    accum = {}
    accum["type"] = reader.get(str).strip()

    match accum["type"]:
        case "Gpt" | "wave" | "G-sl" | "sl":
            accum["ng"] = reader.get(int)
            if version < (7, 0):
                _ncoeffs, nbands, nkpts, nspins = reader.get(int)
                nspinorcomps = 1
            else:
                _ncoeffs, nspinorcomps, nbands, nkpts, nspins = reader.get(int)

            dkc = accum["data_kpoint_coords"] = {}
            pw = accum["total_pw"] = {}
            pw_coord = accum["pw_grid_coord"] = {}
            coeffs = accum["coeffs"] = {}

            for ns in range(nspins):
                for nk in range(nkpts):
                    dkc[ns, nk], pw[ns, nk] = reader.get(int)
                    pw_coord[ns, nk] = [reader.get(int) for _ in range(3)]
                    coeffs[ns, nk] = [
                        [reader.get(complex) for _ in range(nbands)]
                        for _ in range(nspinorcomps)
                    ]

                for node in range(nkpt_on_node):
                    ...

        case "bks":
            ...


@file_or_path(mode="rb")
def parse_check_castep_bin_file(castep_bin_file: BinaryIO) -> dict:
    reader = FortranBinaryReader(castep_bin_file)

    castep_bin = reader.get(str) == "CASTEP_BIN"

    accum = parse_parameters_dump(reader)
    accum["castep_bin"] = castep_bin

    accum["cell"] = parse_cell_dump(reader)
    accum["cell_global"] = parse_cell_global(reader)

    accum["orig_cell"] = parse_cell_dump(reader)
    accum["orig_cell_global"] = parse_cell_global(reader)

    tmp = reader.get_dtype_dict(
        {
            "found_ground_state_wvfn": bool,
            "found_ground_state_den": bool,
            "total_energy": float,
            "fermi_energy": float,
        }
    )
    accum["n_bands"], accum["n_spins"] = reader.get(int)

    if not castep_bin:
        parse_wavefn()

    parse_occ()

    _found_ground_state_den = reader.get(bool)
    accum["ng_fine"] = reader.get(int)

    parse_density()

    from pprint import pprint

    pprint(tmp)

    return accum
