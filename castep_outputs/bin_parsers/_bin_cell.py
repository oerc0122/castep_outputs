"""Parse parameters dump from check/castep_bin."""

from __future__ import annotations

import struct
from typing import Any, BinaryIO

from castep_outputs.utilities.utility import file_or_path

from .fortran_bin_parser import FortranBinaryReader

NEW_CELL_DUMP = {
    "CELL%REAL_LATTICE": float,
    "CELL%RECIP_LATTICE": float,
    "CELL%VOLUME": float,
    "CELL%NUM_SPECIES": int,
    "CELL%NUM_IONS": int,
    "CELL%MAX_IONS_IN_SPECIES": int,
    "CELL_VERSION_NUMBER": float,
    "CELL%NUM_IONS_IN_SPECIES": int,
    "CELL%IONIC_POSITIONS": float,
    "CELL%IONIC_VELOCITIES": float,
    "CELL%IONIC_CHARGE": int,
    "CELL%IONIC_CHARGE_REAL": float,
    "CELL%ATOM_MOVE": bool,
    "CELL%SPECIES_MASS": float,
    "CELL%SPECIES_SYMBOL": str,
    "CELL%SPECIES_POT": str,
    "CELL%SPECIES_LCAO_STATES": int,
    "CELL%ION_PACK_SPECIES": int,
    "CELL%ION_PACK_INDEX": int,
    "CELL%IONIC_LABEL": str,
    "CELL%INITIAL_MAGNETIC_MOMENT": float,
    "CELL%ATOM_FIX_SPIN": bool,
    "CELL%INITIAL_MAGNETISATION_DIR": float,
    "CELL%INITIAL_NC_DENSITY": bool,
    "CELL%NUM_CELLS_IN_SUPERCELL": int,
    "CELL%SUPERCELL_MATRIX": int,
    "CELL%SUPERCELL_CELL_INDEX": int,
    "CELL%SUPERCELL_ION_INDEX": int,
    "CELL%SUPERCELL_ORIGINS": int,
    "CELL%NUM_MIXTURE_ATOMS": int,
    "CELL%MIXTURE_WEIGHT": float,
    "CELL%LIST_MIXTURE_ATOMS_SIZE": int,
    "CELL%LIST_MIXTURE_ATOMS": int,
    "CELL%ATOM_INIT_MAGMOM": bool,
    "CELL%ATOM_INIT_SPIN": bool,
    "CELL%INDX_MIXTURE_ATOMS": int,
    "CELL%SPECIES_SPIN_ISOTOPE": int,
    "CELL%SPECIES_GAMMA": float,
    "CELL%SPECIES_EFG_ISOTOPE": int,
    "CELL%SPECIES_Q": float,
    "CELL%HUBBARD_U": float,
    "CELL%HUBBARD_ALPHA": float,
    "CELL%CHEMICAL_POTENTIAL": float,
    "CELL%SEDC_CUSTOM_PARAMS_LEN": int,
    "CELL%SEDC_CUSTOM_PARAMS": str,
}


OLD_CELL_DUMP = {
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

NEW_CELL_GLOBAL = {
    "NKPTS": int,
    "KPOINTS": float,
    "KPOINT_WEIGHTS": float,
    "NUM_SYMMETRY_OPERATIONS": int,
    "SYMMETRY_OPERATIONS": float,
    "SYMMETRY_DISPS": float,
    "SYMMETRY_EQUIV_ATOMS": int,
    "SPACEGROUP": bytes,
    "NUM_CRYSTAL_SYMMETRY_OPERATIONS": int,
    "CRYSTAL_SYMMETRY_OPERATIONS": float,
    "CRYSTAL_SYMMETRY_DISPS": float,
    "CRYSTAL_SYMMETRY_EQUIV_ATOMS": int,
    "CRYSTAL_SPACEGROUP": bytes,
    "CELL_SYMMETRY_ION_CONSTRAINTS": int,
    "NUM_IONIC_CONSTRAINTS": int,
    "IONIC_CONSTRAINTS": float,
    "NUM_CELL_CONSTRAINTS": int,
    "CELL_CONSTRAINTS": int,
    "EXTERNAL_PRESSURE": float,
    "EXTERNAL_EFIELD": float,
    "EXTERNAL_BFIELD": float,
    "INPUT_PERMITTIVITY": float,
    "NUM_BS_KPOINTS": int,
    "BS_KPOINTS": float,
    "BS_KPOINT_WEIGHTS": float,
    "NUM_SPECTRAL_KPOINTS": int,
    "SPECTRAL_KPOINTS": float,
    "SPECTRAL_KPOINT_WEIGHTS": float,
    "NUM_PHONON_KPOINTS": int,
    "PHONON_KPOINTS": float,
    "NUM_PHONON_GAMMA_DIRECTIONS": int,
    "PHONON_GAMMA_DIRECTIONS": float,
    "PHONON_KPOINT_WEIGHTS": float,
    "NUM_PHONON_FINE_KPOINTS": int,
    "PHONON_FINE_KPOINTS": float,
    "PHONON_FINE_KPOINT_WEIGHTS": float,
    "NUM_SCF_KPOINTS": int,
    "SCF_KPOINTS": float,
    "SCF_KPOINT_WEIGHTS": float,
    "NUM_MAGRES_KPOINTS": int,
    "MAGRES_KPOINTS": float,
    "MAGRES_KPOINT_WEIGHTS": float,
    "NUM_ELNES_KPOINTS": int,
    "ELNES_KPOINTS": float,
    "ELNES_KPOINT_WEIGHTS": float,
    "NUM_EP_KPOINT_PAIRS": int,
    "EP_KPOINT_PAIRS": float,
    "CELL_SYMMORPHIC": bool,
    "KPOINT_MP_GRID": int,
    "KPOINT_MP_OFFSET": float,
    "KPOINT_MP_DENSITY": float,
    "KPOINT_MP_SPACING": float,
    "FIX_COM": bool,
    "FIX_ALL_IONS": bool,
    "FIX_ALL_CELL": bool,
    "FIX_VOL": bool,
    "SYMMETRY_GENERATE": bool,
    "SYMMETRY_TOL": float,
    "NUM_OPTICS_KPOINTS": int,
    "OPTICS_KPOINTS": float,
    "OPTICS_KPOINT_WEIGHTS": float,
    "OPTICS_KPOINT_MP_GRID": int,
    "OPTICS_KPOINT_MP_OFFSET": float,
    "OPTICS_KPOINT_MP_SPACING": float,
    "OPTICS_KPOINT_MP_DENSITY": float,
    "QUANTISATION_AXIS": float,
    "PHONON_SUPERCELL_MATRIX": int,
    "NUM_SUPERCELL_KPOINTS": int,
    "SUPERCELL_KPOINTS": float,
    "SUPERCELL_KPOINT_WEIGHTS": float,
    "JCOUPLING_SPECIES": int,
    "JCOUPLING_SITE": int,
    "SCF_KPOINT_MP_GRID": int,
    "SCF_KPOINT_MP_OFFSET": float,
    "SCF_KPOINT_MP_SPACING": float,
    "BS_KPOINT_MP_GRID": int,
    "BS_KPOINT_MP_OFFSET": float,
    "BS_KPOINT_MP_SPACING": float,
    "SPECTRAL_KPOINT_MP_GRID": int,
    "SPECTRAL_KPOINT_MP_OFFSET": float,
    "SPECTRAL_KPOINT_MP_SPACING": float,
    "PHONON_KPOINT_MP_GRID": int,
    "PHONON_KPOINT_MP_OFFSET": float,
    "PHONON_KPOINT_MP_SPACING": float,
    "PHONON_FINE_KPOINT_MP_GRID": int,
    "PHONON_FINE_KPOINT_MP_OFFSET": float,
    "PHONON_FINE_KPOINT_MP_SPACING": float,
    "MAGRES_KPOINT_MP_GRID": int,
    "MAGRES_KPOINT_MP_OFFSET": float,
    "MAGRES_KPOINT_MP_SPACING": float,
    "ELNES_KPOINT_MP_GRID": int,
    "ELNES_KPOINT_MP_OFFSET": float,
    "ELNES_KPOINT_MP_SPACING": float,
    "SUPERCELL_KPOINT_MP_GRID": int,
    "SUPERCELL_KPOINT_MP_OFFSET": float,
    "SUPERCELL_KPOINT_MP_SPACING": float,
    "NUM_NONLINEAR_CONSTRAINTS": int,
    "NONLINEAR_CONSTRAINTS": float,
    "NQPTS": int,
    "QPOINTS": float,
    "QPOINT_WEIGHTS": float,
    "QPOINT_CONJG": bool,
    "NQ_TO_SCF_GLOBAL_NK": int,
    "Q_FROM_SCF_K_SYM_OP": int,
    "DENSITY": float,
    "DEVEL_CODE": str,
}

OLD_CELL_GLOBAL = {
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


def _parse_new_format(
    reader: FortranBinaryReader, dtypes: dict[str, type], term: str
) -> dict[str, Any]:
    accum = {}

    try:
        while (header := reader.get(str).strip()) != term:
            key = header.split("%")[1] if "%" in header else header
            accum[key.lower()] = reader.get(dtypes[header])
    except KeyError:
        raise ValueError(f"Unable to parse unknown block {header}.")
    except Exception:
        reader.rewind()
        raw_data = next(reader)
        raise TypeError(f"Unable to process data ({raw_data}) as {dtypes[header]} for {header}.")

    return accum


@file_or_path(mode="rb")
def parse_cell_dump(
    in_file: BinaryIO | FortranBinaryReader,
) -> dict[str, Any]:
    reader = in_file if isinstance(in_file, FortranBinaryReader) else FortranBinaryReader(in_file)

    new = next(reader).strip() == b"BEGIN_UNIT_CELL"

    if new:
        return _parse_new_format(reader, NEW_CELL_DUMP, "END_UNIT_CELL")

    reader.rewind()
    return reader.get_dtype_dict(OLD_CELL_DUMP)


@file_or_path(mode="rb")
def parse_cell_global(
    in_file: BinaryIO | FortranBinaryReader,
) -> dict[str, Any]:
    reader = in_file if isinstance(in_file, FortranBinaryReader) else FortranBinaryReader(in_file)

    new = next(reader).strip() == b"BEGIN_CELL_GLOBAL"

    if new:
        accum = _parse_new_format(reader, NEW_CELL_GLOBAL, "END_CELL_GLOBAL")

        for spacegroup in ("spacegroup", "crystal_spacegroup"):
            accum[spacegroup] = _parse_spacegroup(accum[spacegroup])

        return accum

    reader.rewind()

    accum = reader.get_dtype_dict(
        {"nkpts": int, "kpoints": float, "kpoint_weights": float, "num_symmetry_operations": int}
    )

    if accum["num_symmetry_operations"]:
        accum.update(
            reader.get_dtype_dict(
                {
                    "symmetry_operations": float,
                    "symmetry_disps": float,
                    "symmetry_equiv_atoms": int,
                }
            )
        )

    accum.update(
        reader.get_dtype_dict(
            {
                "cell_symmetry_ion_constraints": int,
                "num_ionic_constraints": int,
            }
        )
    )

    if accum["num_ionic_constraints"]:
        accum["ionic_constraints"] = reader.get(float)

    accum.update(reader.get_dtype_dict(OLD_CELL_GLOBAL))

    return accum
