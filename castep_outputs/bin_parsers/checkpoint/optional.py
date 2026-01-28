"""Parse optional components in CASTEP_BIN dump."""
from itertools import product
from typing import Any

from castep_outputs.bin_parsers.checkpoint.cell import parse_cell_dump
from castep_outputs.bin_parsers.checkpoint.utility import parse_nested_header_dump
from castep_outputs.bin_parsers.fortran_bin_parser import FortranBinaryReader
from castep_outputs.utilities.type_conv import (
    ByteParser,
    ToTypeTuple,
    _parse_complex_bytes,
    _parse_int_bytes,
)

OPTIONAL_SEC: dict[str, dict[str, type | ByteParser | ToTypeTuple]] = {
    "E_FERMI": {"fermi_energy": float},
    "OEP_POT": {
        "found_oep_ground_state": bool,
        "oep_energy_difference": float,
        "oep_potential": (),
    },
    "OEP_HF_DEN": {"oep_den_need_ked": bool, "oep_hf_density": ()},
    "DE_DLOGE": {"de_deloge": float},
    "FORCES": {"forces": (float, ...)},
    "STRESS": {"stress": (float, ...), "strain": (float, ...)},
    "MD": {"iteration": int, "time": float},
    "PIMD": {
        "staging": bool,
        "num_stages": int,
        "num_beads": int,
        "current_bead": int,
        "r": (float, ...),
        "v": (float, ...),
        "f": (float, ...),
        "mass": (float, ...),
        "kinetic_energy": (float, ...),
        "total_energy": (float, ...),
        "hamilt_energy": (float, ...),
        "potential_energy": (float, ...),
        "spring_energy": (float, ...),
        "primitive_energy": (float, ...),
        "virial_energy": (float, ...),
        "actual_temp": (float, ...),
        "actual_press": (float, ...),
        "stress": (float, ...),
    },
    "MD_HUG": {
        "curr_compression": float,
        "unshock_e": float,
        "unshock_v": float,
        "unshock_p": float,
        "chi": float,
        "eta": float,
    },
    "MD_NOSE": {"r": float, "v": float},
    "MD_NOSE_2": {
        "ion_r": (float, ...),
        "ion_v": (float, ...),
        "ion_g": (float, ...),
        "cell_r": (float, ...),
        "cell_v": (float, ...),
        "cell_g": (float, ...),
    },
    "BFGS": {"iteration": int, "inv_hessian": (float, ...)},
    "LBFGS": {
        "iteration": int,
        "num_updates": int,
        "position_updates": (float, ...),
        "gradient_updates": (float, ...),
    },
    "TPSD": {
        "iteration": int,
        "num_updates": int,
        "position_updates": (float, ...),
        "gradient_updates": (float, ...),
    },
    "DAMPED_MD": {"iteration": int, "time": float, "gamma": (float, ...), "md_energy": float},
    "FIRE": {
        "iteration": int,
        "time": float,
        "gamma": (float, ...),
        "md_energy": float,
        "reset": bool,
        "alpha": float,
    },
    "VAR_CELL": {
        "cell": parse_cell_dump,
        "isoshape": bool,
        "r": (float, ...),
        "v": (float, ...),
        "f": (float, ...),
    },
    "PHONON": {"nq_complete": int, "dynamical_matrix": (complex, ...)},
    "PHON_GAMMA": {"dynamical_matrix_gamma": (float, ...)},
    "SECONDD": {
        "q_point": (float, ...),
        "dynamical_matrix_size": int,
        "dynamical_matrix_assigned": (bool, ...),
        "dynamical_matrix": (complex, ...),
    },
    "FORCE_CON": {
        "supercell_matrix": (int, ...),
        "force_constant_matrix": (float, ...),
        "supercell_origins": (float, ...),
        "dipole_subtraction": bool,
    },
    "FINE_FREQ": {"fine_frequencies": (float, ...)},
    "PHONON_ADP": {"thermal_adps": (float, ...)},
    "PHONON_DOS": {"phonon_dos": (float, ...)},
    "BORN_CHGS": {"born_charges": (float, ...), "assigned": (bool, ...)},
    "PART_CHGS": {"born_charges": (float, ...), "assigned": (bool, ...)},
    "DIELECTRIC": {"dielectric_permittivity": (float, ...), "permittivity_is_imported": bool},
    "NLO_D_MATR": {"d_matrix": (float, ...)},
    "RAMAN_TENS": {"converged": bool, "active": (bool, ...), "tensors": (float, ...)},
    "RAMAN_ATOM": {"atomic_tensor": (float, ...), "assigned": (bool, ...)},
    "SHIELDING": {"tensor": (float, ...), "susceptibility": (float, ...)},
    "EFG": {"tensor": (float, ...)},
    "GTENSOR": {"tensor": (float, ...)},
    "HYPERFINE": {"tensor": (float, ...)},
    "JCOUP": {"species": int, "site": int},
    "JCOUP_FC": {"fc": (float, ...)},
    "JCOUP_SPIN": {"spin": (float, ...)},
    "JCOUP_ORB": {"d": (float, ...), "p": (float, ...)},
    "GENETIC": {
        "pop_size": int,
        "max_gens": int,
        "generation": int,
        "populations": (),
        "enthalpy": (float, ...),
        "fitness": (float, ...),
        "birthplace": (int, ...),
        "birthday": (int, ...),
        "kids": (int, ...),
        "converged": (bool, ...),
        "fittest": (bool, ...),
    },
    "HUBBARD": {"hubbard_u": ()},
    "TDDFT_EIG": {
        "total_states": int,
        "eigenvalues": (float, ...),
        "converged": (bool, ...),
        "state_character": str,
        "num_unocc": int,
        "num_occ": int,
        "overlaps": (complex, ...),
    },
    "TDDFT_FOR": {"forces_state": int, "forces": (float, ...)},
    "EPCOUPLING": {
        "num_kpoint_pairs": int,
        "num_bands": int,
        "min_band": int,
        "max_band": int,
        "calculated": bool,
        "kpoint_pairs": (float, ...),
        "phonon_freqs": (float, ...),
        "phonon_modes": (complex, ...),
        "matrix_elements": (complex, ...),
    },
    "TSS": {"iteration": int, "images": (float, ...)},
    "SOLVATION": {"vacuum_energy": float},
    "ELASTIC": {"elastic_constants": (float, ...)},
    "ELASTIC_FI": {"frozen_ion": (float, ...)},
    "INT_STRAIN": {"internal_strain": (float, ...)},
    "PIEZO": {"piezoelectric_constants": (float, ...)},
    "PIEZO_FI": {"piezoelectric_frozen_ion": (float, ...)},
    "FORCE_FIELD": {},
    "ML_ENERGY": {},
}


def parse_hubbard_occm(reader: FortranBinaryReader) -> dict[str, Any]:
    accum = {}

    accum["num_channels"], accum["lmax"], accum["n_spins"] = reader.get((int, ...))
    accum.update(
        reader.get_dtype_dict(
            {
                "N_matrix": (complex, ...),
                "_META": str,
                "channel_l": (int, ...),
                "channel_species": (int, ...),
                "channel_ion": (int, ...),
            }
        )
    )
    return accum


def parse_potential(
    reader: FortranBinaryReader,
    fine_grid: tuple[int, int, int],
    n_spins: int,
) -> list[list[tuple[complex, ...]]]:
    nx, ny, _nz = fine_grid

    grid: list[list[tuple[complex, ...]]] = [[() for _ in range(ny)] for _ in range(nx)]

    for row in reader.get_dtype_cycle(
        {"nx": int, "ny": int, "zcol": (complex, ...)}, n=n_spins * nx * ny
    ):
        grid[row["nx"], row["ny"]] = row["zcol"]

    return grid


def parse_wave(reader: FortranBinaryReader, version: tuple[int, int]) -> dict:

    accum = {}
    accum["type"] = reader.get(str).strip()

    match accum["type"]:
        case "Gpt" | "wave" | "G-sl" | "sl":
            accum["ng"] = reader.get((int, ...))
            if version < (7, 0):
                _ncoeffs, nbands, accum["nkpts"], nspins = reader.get((int, ...))
                nspinorcomps = 1
            else:
                _ncoeffs, nspinorcomps, nbands, accum["nkpts"], nspins = reader.get((int, ...))

            dkc = accum["data_kpoint_coords"] = {}
            pw = accum["total_pw"] = {}
            pw_coord = accum["pw_grid_coord"] = {}
            coeffs = accum["coeffs"] = {}

            for ns in range(nspins):
                for nk in range(accum["nkpts"]):
                    dkc[ns, nk], pw[ns, nk] = reader.get((int, ...))
                    pw_coord[ns, nk] = [reader.get((int, ...)) for _ in range(3)]
                    coeffs[ns, nk] = [
                        [reader.get((complex, ...)) for _ in range(nbands)]
                        for _ in range(nspinorcomps)
                    ]

                    data_coeffs = {}
                    for nb1 in range(nbands):
                        for sc in range(nspinorcomps):
                            data_coeffs[sc, nb1] = reader.get((complex, ...))

        case "bks":
            coeffs = accum["coeffs"] = {}

            band, *kpoint, spin = reader.get_dtype_iter((int, float, float, float, int))
            n_coeffs, paged = reader.get_dtype_iter((int, bool))
            coeffs[spin,] = reader.get((complex, ...))

    return accum

def parse_occ(
    reader: FortranBinaryReader,
    nkpoints: int,
    nspins: int,
) -> tuple[
    list[tuple[float, ...]],
    list[tuple[float, ...]],
]:

    occupancies: list[tuple[float, ...]] = [() for _ in range(nkpoints)]
    eigenvalues: list[tuple[float, ...]] = [() for _ in range(nkpoints)]
    for kp in range(nkpoints):
        _current_kp = reader.get((float, ...))

        for _ in range(nspins):
            occupancies[kp] = reader.get((float, ...))
            eigenvalues[kp] = reader.get((float, ...))

    return occupancies, eigenvalues


def parse_density(
    reader: FortranBinaryReader,
    fine_grid: tuple[int, int, int],
    n_spins: int,
) -> tuple[
    list[list[tuple[complex, ...]]],
    list[list[tuple[complex, ...]]] | None,
]:

    grid_nx, grid_ny, grid_nz = fine_grid

    den_charge: list[list[tuple[complex, ...]]] = [
        [() for _ in range(grid_ny)] for _ in range(grid_nx)
    ]

    if n_spins == 2:  # or den.has_ncm:
        den_spin: list[list[tuple[complex, ...]]] = [
            [() for _ in range(grid_ny)] for _ in range(grid_nx)
        ]

        for nx, ny in product(range(grid_nx), range(grid_ny)):
            data = reader.get(bytes)
            _nx, _ny = _parse_int_bytes(data[:8])
            col = _parse_complex_bytes(data[8:])
            den_charge[nx][ny] = col[:grid_nz]
            den_spin[nx][ny] = col[grid_nz:]

        return den_charge, den_spin

    for nx, ny in product(range(grid_nx), range(grid_ny)):
        data = reader.get(bytes)
        _nx, _ny = _parse_int_bytes(data[:8])
        den_charge[nx][ny] = _parse_complex_bytes(data[8:])

    return den_charge, None


def parse_optional(reader: FortranBinaryReader, accum: dict[str, Any]) -> dict[str, Any]:

    OPTIONAL_SEC["OEP_POT"]["oep_potential"] = lambda _: parse_potential(
        reader,
        accum["ng_fine"],
        accum["n_spins"],
    )
    OPTIONAL_SEC["OEP_HF_DEN"]["oep_hf_density"] = lambda _: parse_density(
        reader,
        accum["ng_fine"],
        accum["n_spins"],
    )
    OPTIONAL_SEC["HUBBARD"]["hubbard_u"] = lambda _: parse_hubbard_occm(reader)
    OPTIONAL_SEC["GENETIC"]["populations"] = lambda _: parse_cell_dump(reader)

    optional = parse_nested_header_dump(reader, dtypes=OPTIONAL_SEC, term="END")

    return optional
