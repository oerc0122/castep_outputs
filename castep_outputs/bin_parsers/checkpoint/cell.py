"""Parse parameters dump from check/castep_bin."""

from __future__ import annotations

import struct
from typing import Any, BinaryIO

from castep_outputs.utilities.type_conv import TypeTupleMapping
from castep_outputs.utilities.utility import file_or_path

from ..fortran_bin_parser import FortranBinaryReader
from .utility import parse_headered_dump


def _kpt_grp(name: str) -> TypeTupleMapping:
    return {
        f"NUM_{name}_KPOINTS": int,
        f"{name}_KPOINTS": (float, ...),
        f"{name}_KPOINT_WEIGHTS": (float, ...),
    }


def _kpt_gos(name: str) -> TypeTupleMapping:
    return {
        f"{name}_KPOINT_MP_GRID": (int, ...),
        f"{name}_KPOINT_MP_OFFSET": (float, ...),
        f"{name}_KPOINT_MP_SPACING": (float, ...),
    }


NEW_CELL_DUMP: TypeTupleMapping = {
    "REAL_LATTICE": (float, ...),
    "RECIP_LATTICE": (float, ...),
    "VOLUME": float,
    "NUM_SPECIES": int,
    "NUM_IONS": int,
    "MAX_IONS_IN_SPECIES": int,
    "CELL_VERSION_NUMBER": float,
    "NUM_IONS_IN_SPECIES": (int, ...),
    "IONIC_POSITIONS": (float, ...),
    "IONIC_VELOCITIES": (float, ...),
    "IONIC_CHARGE": (int, ...),
    "IONIC_CHARGE_REAL": (float, ...),
    "ATOM_MOVE": (bool, ...),
    "SPECIES_MASS": (float, ...),
    "SPECIES_SYMBOL": (str, ...),
    "SPECIES_POT": (str, ...),
    "SPECIES_LCAO_STATES": (int, ...),
    "ION_PACK_SPECIES": (int, ...),
    "ION_PACK_INDEX": (int, ...),
    "IONIC_LABEL": (str, ...),
    "INITIAL_MAGNETIC_MOMENT": (float, ...),
    "ATOM_FIX_SPIN": (bool, ...),
    "INITIAL_MAGNETISATION_DIR": (float, ...),
    "INITIAL_NC_DENSITY": (bool, ...),
    "NUM_CELLS_IN_SUPERCELL": (int, ...),
    "SUPERCELL_MATRIX": (int, ...),
    "SUPERCELL_CELL_INDEX": (int, ...),
    "SUPERCELL_ION_INDEX": (int, ...),
    "SUPERCELL_ORIGINS": (int, ...),
    "NUM_MIXTURE_ATOMS": (int, ...),
    "MIXTURE_WEIGHT": (float, ...),
    "LIST_MIXTURE_ATOMS_SIZE": (int, ...),
    "LIST_MIXTURE_ATOMS": (int, ...),
    "ATOM_INIT_MAGMOM": (bool, ...),
    "ATOM_INIT_SPIN": (bool, ...),
    "INDX_MIXTURE_ATOMS": (int, ...),
    "SPECIES_SPIN_ISOTOPE": (int, ...),
    "SPECIES_GAMMA": (float, ...),
    "SPECIES_EFG_ISOTOPE": (int, ...),
    "SPECIES_Q": (float, ...),
    "HUBBARD_U": (float, ...),
    "HUBBARD_ALPHA": (float, ...),
    "CHEMICAL_POTENTIAL": (float, ...),
    "SEDC_CUSTOM_PARAMS_LEN": int,
    "SEDC_CUSTOM_PARAMS": (str, ...),
}


OLD_CELL_DUMP: TypeTupleMapping = {
    "real_lattice": float,
    "recip_lattice": float,
    "volume": float,
    "num_species": int,
    "num_ions": int,
    "max_ions_in_species": int,
    "num_ions_in_species": int,
    "ionic_positions": float,
    "ionic_velocities": float,
    "ionic_charge": float,
    "atom_move": bool,
    "species_mass": float,
    "species_symbol": str,
    "species_pot": str,
    "species_lcao_states": int,
}

NEW_CELL_GLOBAL: TypeTupleMapping = {
    "NKPTS": int,
    "KPOINTS": (float, ...),
    "KPOINT_WEIGHTS": (float, ...),
    "NUM_SYMMETRY_OPERATIONS": int,
    "SYMMETRY_OPERATIONS": (float, ...),
    "SYMMETRY_DISPS": (float, ...),
    "SYMMETRY_EQUIV_ATOMS": (int, ...),
    "SPACEGROUP": bytes,
    "NUM_CRYSTAL_SYMMETRY_OPERATIONS": int,
    "CRYSTAL_SYMMETRY_OPERATIONS": (float, ...),
    "CRYSTAL_SYMMETRY_DISPS": (float, ...),
    "CRYSTAL_SYMMETRY_EQUIV_ATOMS": (int, ...),
    "CRYSTAL_SPACEGROUP": bytes,
    "CELL_SYMMETRY_ION_CONSTRAINTS": (int, ...),
    "NUM_IONIC_CONSTRAINTS": int,
    "IONIC_CONSTRAINTS": (float, ...),
    "NUM_CELL_CONSTRAINTS": int,
    "CELL_CONSTRAINTS": (int, ...),
    "EXTERNAL_PRESSURE": (float, ...),
    "EXTERNAL_EFIELD": (float, ...),
    "EXTERNAL_BFIELD": (float, ...),
    "INPUT_PERMITTIVITY": (float, ...),
    **_kpt_grp("BS"),
    **_kpt_grp("SPECTRAL"),
    "NUM_PHONON_KPOINTS": int,
    "PHONON_KPOINTS": (float, ...),
    "NUM_PHONON_GAMMA_DIRECTIONS": int,
    "PHONON_GAMMA_DIRECTIONS": (float, ...),
    "PHONON_KPOINT_WEIGHTS": (float, ...),
    **_kpt_grp("PHONON_FINE"),
    **_kpt_grp("SCF"),
    **_kpt_grp("MAGRES"),
    **_kpt_grp("ELNES"),
    "NUM_EP_KPOINT_PAIRS": int,
    "EP_KPOINT_PAIRS": (float, ...),
    "CELL_SYMMORPHIC": bool,
    "KPOINT_MP_GRID": (int, ...),
    "KPOINT_MP_OFFSET": (float, ...),
    "KPOINT_MP_DENSITY": float,
    "KPOINT_MP_SPACING": (float, ...),
    "FIX_COM": bool,
    "FIX_ALL_IONS": bool,
    "FIX_ALL_CELL": bool,
    "FIX_VOL": bool,
    "SYMMETRY_GENERATE": bool,
    "SYMMETRY_TOL": float,
    **_kpt_grp("OPTICS"),
    **_kpt_gos("OPTICS"),
    "OPTICS_KPOINT_MP_DENSITY": float,
    "QUANTISATION_AXIS": (float, ...),
    "PHONON_SUPERCELL_MATRIX": (int, ...),
    **_kpt_grp("SUPERCELL"),
    "JCOUPLING_SPECIES": int,
    "JCOUPLING_SITE": int,
    **_kpt_gos("SCF"),
    **_kpt_gos("BS"),
    **_kpt_gos("SPECTRAL"),
    **_kpt_gos("PHONON"),
    **_kpt_gos("PHONON_FINE"),
    **_kpt_gos("MAGRES"),
    **_kpt_gos("ELNES"),
    **_kpt_gos("SUPERCELL"),
    "NUM_NONLINEAR_CONSTRAINTS": int,
    "NONLINEAR_CONSTRAINTS": (float, ...),
    "NQPTS": int,
    "QPOINTS": (float, ...),
    "QPOINT_WEIGHTS": (float, ...),
    "QPOINT_CONJG": bool,
    "NQ_TO_SCF_GLOBAL_NK": int,
    "Q_FROM_SCF_K_SYM_OP": int,
    "DENSITY": float,
    "DEVEL_CODE": str,
}

OLD_CELL_GLOBAL: TypeTupleMapping = {
    "num_cell_constraints": int,
    "cell_constraints": int,
    "external_pressure": float,
    "num_bs_kpoints": int,
    "bs_kpoints": float,
    "bs_kpoint_weights": float,
    "num_phonon_kpoints": int,
    "phonon_kpoints": float,
    # num_phonon_gamma_directions
    # phonon_gamma_directions
    # phonon_kpoint_weights
    "cell_symmorphic": bool,
    "kpoint_mp_grid": int,
    "kpoint_mp_offset": float,
    "kpoint_mp_density": float,
    "fix_com": bool,
    "fix_all_ions": bool,
    "fix_all_cell": bool,
    "symmetry_generate": bool,
    "symmetry_tol": float,
    "num_optics_kpoints": int,
    "optics_kpoints": float,
    "optics_kpoint_weights": float,
    "optics_kpoint_mp_grid": int,
    "optics_kpoint_mp_offset": float,
    "optics_kpoint_mp_density": float,
}


def _parse_spacegroup(spc: bytes) -> dict[str, int | str]:
    return {
        key: val.decode("utf-8").strip() if isinstance(val, bytes) else val
        for key, val in zip(
            (
                "number",
                "international_short",
                "international_full",
                "international",
                "schoenflies",
                "hall_number",
                "hall_symbol",
                "choice",
                "pointgroup_international",
                "pointgroup_schoenflies",
                "arithmetic_crystal_class_number",
                "arithmetic_crystal_class_symbol",
            ),
            struct.unpack(">i11s20s32s7si17s6s6s4si7s", spc),
            strict=True,
        )
    }


@file_or_path(mode="rb")
def parse_cell_dump(
    in_file: BinaryIO | FortranBinaryReader,
) -> dict[str, Any]:
    reader = FortranBinaryReader(in_file)

    new = next(reader).strip() == b"BEGIN_UNIT_CELL"

    if new:
        return parse_headered_dump(reader, NEW_CELL_DUMP, "END_UNIT_CELL")

    reader.rewind()
    return reader.get_dtype_dict(OLD_CELL_DUMP)


@file_or_path(mode="rb")
def parse_cell_global(
    in_file: BinaryIO | FortranBinaryReader,
) -> dict[str, Any]:
    reader = FortranBinaryReader(in_file)

    new = next(reader).strip() == b"BEGIN_CELL_GLOBAL"

    if new:
        accum = parse_headered_dump(reader, NEW_CELL_GLOBAL, "END_CELL_GLOBAL")

        for spacegroup in ("spacegroup", "crystal_spacegroup"):
            accum[spacegroup] = _parse_spacegroup(accum[spacegroup])

        return accum

    reader.rewind()

    accum = reader.get_dtype_dict(
        {
            "nkpts": int,
            "kpoints": float,
            "kpoint_weights": float,
            "num_symmetry_operations": int,
        },
    )

    if accum["num_symmetry_operations"]:
        accum.update(
            reader.get_dtype_dict(
                {
                    "symmetry_operations": float,
                    "symmetry_disps": float,
                    "symmetry_equiv_atoms": int,
                },
            ),
        )

    accum.update(
        reader.get_dtype_dict(
            {
                "cell_symmetry_ion_constraints": int,
                "num_ionic_constraints": int,
            },
        ),
    )

    if accum["num_ionic_constraints"]:
        accum["ionic_constraints"] = reader.get((float, ...))

    accum.update(reader.get_dtype_dict(OLD_CELL_GLOBAL))

    return accum
