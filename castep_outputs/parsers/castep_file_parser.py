# pylint: disable=too-many-lines, too-many-branches, too-many-statements, too-many-locals
"""
Extract results from .castep file for comparison and further processing.

Notes
-----
Port of extract_results.pl
"""
from __future__ import annotations

import io
import itertools
import re
from collections import defaultdict
from enum import Flag, auto
from typing import Any, Dict, List, TextIO, Union, cast

from ..utilities import castep_res as REs
from ..utilities.castep_res import gen_table_re, get_numbers, labelled_floats
from ..utilities.constants import SHELLS
from ..utilities.datatypes import (
    AtomIndex,
    AtomPropBlock,
    BandStructure,
    BondData,
    CellInfo,
    CharTable,
    ConstraintsReport,
    DipoleTable,
    ElasticProperties,
    FinalConfig,
    GeomTable,
    InitialSpin,
    KPointsList,
    KPointsSpec,
    MDInfo,
    MemoryEst,
    MullikenInfo,
    Occupancies,
    PhononSymmetryReport,
    PSPotEnergy,
    PSPotReport,
    PSPotStrInfo,
    QData,
    RamanReport,
    SCFDebugInfo,
    SCFReport,
    SixVector,
    SymmetryReport,
    TDDFTData,
    Thermodynamics,
    ThreeByThreeMatrix,
    ThreeVector,
    WvfnLineMin,
)
from ..utilities.filewrapper import Block, FileWrapper
from ..utilities.utility import (
    add_aliases,
    atreg_to_index,
    determine_type,
    fix_data_types,
    get_only,
    log_factory,
    normalise_key,
    normalise_string,
    parse_int_or_float,
    stack_dict,
    to_type,
)
from .bands_file_parser import parse_bands_file
from .cell_param_file_parser import _parse_devel_code_block
from .efield_file_parser import parse_efield_file
from .elastic_file_parser import parse_elastic_file
from .hug_file_parser import parse_hug_file
from .parse_fmt_files import (
    parse_chdiff_fmt_file,
    parse_den_fmt_file,
    parse_elf_fmt_file,
    parse_pot_fmt_file,
)
from .phonon_dos_file_parser import parse_phonon_dos_file
from .xrd_sf_file_parser import parse_xrd_sf_file


class Filters(Flag):
    """Enum of possible filters for CASTEP file parsing."""

    BS = auto()
    CELL = auto()
    CHEM_SHIELDING = auto()
    DIPOLE = auto()
    ELASTIC = auto()
    ELF = auto()
    FINAL_CONFIG = auto()
    FORCE = auto()
    GEOM_OPT = auto()
    MD = auto()
    MD_SUMMARY = auto()
    OPTICS = auto()
    PARAMETERS = auto()
    PHONON = auto()
    POPN_ANALYSIS = auto()
    POSITION = auto()
    PSPOT = auto()
    SCF = auto()
    SOLVATION = auto()
    SPECIES_PROPS = auto()
    SPIN = auto()
    STRESS = auto()
    SYMMETRIES = auto()
    SYS_INFO = auto()
    TDDFT = auto()
    TEST_EXTRA_DATA = auto()
    THERMODYNAMICS = auto()
    TSS = auto()

    # Preset sets
    NONE = 0
    LOW = (BS | CELL | CHEM_SHIELDING | DIPOLE |
           ELASTIC | ELF | FINAL_CONFIG | FORCE |
           MD_SUMMARY | OPTICS | POPN_ANALYSIS |
           POSITION | SOLVATION | SPECIES_PROPS | SPIN |
           STRESS | TDDFT | THERMODYNAMICS | TSS)

    MEDIUM = LOW | PARAMETERS | GEOM_OPT | MD | PHONON

    HIGH = MEDIUM | PSPOT | SYMMETRIES | SYS_INFO

    FULL = HIGH | SCF
    ALL = FULL

    TESTING = (BS | CELL | CHEM_SHIELDING | DIPOLE |
               ELASTIC | ELF | FORCE |
               GEOM_OPT | MD | OPTICS |
               PHONON | POPN_ANALYSIS | POSITION |
               PSPOT | SOLVATION | SPECIES_PROPS |
               STRESS | TDDFT | TEST_EXTRA_DATA |
               THERMODYNAMICS | TSS)


def parse_castep_file(castep_file_in: TextIO,
                      filters: Filters = Filters.HIGH) -> list[dict[str, Any]]:
    """
    Parse castep file into lists of dicts ready to JSONise.

    Parameters
    ----------
    castep_file_in
        File to parse.
    filters
        Parameters to parse.

    Returns
    -------
    list[dict[str, Any]]
        Parsed data.

    Raises
    ------
    ValueError
        On invalid top-level blocks.
    """
    # pylint: disable=redefined-outer-name

    runs: list[dict[str, Any]] = []
    curr_run: dict[str, Any] = defaultdict(list)

    to_parse = filters

    if not isinstance(castep_file_in, (FileWrapper, Block)):
        castep_file = FileWrapper(castep_file_in)
    else:
        castep_file = castep_file_in

    logger = log_factory(castep_file)

    for line in castep_file:
        # Build Info
        if block := Block.from_re(line, castep_file,
                                  r"^\s*Compiled for",
                                  REs.EMPTY):

            if curr_run:
                runs.append(curr_run)
            logger("Found run %s", len(runs) + 1)
            curr_run = defaultdict(list)

            if Filters.SYS_INFO not in to_parse:
                continue

            logger("Found build info")
            curr_run["build_info"] = _process_buildinfo(block)

        elif re.search(r"Run started", line):

            if Filters.SYS_INFO not in to_parse:
                continue

            curr_run["time_started"] = normalise_string(line.split(":", 1)[1])

        # Finalisation
        elif block := Block.from_re(line, castep_file, "Initialisation time", "Peak Memory Use"):

            if Filters.SYS_INFO not in to_parse:
                continue

            logger("Found finalisation")
            curr_run.update(_process_finalisation(block))

        elif line.startswith("Overall parallel efficiency rating"):

            if Filters.SYS_INFO not in to_parse:
                continue

            logger("Found parallel efficiency")

            curr_run["parallel_efficiency"] = float(get_numbers(line)[0])

        # Continuation
        elif line.startswith("Reading continuation data"):

            if Filters.SYS_INFO not in to_parse:
                continue

            logger("Found continuation block")

            curr_run["continuation"] = line.split()[-1]

        # Warnings
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("", r"\?+"),
                                    gen_table_re("", r"\?+")):

            if Filters.SYS_INFO not in to_parse:
                continue

            logger("Found warning")

            block.remove_bounds(1, 1)
            curr_run["warning"].append(" ".join(x.strip() for x in block))

        elif match := re.match(r"(?:\s*[^:]+:)?(\s*)warning", line, re.IGNORECASE):

            if Filters.SYS_INFO not in to_parse:
                continue

            logger("Found warning")

            warn = line.strip()

            for tst, line in enumerate(castep_file):
                if not line.strip() or not re.match(match.group(1)+r"\s+", line):
                    if tst:
                        castep_file.rewind()
                    break
                warn += " " + line.strip()

            curr_run["warning"].append(warn)

        # Memory estimate
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re(r"MEMORY AND SCRATCH[\w\s]+", "[+-]+"),
                                    gen_table_re("", "[+-]+")):

            if Filters.SYS_INFO not in to_parse:
                continue

            logger("Found memory estimate")

            curr_run["memory_estimate"].append(_process_memory_est(block))

        # Title
        elif re.match(gen_table_re("Title", r"\*+"), line):

            if Filters.PARAMETERS not in to_parse:
                continue

            logger("Found title")

            curr_run["title"] = next(castep_file).strip()

        # Parameters
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("[^*]+ Parameters", r"\*+"),
                                    gen_table_re("", r"\*+")):

            if Filters.PARAMETERS not in to_parse:
                continue

            logger("Found options")

            curr_run["options"] = _process_params(block)

        # Quantisation axis
        elif "Quantisation axis" in line:

            if Filters.SPECIES_PROPS not in to_parse:
                continue

            logger("Found Quantisation axis")

            curr_run["quantisation_axis"] = to_type(get_numbers(line), float)

        # Pseudo-atomic energy
        elif block := Block.from_re(line, castep_file, REs.PS_SHELL_RE, REs.EMPTY, n_end=2):

            if Filters.SPECIES_PROPS not in to_parse:
                continue

            logger("Found pseudo-atomic energy")

            key, val = _process_ps_energy(block)

            if "species_properties" not in curr_run:
                curr_run["species_properties"] = defaultdict(dict)

            curr_run["species_properties"][key].update(val)

        # Mass
        elif block := Block.from_re(line, castep_file, r"Mass of species in AMU", REs.EMPTY):

            if Filters.SPECIES_PROPS not in to_parse:
                continue

            logger("Found mass")

            if "species_properties" not in curr_run:
                curr_run["species_properties"] = defaultdict(dict)

            for key, val in _process_spec_prop(block):
                curr_run["species_properties"][key]["mass"] = float(val)

        # Electric Quadrupole Moment
        elif block := Block.from_re(line, castep_file,
                                    r"Electric Quadrupole Moment",
                                    rf"({REs.EMPTY}|^\s*x+$)"):
            if Filters.SPECIES_PROPS not in to_parse:
                continue

            logger("Found electric quadrupole moment")

            if "species_properties" not in curr_run:
                curr_run["species_properties"] = defaultdict(dict)

            for key, val, *_ in _process_spec_prop(block):
                curr_run["species_properties"][key]["electric_quadrupole_moment"] = float(val)

        # Pseudopots
        elif block := Block.from_re(line, castep_file,
                                    r"Files used for pseudopotentials", REs.EMPTY):

            if Filters.SPECIES_PROPS not in to_parse:
                continue

            logger("Found pseudopotentials")

            if "species_properties" not in curr_run:
                curr_run["species_properties"] = defaultdict(dict)

            for key, val in _process_spec_prop(block):
                if Filters.PSPOT in to_parse and "|" in val:
                    val = _process_pspot_string(val)

                curr_run["species_properties"][key]["pseudopot"] = val

        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Pseudopotential Report[^|]+", r"\|"),
                                    gen_table_re("", "=+")):

            if Filters.PSPOT not in to_parse:
                continue

            logger("Found pseudopotential report")

            curr_run["pspot_detail"].append(_process_pspot_report(block))

        elif match := re.match(r"\s*(?P<type>AE|PS) eigenvalue nl (?P<nl>\d+) =" +
                               labelled_floats(("eigenvalue",)), line):

            if Filters.PSPOT not in to_parse:
                continue

            logger("Found PSPot debug for %s at %s", match["type"], match["nl"])

            val = match.groupdict()
            fix_data_types(val, {"nl": int, "eigenvalue": float})

            curr_run["pspot_debug"].append(val)

        # Pair Params
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("PairParams", r"\*+", pre=r"\w*"),
                                    REs.EMPTY):

            if Filters.PARAMETERS not in to_parse:
                continue

            logger("Found pair params")

            curr_run["pair_params"].append(_process_pair_params(block))

        # DFTD
        elif block := Block.from_re(line, castep_file,
                                    "DFT-D parameters",
                                    r"^\s*$", n_end=3):

            if Filters.PARAMETERS not in to_parse:
                continue

            logger("Found DFTD block")

            curr_run["dftd"] = _process_dftd(block)

        # SCF
        elif block := Block.from_re(line, castep_file, "SCF loop", "^-+ <-- SCF", n_end=2):

            if Filters.SCF not in to_parse:
                continue

            logger("Found SCF")

            curr_run["scf"].append(_process_scf(block))

        # SCF Line min
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("WAVEFUNCTION LINE MINIMISATION", "[+-]+",
                                                 post="<- line"),
                                    gen_table_re("", "[+-]+", post="<- line"), n_end=2):

            if Filters.SCF not in to_parse:
                continue

            logger("Found wvfn line min")

            curr_run["wvfn_line_min"].append(_process_wvfn_line_min(block))

        # SCF Occupancy
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Occupancy", r"\|",
                                                 post="<- occ", whole_line=False),
                                    r"Have a nice day\."):

            if Filters.SCF not in to_parse:
                continue

            logger("Found occupancies")

            curr_run["occupancies"].append(_process_occupancies(block))

        # SCF Basis set
        elif match := re.search(r" with +(\d) +cut-off energies.", line):

            if Filters.SCF not in to_parse:
                continue

            ncut = int(match.group(1))
            line = ""
            next(castep_file)
            block = Block.from_re(line, castep_file,
                                  "",
                                  "^-+ <-- SCF", n_end=ncut*3)
            data = get_only(parse_castep_file(block, Filters.HIGH | Filters.SCF))

            scf = data.pop("scf")
            curr_run["bsc_energies"] = data.pop("energies")

            curr_run["scf"], curr_run["bsc_scf"] = scf[-1], scf[:-1]

            curr_run.update(data)

        # Energies
        elif line.startswith("Final energy, E") or line.startswith("Final energy"):

            logger("Found energy")

            if "energies" not in curr_run:
                curr_run["energies"] = defaultdict(list)

            curr_run["energies"]["final_energy"].append(to_type(get_numbers(line)[-1], float))

        elif "Total energy corrected for finite basis set" in line:

            logger("Found energy")

            if "energies" not in curr_run:
                curr_run["energies"] = defaultdict(list)

            curr_run["energies"]["final_basis_set_corrected"].append(
                to_type(get_numbers(line)[-1], float))

        elif "0K energy (E-0.5TS)" in line:

            logger("Found estimated 0K energy")

            if "energies" not in curr_run:
                curr_run["energies"] = defaultdict(list)

            curr_run["energies"]["est_0K"].append(to_type(get_numbers(line)[-1], float))

        elif line.startswith("(SEDC) Total Energy"):

            logger("Found SEDC energy correction")

            if "energies" not in curr_run:
                curr_run["energies"] = defaultdict(list)

            curr_run["energies"]["sedc_correction"].append(to_type(get_numbers(line)[-1], float))

        elif line.startswith("Dispersion corrected final energy"):

            logger("Found SEDC final energy")

            if "energies" not in curr_run:
                curr_run["energies"] = defaultdict(list)

            curr_run["energies"]["disperson_corrected"].append(
                to_type(get_numbers(line)[-1], float))

        # Free energies
        elif re.match(rf"Final free energy \(E-TS\) += +({REs.EXPFNUMBER_RE})", line):

            logger("Found free energy (E-TS)")

            if "energies" not in curr_run:
                curr_run["energies"] = defaultdict(list)

            curr_run["energies"]["free_energy"].append(to_type(get_numbers(line)[-1], float))

        # Solvation energy
        elif line.startswith(" Free energy of solvation"):

            if Filters.SOLVATION not in to_parse:
                continue

            logger("Found solvation energy")

            if "energies" not in curr_run:
                curr_run["energies"] = defaultdict(list)

            curr_run["energies"]["solvation"].append(*to_type(get_numbers(line), float))

        # Spin densities
        elif match := REs.INTEGRATED_SPIN_DENSITY_RE.match(line):

            if Filters.SCF not in to_parse and Filters.SPIN not in to_parse:
                continue

            logger("Found spin")

            val = match["val"] if len(match["val"].split()) == 1 else match["val"].split()

            if "|" in line:
                curr_run["modspin"].append(to_type(val, float))
            else:
                curr_run["spin"].append(to_type(val, float))

        # Initial cell
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Unit Cell"), REs.EMPTY, n_end=3):

            if Filters.CELL not in to_parse:
                continue

            logger("Found cell")

            curr_run["initial_cell"] = _process_unit_cell(block)

        # Cell Symmetry and contstraints
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Symmetry and Constraints"),
                                    "Cell constraints are"):

            if Filters.SYMMETRIES not in to_parse:
                continue

            logger("Found symmetries")

            curr_run["symmetries"], curr_run["constraints"] = _process_symmetry(block)

        # TSS (must be ahead of initial pos)
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("(Reactant|Product)", "x"),
                                    gen_table_re("", "x+"), n_end=2):

            if Filters.TSS not in to_parse or Filters.POSITION not in to_parse:
                continue

            mode = "reactant" if "Reactant" in line else "product"

            logger("Found %s initial states", mode)

            curr_run[mode] = _process_atreg_block(block)

        # Initial pos
        elif block := Block.from_re(line, castep_file,  # Labelled
                                    r"Fractional coordinates of atoms\s+User-defined",
                                    gen_table_re("", "x+")):

            if Filters.POSITION not in to_parse:
                continue

            if "labels" not in curr_run:
                curr_run["labels"] = defaultdict(dict)

            logger("Found initial positions")

            curr_run["initial_positions"] = {}
            for line in block:
                if match := REs.LABELLED_POS_RE.search(line):
                    ind = atreg_to_index(match)

                    if lab := match["label"].strip():
                        curr_run["labels"][ind] = lab
                        ind = (f"{ind[0]} [{lab}]", ind[1])
                    else:
                        curr_run["labels"][ind] = "NULL"

                    curr_run["initial_positions"][ind] = to_type(match.group("x", "y", "z"), float)

        elif block := Block.from_re(line, castep_file,  # Mixture
                                    r"Mixture\s+Fractional coordinates of atoms",
                                    gen_table_re("", "x+")):

            if Filters.POSITION not in to_parse:
                continue

            logger("Found initial positions")

            curr_run["initial_positions"] = {}
            for line in block:
                if match := REs.MIXTURE_LINE_1_RE.search(line):
                    val = match.groupdict()
                    spec, idx = atreg_to_index(match)
                    pos = to_type(match.group("x", "y", "z"), float)
                    weight = float(match["weight"])

                    curr_run["initial_positions"][(spec, idx)] = {"pos": pos, "weight": weight}

                elif match := REs.MIXTURE_LINE_2_RE.search(line):
                    spec = match["spec"].strip()
                    weight = float(match["weight"])

                    curr_run["initial_positions"][(spec, idx)] = {"pos": pos, "weight": weight}

        elif block := Block.from_re(line, castep_file,
                                    "Fractional coordinates of atoms",
                                    gen_table_re("", "x+")):

            if Filters.POSITION not in to_parse:
                continue

            logger("Found initial positions")

            curr_run["initial_positions"] = _process_atreg_block(block)

        elif "Supercell generated" in line:
            accum = iter(get_numbers(line))
            curr_run["supercell"] = tuple(to_type([next(accum) for _ in range(3)], float)
                                          for _ in range(3))

        # Initial vel
        elif block := Block.from_re(line, castep_file,
                                    "User Supplied Ionic Velocities",
                                    gen_table_re("", "x+")):

            if Filters.POSITION not in to_parse:
                continue

            logger("Found initial velocities")

            curr_run["initial_velocities"] = _process_atreg_block(block)

        # Initial spins
        elif block := Block.from_re(line, castep_file,
                                    "Initial magnetic",
                                    gen_table_re("", "x+")):

            if Filters.PARAMETERS not in to_parse:
                continue

            logger("Found initial spins")

            curr_run["initial_spins"] = _process_initial_spins(block)

        # Target Stress
        elif block := Block.from_re(line, castep_file, "External pressure/stress", "", n_end=3):

            if Filters.PARAMETERS not in to_parse:
                continue

            logger("Found target stress")

            accum = [to_type(number, float)
                     for line in block
                     for number in get_numbers(line)]

            curr_run["target_stress"].append(accum)

        # Finite basis correction parameter
        elif match := re.search(rf"finite basis dEtot\/dlog\(Ecut\) = +({REs.FNUMBER_RE})", line):

            logger("Found dE/dlog(E)")
            curr_run["dedlne"] = to_type(match.group(1), float)

        # K-Points
        elif block := Block.from_re(line, castep_file, "k-Points For BZ Sampling", REs.EMPTY):

            if Filters.PARAMETERS not in to_parse:
                continue

            logger("Found k-points")

            curr_run["k-points"] = _process_kpoint_blocks(block, implicit_kpoints=True)

        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Number +Fractional coordinates +Weight", r"\+"),
                                    gen_table_re("", r"\++")):

            if Filters.PARAMETERS not in to_parse:
                continue

            logger("Found k-points list")

            curr_run["k-points"] = _process_kpoint_blocks(block, implicit_kpoints=False)

        elif "Applied Electric Field" in line:

            if Filters.PARAMETERS not in to_parse:
                continue

            logger("Found electric field")
            line = next(castep_file)
            curr_run["applied_field"] = to_type(get_numbers(line), float)

        # Forces blocks
        elif block := Block.from_re(line, castep_file, REs.FORCES_BLOCK_RE, r"^\s*\*+$"):

            if Filters.FORCE not in to_parse:
                continue

            if "forces" not in curr_run:
                curr_run["forces"] = defaultdict(list)

            key, val = _process_forces(block)

            logger("Found %s forces", key)

            curr_run["forces"][key].append(val)

        # Stress tensor block
        elif block := Block.from_re(line, castep_file, REs.STRESSES_BLOCK_RE, r"^\s*\*+$"):
            if Filters.STRESS not in to_parse:
                continue

            if "stresses" not in curr_run:
                curr_run["stresses"] = defaultdict(list)

            key, val = _process_stresses(block)

            logger("Found %s stress", key)

            curr_run["stresses"][key].append(val)

            # Phonon block
        elif block := Block.from_re(line, castep_file,
                                    "Vibrational Frequencies",
                                    gen_table_re("", "=+")):

            if Filters.PHONON not in to_parse:
                continue

            logger("Found phonon")

            curr_run["phonons"] = _process_phonon(block, logger)

            logger("Found %d phonon samples", len(curr_run["phonons"]))

        # Phonon Symmetry
        elif block := Block.from_re(line, castep_file,
                                    "Phonon Symmetry Analysis", REs.EMPTY):

            if Filters.PHONON not in to_parse:
                continue

            logger("Found phonon symmetry analysis")

            val = _process_phonon_sym_analysis(block)
            curr_run["phonon_symmetry_analysis"].append(val)

        # Dynamical Matrix
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Dynamical matrix"),
                                    gen_table_re("", "-+")):

            if Filters.PHONON not in to_parse:
                continue

            logger("Found dynamical matrix")

            val = _process_dynamical_matrix(block)
            curr_run["dynamical_matrix"] = val

        # Raman tensors
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Raman Susceptibility Tensors[^+]*", r"\+"),
                                    REs.EMPTY):

            if Filters.PHONON not in to_parse:
                continue

            logger("Found Raman")

            curr_run["raman"].append(_process_raman(block))

        # Solvation
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("AUTOSOLVATION CALCULATION RESULTS", r"\*+"),
                                    r"^\s*\*+\s*$"):

            if Filters.SOLVATION not in to_parse:
                continue

            logger("Found autosolvation")

            curr_run["autosolvation"] = _process_autosolvation(block)

        # Permittivity and NLO Susceptibility
        elif block := Block.from_re(line, castep_file,
                                    r"^\s+Optical Permittivity", r"^ =+$"):

            if Filters.OPTICS not in to_parse:
                continue

            logger("Found optical permittivity")

            val = _process_3_6_matrix(block, split=True)
            curr_run["optical_permittivity"] = val[0]
            if val[1]:
                curr_run["dc_permittivity"] = val[1]

        # Polarisability
        elif block := Block.from_re(line, castep_file, r"^\s+Polarisabilit(y|ies)", r"^ =+$"):

            if Filters.OPTICS not in to_parse:
                continue

            logger("Found polarisability")

            val = _process_3_6_matrix(block, split=True)
            curr_run["optical_polarisability"] = val[0]
            if val[1]:
                curr_run["static_polarisability"] = val[1]

        # Non-linear
        elif block := Block.from_re(line, castep_file,
                                    r"^\s+Nonlinear Optical Susceptibility", r"^ =+$"):

            if Filters.OPTICS not in to_parse:
                continue

            logger("Found NLO")

            curr_run["nlo"], _ = _process_3_6_matrix(block, split=False)

        # Atomic displacements
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re(r"Atomic Displacement Parameters \(A\*\*2\)"),
                                    gen_table_re("", "-+"), n_end=3):

            if Filters.THERMODYNAMICS not in to_parse:
                continue

            logger("Found atomic displacements")

            accum = _process_atom_disp(block)
            curr_run["atomic_displacements"] = accum

        # Thermodynamics
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Thermodynamics"),
                                    gen_table_re("", "-+"), n_end=3):

            if Filters.THERMODYNAMICS not in to_parse:
                continue

            logger("Found thermodynamics")

            accum = _process_thermodynamics(block)
            curr_run["thermodynamics"] = accum

        # Mulliken Population Analysis
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re(r"Atomic Populations \(Mulliken\)"),
                                    gen_table_re("", "=+"), n_end=2):

            if Filters.POPN_ANALYSIS not in to_parse:
                continue

            logger("Found Mulliken")

            curr_run["mulliken_popn"] = _process_mulliken(block)

        # Born charges
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Born Effective Charges"),
                                    gen_table_re("", "=+")):

            if Filters.POPN_ANALYSIS not in to_parse:
                continue

            logger("Found Born")

            curr_run["born"].append(_process_born(block))

        # Orbital populations
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Orbital Populations"),
                                    gen_table_re("", "-+"), n_end=3):

            if Filters.POPN_ANALYSIS not in to_parse:
                continue

            logger("Found Orbital populations")

            curr_run["orbital_popn"] = _process_orbital_populations(block)

        # Bond analysis
        elif block := Block.from_re(line, castep_file,
                                    r"Bond\s+Population(?:\s+Spin)?\s+Length",
                                    gen_table_re("", "=+"), n_end=2):

            if Filters.POPN_ANALYSIS not in to_parse:
                continue

            logger("Found bond info")

            curr_run["bonds"] = _process_bond_analysis(block)

        # Hirshfeld Population Analysis
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Hirshfeld Analysis"),
                                    gen_table_re("", "=+"), n_end=2):

            if Filters.POPN_ANALYSIS not in to_parse:
                continue

            logger("Found Hirshfeld")

            curr_run["hirshfeld"] = _process_hirshfeld(block)

        # ELF
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("ELF grid sample"),
                                    gen_table_re("", "-+"), n_end=2):

            if Filters.ELF not in to_parse:
                continue

            logger("Found ELF")

            curr_run["elf"] = _process_elf(block)

        # MD Block
        elif ((block := Block.from_re(line, castep_file,  # Capture general MD step
                                    "Starting MD iteration",
                                     "finished MD iteration")) or
              (block := Block.from_re(line, castep_file,  # Capture 0th iteration
                                     "Starting MD",
                                     gen_table_re("", "=+")))):

            if Filters.MD not in to_parse:
                continue

            logger("Found MD Block (step %d)", len(curr_run["md"]))

            # Avoid infinite recursion
            next(block)
            data = get_only(parse_castep_file(block))
            add_aliases(data, {"initial_positions": "positions",
                               "initial_cell": "cell"},
                        replace=True)

            # Put memory estimate to top level
            if "memory_estimate" in data:
                curr_run["memory_estimate"] = data.pop("memory_estimate")

            curr_run["md"].append(data)

        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("MD Data:", "x"),
                                    gen_table_re("", "x+")):

            if Filters.MD not in to_parse and Filters.MD_SUMMARY not in to_parse:
                continue

            curr_run.update(_process_md_block(block))

        # GeomOpt
        elif block := Block.from_re(line, castep_file, "Final Configuration",
                                    rf"\s*{REs.MINIMISERS_RE}: Final"):

            if Filters.GEOM_OPT not in to_parse and Filters.FINAL_CONFIG not in to_parse:
                continue

            logger("Found final geom configuration")

            curr_run["geom_opt"]["final_configuration"] = _process_final_config_block(block)

        elif block := Block.from_re(line, castep_file,
                                    rf"Starting {REs.MINIMISERS_RE} iteration\s*\d+\s*\.{{3}}",
                                    rf"^=+$|^\s*Finished\s+{REs.MINIMISERS_RE}\s*$", n_end=2):

            if Filters.GEOM_OPT not in to_parse:
                continue

            if "geom_opt" not in curr_run:
                curr_run["geom_opt"] = defaultdict(list)

            if not curr_run["geom_opt"]["iterations"]:
                data = {key: val for key, val in curr_run.items()
                        if key in ("enthalpy", "initial_cell", "initial_positions",
                                   "scf", "forces", "stresses", "minimisation")}

                for key in ("enthalpy", "scf", "forces", "stresses", "minimisation"):
                    if key in curr_run:
                        del curr_run[key]

                add_aliases(data, {"initial_positions": "positions",
                                   "initial_cell": "cell"},
                            replace=True)

                curr_run["geom_opt"]["iterations"] = [data]

            logger("Found geom block (iteration %d)", len(curr_run["geom_opt"]["iterations"])+1)
            # Avoid infinite recursion
            next(block)
            data = get_only(parse_castep_file(block))

            add_aliases(data, {"initial_positions": "positions",
                               "initial_cell": "cell"},
                        replace=True)
            curr_run["geom_opt"]["iterations"].append(data)

        elif match := re.search(f"(?P<minim>{REs.MINIMISERS_RE}):"
                                r" finished iteration\s*\d+\s*with enthalpy", line):

            if Filters.GEOM_OPT not in to_parse:
                continue

            minim = match["minim"]

            logger("Found %s energy", minim)

            curr_run["enthalpy"].append(to_type(get_numbers(line)[-1], float))

        elif match := re.search(rf"trial guess \(lambda=\s*({REs.EXPFNUMBER_RE})\)", line):

            if "geom_opt" not in curr_run:
                curr_run["geom_opt"] = defaultdict(list)

            curr_run["geom_opt"]["trial"].append(float(match.group(1)))

        elif match := re.match(rf"^\s*(?:{REs.MINIMISERS_RE}):\s*"
                               r"(?P<key>Final [^=]+)=\s*"
                               f"(?P<value>{REs.EXPFNUMBER_RE}).*",
                               line, re.IGNORECASE):

            if Filters.GEOM_OPT not in to_parse:
                continue

            key, val = normalise_string(match["key"]).lower(), to_type(match["value"], float)
            key = "_".join(key.split())
            logger("Found geomopt %s", key)
            curr_run["geom_opt"]["final_configuration"][key] = val

        elif block := Block.from_re(line, castep_file,
                                    f"<--( min)? {REs.MINIMISERS_RE}$",
                                    r"\+(?:-+\+){4,5}", n_end=2):

            if Filters.GEOM_OPT not in to_parse:
                continue

            if not (match := re.search(REs.MINIMISERS_RE, line)):
                raise ValueError("Invalid Geom block")

            typ = match.group(0)

            logger("Found %s geom_block", typ)

            curr_run["minimisation"].append(_process_geom_table(block))

        # TDDFT
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("TDDFT excitation energies", r"\+", post="TDDFT"),
                                    gen_table_re("=+", r"\+", post="TDDFT"), n_end=2):

            if Filters.TDDFT not in to_parse:
                continue

            logger("Found TDDFT excitations")

            curr_run["tddft"] = _process_tddft(block)

        # Band structure
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("(B A N D|Band Structure Calculation)[^+]+",
                                                 r"\+"),
                                    gen_table_re("", "=+")):

            if Filters.BS not in to_parse:
                continue

            logger("Found band-structure")

            curr_run["bs"] = _process_band_structure(block)

        # Molecular Dipole
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("D I P O L E   O F   M O L E C U L E"
                                                 "   I N   S U P E R C E L L",
                                                 r"\+"),
                                    gen_table_re("", "=+")):

            if Filters.DIPOLE not in to_parse:
                continue

            logger("Found molecular dipole")

            curr_run["molecular_dipole"] = _process_dipole(block)

        # Chemical shielding
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Chemical Shielding Tensor", r"\|"),
                                    gen_table_re("", "=+")):

            if Filters.CHEM_SHIELDING not in to_parse:
                continue

            logger("Found Chemical Shielding Tensor")

            val = _parse_magres_block(0, block)
            curr_run["magres"].append(val)

        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Chemical Shielding and "
                                                 "Electric Field Gradient Tensors", r"\|"),
                                    gen_table_re("", "=+")):

            if Filters.CHEM_SHIELDING not in to_parse:
                continue

            logger("Found Chemical Shielding + EField Tensor")

            val = _parse_magres_block(1, block)
            curr_run["magres"].append(val)

        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Electric Field Gradient Tensor", r"\|"),
                                    gen_table_re("", "=+")):

            if Filters.CHEM_SHIELDING not in to_parse:
                continue

            logger("Found EField Tensor")

            val = _parse_magres_block(2, block)
            curr_run["magres"].append(val)

        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("(?:I|Ani)sotropic J-coupling", r"\|"),
                                    gen_table_re("", "=+")):

            if Filters.CHEM_SHIELDING not in to_parse:
                continue

            logger("Found J-coupling")

            val = _parse_magres_block(3, block)
            curr_run["magres"].append(val)

        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Hyperfine Tensor", r"\|"),
                                    gen_table_re("", "=+")):

            if Filters.CHEM_SHIELDING not in to_parse:
                continue

            logger("Found Hyperfine tensor")

            val = _parse_magres_block(4, block)
            curr_run["magres"].append(val)

        # Elastic
        elif block := Block.from_re(line, castep_file,
                                    gen_table_re(r"Elastic Constants Tensor \(GPa\)"),
                                    gen_table_re("", "=+")):

            if Filters.ELASTIC not in to_parse:
                continue

            logger("Found elastic constants tensor")

            if "elastic" not in curr_run:
                curr_run["elastic"] = {}

            val, _ = _process_3_6_matrix(block, split=False)
            curr_run["elastic"]["elastic_constants"] = val

        elif block := Block.from_re(line, castep_file,
                                    gen_table_re(r"Compliance Matrix \(GPa\^-1\)"),
                                    gen_table_re("", "=+")):

            if Filters.ELASTIC not in to_parse:
                continue

            logger("Found compliance matrix")

            if "elastic" not in curr_run:
                curr_run["elastic"] = {}

            val, _ = _process_3_6_matrix(block, split=False)
            curr_run["elastic"]["compliance_matrix"] = val

        elif block := Block.from_re(line, castep_file, "Contribution ::", REs.EMPTY):

            if not (match := re.match("(?P<type>.* Contribution)", line)):
                raise ValueError("Invalid elastic block")

            typ = match.group("type")
            next(block)

            if Filters.ELASTIC not in to_parse:
                continue

            logger("Found elastic %s contribution", typ)

            if "elastic" not in curr_run:
                curr_run["elastic"] = {}

            val, _ = _process_3_6_matrix(block, split=False)
            curr_run["elastic"][typ] = val

        elif block := Block.from_re(line, castep_file,
                                    gen_table_re("Elastic Properties"),
                                    gen_table_re("", "=+")):

            if Filters.ELASTIC not in to_parse:
                continue

            logger("Found elastic properties")

            if "elastic" not in curr_run:
                curr_run["elastic"] = {}

            curr_run["elastic"].update(_process_elastic_properties(block))

        # --- Extra blocks for testing

        # Hugoniot data
        elif block := Block.from_re(line, castep_file, "BEGIN hug", "END hug"):

            if Filters.TEST_EXTRA_DATA not in to_parse:
                continue

            logger("Found hug block")

            val = parse_hug_file(block)
            curr_run["hug"].append(val)

        # Bands block (spectral data)
        elif block := Block.from_re(line, castep_file, "BEGIN bands", "END bands"):

            if Filters.TEST_EXTRA_DATA not in to_parse:
                continue

            logger("Found bands block")

            val = parse_bands_file(block)
            curr_run["bands"].append(val["bands"])

        elif block := Block.from_re(line, castep_file, "BEGIN phonon_dos", "END phonon_dos"):

            if Filters.TEST_EXTRA_DATA not in to_parse:
                continue

            logger("Found phonon_dos block")

            val = parse_phonon_dos_file(block)
            curr_run["phonon_dos"] = val["dos"]
            curr_run["gradients"] = val["gradients"]

        # E-Field
        elif block := Block.from_re(line, castep_file, "BEGIN efield", "END efield"):

            if Filters.TEST_EXTRA_DATA not in to_parse:
                continue

            logger("Found efield block")

            val = parse_efield_file(block)
            curr_run["oscillator_strengths"] = val["oscillator_strengths"]
            curr_run["permittivity"] = val["permittivity"]

        # Elastic
        elif block := Block.from_re(line, castep_file, "<BEGIN elastic>", "<END elastic>"):

            if Filters.TEST_EXTRA_DATA not in to_parse:
                continue

            logger("Found elastic block")

            val = parse_elastic_file(block)
            curr_run["oscillator_strengths"] = val["elastic_constants"]
            curr_run["permittivity"] = val["compliance_matrix"]

        # XRD Structure Factor
        elif block := Block.from_re(line, castep_file, "BEGIN xrd_sf", "END xrd_sf"):

            if Filters.TEST_EXTRA_DATA not in to_parse:
                continue

            logger("Found xrdsf")

            block = "\n".join(block[1:-1])  # Strip begin/end tags lazily
            block = io.StringIO(block)
            val = parse_xrd_sf_file(block)

            curr_run["xrd_sf"] = val

        # ELF FMT
        elif block := Block.from_re(line, castep_file, "BEGIN elf_fmt", "END elf_fmt"):

            if Filters.TEST_EXTRA_DATA not in to_parse:
                continue

            logger("Found ELF fmt")

            block = "\n".join(block[1:-1])  # Strip begin/end tags lazily
            block = io.StringIO(block)
            val = parse_elf_fmt_file(block)
            if "kpt-data" not in curr_run:
                curr_run["kpt-data"] = val
            else:
                curr_run["kpt-data"].update(val)

        # CHDIFF FMT
        elif block := Block.from_re(line, castep_file, "BEGIN chdiff_fmt", "END chdiff_fmt"):

            if Filters.TEST_EXTRA_DATA not in to_parse:
                continue

            logger("Found CHDIFF fmt")

            block = "\n".join(block[1:-1])  # Strip begin/end tags lazily
            block = io.StringIO(block)
            val = parse_chdiff_fmt_file(block)
            if "kpt-data" not in curr_run:
                curr_run["kpt-data"] = val
            else:
                curr_run["kpt-data"].update(val)

        # POT FMT
        elif block := Block.from_re(line, castep_file, "BEGIN pot_fmt", "END pot_fmt"):

            if Filters.TEST_EXTRA_DATA not in to_parse:
                continue

            logger("Found POT fmt")

            block = "\n".join(block[1:-1])  # Strip begin/end tags lazily
            block = io.StringIO(block)
            val = parse_pot_fmt_file(block)
            if "kpt-data" not in curr_run:
                curr_run["kpt-data"] = val
            else:
                curr_run["kpt-data"].update(val)

        # DEN FMT
        elif block := Block.from_re(line, castep_file, "BEGIN den_fmt", "END den_fmt"):

            if Filters.TEST_EXTRA_DATA not in to_parse:
                continue

            logger("Found DEN fmt")

            block = "\n".join(block[1:-1])  # Strip begin/end tags lazily
            block = io.StringIO(block)
            val = parse_den_fmt_file(block)
            if "kpt-data" not in curr_run:
                curr_run["kpt-data"] = val
            else:
                curr_run["kpt-data"].update(val)

    if curr_run:
        fix_data_types(curr_run, {"energies": float,
                                  "solvation": float})
        runs.append(curr_run)
    return runs


def _process_ps_energy(block: Block) -> tuple[str, PSPotEnergy]:
    if not (match := REs.PS_SHELL_RE.search(next(block))):
        raise ValueError("Invalid PS Energy")

    key = match["spec"]
    accum: PSPotEnergy = defaultdict(list)

    next(block)
    accum["pseudo_atomic_energy"] = float(get_numbers(next(block))[1])
    for line in block:
        if "Charge spilling" in line:
            assert isinstance(accum["charge_spilling"], list)
            accum["charge_spilling"].append(0.01*float(get_numbers(line)[-1]))

    if "charge_spilling" in accum:
        accum["charge_spilling"] = tuple(accum["charge_spilling"])

    return key, accum


def _process_tddft(block: Block) -> list[TDDFTData]:
    return [
        {"energy": float(match["energy"]),
         "error": float(match["error"]),
         "type": match["type"]}
        for line in block
        if (match := REs.TDDFT_RE.match(line))
    ]


def _process_atreg_block(block: Block) -> AtomPropBlock:
    return {
        atreg_to_index(match): to_type(match.group("x", "y", "z"), float)
        for line in block
        if (match := REs.ATOMIC_DATA_3VEC.search(line))
    }



def _process_spec_prop(block: Block) -> list[list[str]]:

    accum = []

    for line in block:
        words = line.split()
        if words and re.match(rf"{REs.SPECIES_RE}\b", words[0]):

            accum.append(words)

    return accum


def _process_md_block(block: Block) -> MDInfo:
    curr_data = {match.group("key").strip(): float(match.group("val"))
                 for line in block
                 if (match := re.search(r"x\s+"
                                        r"(?P<key>[a-zA-Z][A-Za-z ]+):\s*"
                                        rf"(?P<val>{REs.FNUMBER_RE})", line))}

    return {normalise_key(key): val for key, val in curr_data.items()}


def _process_elf(block: Block) -> list[float]:
    return [
        float(match.group(1)) for line in block
        if (match := re.match(rf"\s+ELF\s+\d+\s+({REs.FNUMBER_RE})", line))
    ]


def _process_hirshfeld(block: Block) -> dict[AtomIndex, float]:
    """Process Hirshfeld block to dict of charges."""
    return {
        atreg_to_index(match): float(match["charge"]) for line in block
        if (match := re.match(rf"\s+{REs.ATOM_RE}\s+(?P<charge>{REs.FNUMBER_RE})", line))
    }


def _process_thermodynamics(block: Block) -> Thermodynamics:
    """Process a thermodynamics block into a dict of lists."""
    accum: Thermodynamics = defaultdict(list)
    for line in block:
        if "Zero-point energy" in line:
            accum["zero_point_energy"] = float(get_numbers(line)[0])

        if match := REs.THERMODYNAMICS_DATA_RE.match(line):
            stack_dict(accum, match.groupdict())

        # elif re.match(r"\s+T\(", line):  # Can make dict/re based on labels
        #     thermo_label = line.split()

    fix_data_types(accum, {key: float for
                           key in ("t", "e", "f", "s", "cv")})
    return accum


def _process_atom_disp(block: Block) -> dict[str, dict[AtomIndex, SixVector]]:
    """Process a atom disp block into a dict of lists."""
    accum: dict[str, dict[AtomIndex, SixVector]] = defaultdict(dict)
    for line in block:
        if match := REs.ATOMIC_DISP_RE.match(line):
            ind = atreg_to_index(match.groupdict())
            temp, disp = match["temperature"], match["displacement"]
            val = to_type(disp.split(), float)
            accum[temp][ind] = val

    return accum


def _process_3_6_matrix(
        block: Block, *, split: bool,
) -> tuple[ThreeByThreeMatrix, ThreeByThreeMatrix | None]:
    """Process a single or pair of 3x3 matrices or 3x6 matrix."""
    parsed = tuple(to_type(vals, float) for line in block
                   if (vals := get_numbers(line)) and len(vals) in (3, 6))

    if split and len(parsed[0]) == 6:
        fst = cast(ThreeByThreeMatrix, tuple(line[0:3] for line in parsed))
        snd = cast(ThreeByThreeMatrix, tuple(line[3:6] for line in parsed))
    else:
        fst = cast(ThreeByThreeMatrix, parsed)
        snd = None

    return fst, snd


def _process_params(block: Block) -> dict[str, dict[str, str | tuple[Any, ...]]]:
    """Process a parameters block into a dict of params."""
    opt: dict[str, Any] = {}
    curr_opt: dict[str, str | tuple[Any, ...]] = {}
    curr_group = ""

    match: re.Match | list[str] | None
    key: str | list[str]
    val: Any

    for line in block:
        if dev_block := Block.from_re(line, block, "Developer Code", gen_table_re("", r"\*+")):

            opt["devel_code"] = _parse_devel_code_block(dev_block)

        elif match := re.match(r"\s*\*+ ([A-Za-z -]+) \*+", line):
            if curr_opt:
                opt[curr_group] = curr_opt

            curr_group = normalise_string(match.group(1).replace("Parameters", "")).lower()
            curr_opt = {}

        elif match := re.match(r"\s*output (?P<key>.*) unit\s*:\s*(?P<val>.*)", line):

            if "output_units" not in opt:
                opt["output_units"] = {}

            key, val = map(normalise_string, match.group("key", "val"))
            opt["output_units"][key] = val

        elif len(match := line.split(":")) > 1:
            *key, val = map(normalise_string, match)
            if val.split() and REs.NUMBER_RE.match(val.split()[0]):
                val, *unit = val.split()
                val = to_type(val, determine_type(val))
                if unit:
                    val = (val, *unit)

            curr_opt[" ".join(key).strip()] = val

    if curr_opt:
        opt[curr_group] = curr_opt

    return opt


def _process_buildinfo(block: Block) -> dict[str, str]:
    info = {}

    info["summary"] = " ".join(map(normalise_string, block[0:2]))
    for line in block[2:]:
        if ":" in line:
            key, val = map(normalise_string, line.split(":", 1))
            info[normalise_key(key)] = val.strip()
    return info


def _process_unit_cell(block: Block) -> CellInfo:
    cell: CellInfo = defaultdict(list)
    prop = []

    assert isinstance(cell["real_lattice"], list)
    assert isinstance(cell["recip_lattice"], list)
    assert isinstance(cell["lattice_parameters"], list)
    assert isinstance(cell["cell_angles"], list)

    for line in block:
        numbers = get_numbers(line)
        if len(numbers) == 6:
            cell["real_lattice"].append(to_type(numbers[0:3], float))
            cell["recip_lattice"].append(to_type(numbers[3:6], float))
        elif len(numbers) == 2:
            if any(ang in line for ang in ("alpha", "beta", "gamma")):
                cell["lattice_parameters"].append(to_type(numbers[0], float))
                cell["cell_angles"].append(to_type(numbers[1], float))
            else:
                prop.append(float(numbers[0]))

    cell.update({name: val for val, name in zip(prop, ("volume", "density_amu", "density_g"))})

    return cell


def _process_scf(block: Block) -> list[SCFReport]:
    scf = []
    curr: SCFReport = {}
    debug_info: SCFDebugInfo = {}
    for line in block:
        if match := REs.SCF_LOOP_RE.match(line):
            if curr:
                scf.append(curr)

            curr = match.groupdict()
            if debug_info:  # Debug info refers to next cycle
                curr["debug_info"] = debug_info
            debug_info = {}
            fix_data_types(curr, {"energy": float,
                                  "energy_gain": float,
                                  "fermi_energy": float,
                                  "time": float})

        elif "Density was not mixed" in line:
            curr["density_residual"] = None

        elif "Norm of density" in line:
            curr["density_residual"] = to_type(get_numbers(line)[0], float)

        elif "constraint energy" in line:
            curr["constraint_energy"] = to_type(get_numbers(line)[0], float)

        elif "Correcting PBC dipole-dipole" in line:
            curr["dipole_corr_energy"] = to_type(get_numbers(line)[0], float)

        # Debug info

        elif "no. bands" in line:
            debug_info["no_bands"] = to_type(get_numbers(line)[0], int)

        elif "Kinetic eigenvalue" in line:
            debug_info.setdefault("kinetic_eigenvalue", [])
            debug_info.setdefault("eigenvalue", [])

            debug_info["kinetic_eigenvalue"].append(to_type(get_numbers(line)[1], float))
            eig = []

        elif re.match(r"eigenvalue\s*\d+\s*init=", line):
            numbers = get_numbers(line)
            eig.append({"initial": float(numbers[1]),
                        "final": float(numbers[2]),
                        "change": float(numbers[3])})

        elif "Checking convergence criteria" in line:
            debug_info["eigenvalue"].append(eig)
            eig = []

        elif match := re.match(r"[+(]?(?P<key>[()0-9A-Za-z -]+)=?"
                               rf"\s*{labelled_floats(('val',))} eV\)?", line):
            debug_info.setdefault("contributions", {})
            key, val = normalise_key(match["key"]), float(match["val"])

            fix_keys = {"apolar_corr_to_eigenvalue_sum": "apolar_correction",
                        "hubbard_u_correction_to_eigenvalu": "hubbard_u_correction",
                        "xc_correction_to_eigenvalue_sum": "xc_correction"}
            key = fix_keys.get(key, key)

            debug_info["contributions"][key] = val

    if curr:
        scf.append(curr)

    return scf


def _process_forces(block: Block) -> tuple[str, AtomPropBlock]:
    if not (ft_guess := REs.FORCES_BLOCK_RE.search(next(block))):
        raise ValueError("Invalid forces block")
    ftype = ft_guess.group(1) if ft_guess.group(1) else "non_descript"
    ftype = normalise_key(ftype)

    accum = {atreg_to_index(match): to_type(match.group("x", "y", "z"), float)
             for line in block
             if (match := REs.ATOMIC_DATA_FORCE.search(line))}

    return ftype, accum


def _process_stresses(block: Block) -> tuple[str, SixVector]:
    if not (ft_guess := REs.STRESSES_BLOCK_RE.search(next(block))):
        raise ValueError("Invalid stresses block")
    ftype = ft_guess.group(1) if ft_guess.group(1) else "non_descript"
    ftype = normalise_key(ftype)

    accum = []
    for line in block:
        numbers = get_numbers(line)
        if "*  x" in line:
            accum += numbers[0:]
        elif "*  y" in line:
            accum += numbers[1:]
        elif "*  z" in line:
            accum += numbers[2:]

    return ftype, to_type(accum, float)


def _process_initial_spins(block: Block) -> dict[AtomIndex, InitialSpin]:
    """Process a set of initial spins into appropriate dict."""
    accum: dict[AtomIndex, InitialSpin] = {}
    for line in block:
        if match := re.match(rf"\s*\|\s*{REs.ATOM_RE}\s*"
                             rf"{labelled_floats(('spin', 'magmom'))}\s*"
                             r"(?P<fix>[TF])\s*\|", line):
            val = match.groupdict()
            ind = atreg_to_index(val)
            fix_data_types(val, {"spin": float, "magmom": float})
            val["fix"] = val["fix"] == "T"
            accum[ind] = cast(Dict[str, Union[float, bool]], val)
    return accum


def _process_born(block: Block) -> dict[AtomIndex, ThreeByThreeMatrix]:
    """Process a Born block into a dict of charges."""
    born_accum = {}
    for line in block:
        if match := REs.BORN_RE.match(line):
            val = match.groupdict()
            label = val.pop("label")
            if label is not None:
                val["spec"] = f"{val['spec']} [{label}]"

            born_accum[atreg_to_index(val)] = (to_type(val["charges"].split(), float),
                                               to_type(next(block).split(), float),
                                               to_type(next(block).split(), float))
    return born_accum


def _process_raman(block: Block) -> list[RamanReport]:
    """Process a Mulliken block into a list of modes."""
    next(block)  # Skip first captured line
    modes = []
    curr_mode: RamanReport = {}
    for line in block:
        if "Mode number" in line:
            if curr_mode:
                modes.append(curr_mode)

            curr_mode = {"tensor": [], "depolarisation": None}
        elif numbers := get_numbers(line):
            assert isinstance(curr_mode["tensor"], list)
            curr_mode["tensor"].append(to_type(numbers[0:3], float))
            if len(numbers) == 4:
                curr_mode["depolarisation"] = float(numbers[3])

        elif re.search(r"^ \+\s+\+", line):  # End of 3x3+depol block
            # Compute Invariants Tr(A) and Tr(A)^2-Tr(A^2) of Raman Tensor
            assert isinstance(curr_mode["tensor"], list)
            tensor = curr_mode["tensor"]
            curr_mode["tensor"] = cast(ThreeByThreeMatrix, tuple(curr_mode["tensor"]))
            curr_mode["trace"] = sum(tensor[i][i] for i in range(3))
            curr_mode["ii"] = (tensor[0][0]*tensor[1][1] +
                               tensor[0][0]*tensor[2][2] +
                               tensor[1][1]*tensor[2][2] -
                               tensor[0][1]*tensor[1][0] -
                               tensor[0][2]*tensor[2][0] -
                               tensor[1][2]*tensor[2][1])
    if curr_mode:
        modes.append(curr_mode)

    return modes


def _process_mulliken(block: Block) -> dict[AtomIndex, MullikenInfo]:
    """Process a mulliken block into a dict of points."""
    accum = {}

    for line in block:
        if match := REs.POPN_RE.match(line):
            mull = match.groupdict()
            mull["spin_sep"] = bool(mull["spin_sep"])
            if mull["spin_sep"]:  # We have spin separation
                add_aliases(mull,
                            {orb: f"up_{orb}" for orb in (*SHELLS, "total")},
                            replace=True)
                line = next(block)
                if not (match := REs.POPN_RE_DN.match(line)):
                    raise ValueError("Invalid mulliken down spin")
                val = match.groupdict()

                add_aliases(val,
                            {orb: f"dn_{orb}" for orb in (*SHELLS, "total")},
                            replace=True)

                mull.update(val)
                mull["total"] = float(mull["up_total"]) + float(mull["dn_total"])

            ind = atreg_to_index(mull)
            fix_data_types(mull, {**{f"{orb}": float for orb in (*SHELLS, "total",
                                                                 "charge", "spin")},
                                  **{f"up_{orb}": float for orb in (*SHELLS, "total")},
                                  **{f"dn_{orb}": float for orb in (*SHELLS, "total")}})
            accum[ind] = mull

    return accum


def _process_band_structure(block: Block) -> list[BandStructure]:
    """Process a band structure into a list of kpts."""

    def fdt(qdat):
        fix_data_types(qdat, {"spin": int,
                              "kx": float,
                              "ky": float,
                              "kz": float,
                              "kpgrp": int,
                              "band": int,
                              "energy": float})

    bands = []
    qdata: BandStructure = {}

    for line in block:
        if match := REs.BS_RE.search(line):
            if qdata:
                fdt(qdata)
                bands.append(qdata)

            qdata = {"band": [], "energy": [], **match.groupdict()}

        elif match := re.search(labelled_floats(("band", "energy"), sep=r"\s+"), line):
            stack_dict(qdata, match.groupdict())

    if qdata:
        fdt(qdata)
        bands.append(qdata)

    return bands


def _process_qdata(qdata: dict[str, str | list[str]]) -> QData:
    """Parse phonon qdata into components."""
    qdata = {key: val
             for key, val in qdata.items()
             if any(val) or key == "qpt"}
    fix_data_types(qdata,
                   {"qpt": float,
                    "N": int,
                    "frequency": float,
                    "intensity": float,
                    "raman_intensity": float,
                    })
    return cast(QData, qdata)


def _parse_magres_block(task: int, inp: Block) -> dict[str | AtomIndex,
                                                       str | dict[str, float | None]]:
    """Parse MagRes data tables from inp according to task."""
    data: dict[str | AtomIndex, str | dict[str, float | None]] = {}
    data["task"] = REs.MAGRES_TASK[task]
    curr_re = REs.MAGRES_RE[task]
    for line in inp:
        if match := curr_re.match(line):
            tmp = match.groupdict()
            ind = atreg_to_index(tmp)

            val: dict[str, float | None] = {key: float(val)
                                               for key, val in tmp.items() if key != "asym"}
            if "asym" in tmp:
                val["asym"] = float(tmp["asym"]) if tmp["asym"] != "N/A" else None

            data[ind] = val

    return data


def _process_finalisation(block: Block) -> dict[str, float]:

    out = {}

    for line in block:
        if line.strip():
            key, val = line.split("=")
            out[normalise_key(key)] = float(get_numbers(val)[0])
    return out


def _process_memory_est(block: Block) -> dict[str, MemoryEst]:

    accum = {}

    for line in block:
        if match := re.match(r"\s*\|([A-Za-z ]+)" +
                             labelled_floats(("memory", "disk"), suffix=" MB"), line):
            key, memory, disk = match.groups()
            accum[normalise_key(key)] = {"memory": float(memory),
                                         "disk": float(disk)}

    return accum


def _process_phonon_sym_analysis(block: Block) -> PhononSymmetryReport:
    accum: PhononSymmetryReport = {"title": "", "mat": ()}
    accum["title"] = normalise_string(next(block).split(":")[1])
    next(block)
    accum["mat"] = tuple(parse_int_or_float(numbers)
                         for line in block
                         if (numbers := get_numbers(line)))
    return accum


def _process_kpoint_blocks(block: Block, *,
                           implicit_kpoints: bool) -> KPointsList | KPointsSpec:

    if implicit_kpoints:
        accum: KPointsSpec = {}
        for line in block:
            if "MP grid size" in line:
                accum["kpoint_mp_grid"] = to_type(get_numbers(line), int)
            elif "offset" in line:
                accum["kpoint_mp_offset"] = to_type(get_numbers(line), float)
            elif "Number of kpoints" in line:
                accum["num_kpoints"] = to_type(get_numbers(line)[0], int)
    else:
        kp_block_re = re.compile(gen_table_re(r"\d\s*" + labelled_floats(("qx", "qy", "qz", "wt")),
                                              r"\+"))
        accum: KPointsList = {"points": [{"qpt": to_type(match.group("qx", "qy", "qx"), float),
                                          "weight": to_type(match["wt"], float)}
                                         for line in block
                                         if (match := kp_block_re.match(line))]}
        assert isinstance(accum["points"], list)
        accum["num_kpoints"] = len(accum["points"])

    return accum


def _process_symmetry(block: Block) -> tuple[SymmetryReport, ConstraintsReport]:

    sym: dict[str, Any] = {}
    con: dict[str, Any] = {}
    val: Any

    for line in block:
        if "=" in line:
            key, val = line.split("=")
            key = normalise_key(key)
            val = normalise_string(val)

            if "Number of" in line:
                val = to_type(val, int)

            if "constraints" in key:
                con[key] = val
            else:
                sym[key] = val

        elif re.match(r"\s*\d+\s*rotation\s*", line):
            if "symop" not in sym:
                sym["symop"] = []

            curr_sym: dict[str, Any] = {"rotation": [], "symmetry_related": []}
            for curr_ln in itertools.islice(block, 3):
                curr_sym["rotation"].append(to_type(get_numbers(curr_ln), float))

            next(block)  # elif re.match(r"\s*\d+\s*displacement\s*", line):

            curr_sym["displacement"] = to_type(get_numbers(next(block)), float)

            next(block)  # elif "symmetry related atoms:" in line:

            while line := next(block).strip():
                key, val = line.split(":")
                curr_sym["symmetry_related"].extend((key, int(ind))
                                                    for ind in val.split())

            sym["symop"].append(curr_sym)

        elif "Cell is a supercell containing" in line:

            sym["n_primitives"] = to_type(get_numbers(line)[0], int)

        elif "Centre of mass" in line:
            con["com_constrained"] = "NOT" not in line

        elif cons_block := Block.from_re(line, block, r"constraints\.{5}", r"\s*x+\.{4}\s*"):
            con["ionic_constraints"] = defaultdict(list)
            for match in re.finditer(rf"{REs.ATOM_RE}\s*[xyz]\s*" +
                                     labelled_floats(("pos",), counts=(3,)),
                                     str(cons_block)):
                val = match.groupdict()
                ind = atreg_to_index(val)
                con["ionic_constraints"][ind].append(to_type(val["pos"].split(), float))

        elif "Cell constraints are:" in line:
            con["cell_constraints"] = to_type(get_numbers(line), int)

    return sym, con


def _process_dynamical_matrix(block: Block) -> tuple[tuple[complex, ...], ...]:
    next(block)  # Skip header line
    next(block)

    real_part = []
    while (line := next(block)) and "Ion" not in line:
        numbers = get_numbers(line)
        real_part.append(numbers[2:])

    # Get remainder
    imag_part = [numbers[2:] for line in block if (numbers := get_numbers(line))]

    return tuple(
        tuple(complex(float(real), float(imag)) for real, imag in zip(real_row, imag_row))
        for real_row, imag_row in zip(real_part, imag_part)
    )


def _process_pspot_string(string: str, *, debug=False) -> PSPotStrInfo:
    if not (match := REs.PSPOT_RE.search(string)):
        raise ValueError(f"Attempt to parse {string} as PSPot failed")

    pspot = match.groupdict()
    projectors = []

    for proj in pspot["proj"].split(":"):
        if match := REs.PSPOT_PROJ_RE.match(proj):
            pdict = dict(zip(REs.PSPOT_PROJ_GROUPS, match.groups()))
        else:
            raise ValueError("Invalid PSPot string")

        pdict["shell"] = SHELLS[int(pdict["shell"])]

        if not pdict["type"]:
            pdict["type"] = None

        for prop in ("beta_delta", "de"):
            if not pdict[prop]:
                del pdict[prop]

        fix_data_types(pdict, {"orbital": int,
                               "beta_delta": float,
                               "de": float})
        projectors.append(pdict)

    for prop in ("shell_swp", "shell_swp_end", "opt"):
        if pspot[prop]:
            pspot[prop] = pspot[prop].split(",")

    pspot["projectors"] = tuple(projectors)
    pspot["string"] = string
    pspot["print"] = bool(pspot["print"])

    if not debug:
        for prop in ("shell_swp", "shell_swp_end", "local_energy",
                     "poly_fit", "beta_radius", "r_inner", "debug"):
            if pspot[prop] is None:
                del pspot[prop]

    fix_data_types(pspot, {"beta_radius": float,
                           "r_inner": float,
                           "core_radius": float,
                           "coarse": float,
                           "medium": float,
                           "fine": float,
                           "local_channel": int,
                           })

    return pspot


def _process_pspot_report(block: Block) -> PSPotReport:

    accum: PSPotReport = {"reference_electronic_structure": [],
                          "pseudopotential_definition": []}

    for line in block:
        if match := REs.PSPOT_REFERENCE_STRUC_RE.match(line):
            val = match.groupdict()
            fix_data_types(val, {"occupation": float, "energy": float})
            accum["reference_electronic_structure"].append(val)
        elif match := REs.PSPOT_DEF_RE.match(line):
            val = match.groupdict()
            # Account for "loc"
            val["beta"] = int(val["beta"]) if val["beta"].isnumeric() else val["beta"]
            fix_data_types(val, {"l": int, "j": int,
                                 "e": float, "Rc": float, "norm": int})
            accum["pseudopotential_definition"].append(val)
        elif match := re.search(rf"Element: (?P<element>{REs.SPECIES_RE})\s+"
                                rf"Ionic charge: (?P<ionic_charge>{REs.FNUMBER_RE})\s+"
                                r"Level of theory: (?P<level_of_theory>[\w\d]+)", line):
            val = match.groupdict()
            val["ionic_charge"] = float(val["ionic_charge"])
            accum.update(val)

        elif match := re.search(r"Atomic Solver:\s*(?P<solver>[\w\s-]+)", line):
            accum["solver"] = normalise_string(match["solver"])

        elif match := REs.PSPOT_RE.search(line):
            accum["detail"] = _process_pspot_string(match.group(0))

        elif "Augmentation charge Rinner" in line:
            accum["augmentation_charge_rinner"] = to_type(get_numbers(line), float)

        elif "Partial core correction Rc" in line:
            accum["partial_core_correction"] = to_type(get_numbers(line), float)

    return accum


def _process_bond_analysis(block: Block) -> BondData:
    accum = {((match["spec1"], int(match["ind1"])),
              (match["spec2"], int(match["ind2"]))):
             {"population": float(match["population"]),
              "spin": float(match["spin"]) if match["spin"] else None,
              "length": float(match["length"])}
             for line in block
             if (match := REs.BOND_RE.match(line))}

    for val in accum.values():
        if not val["spin"]:
            del val["spin"]

    return accum


def _process_orbital_populations(block: Block) -> dict[str | AtomIndex, Any]:

    accum: dict[str | AtomIndex, Any] = defaultdict(dict)
    for line in block:
        if match := REs.ORBITAL_POPN_RE.match(line):
            val = match.groupdict()
            ind = atreg_to_index(val)
            accum[ind][val["orb"]] = to_type(val["charge"], float)
        elif match := re.match(rf"\s*Total:\s*{labelled_floats(('charge',))}", line):
            accum["total"] = float(match["charge"])
        elif "total projected" in line:
            accum["total_projected"] = to_type(get_numbers(line), float)

    return accum


def _process_dftd(block: Block) -> dict[str, Any]:
    dftd: dict[str, Any] = {"species": {}}
    match: list[str] | re.Match | None
    val: Any

    for line in block:
        if len(match := line.split(":")) == 2:
            key, val = match
            val = normalise_string(val)
            if "Parameter" in key:
                val = to_type(get_numbers(val)[0], float)

            dftd[normalise_key(key)] = val

        elif match := re.match(rf"\s*x\s*(?P<spec>{REs.ATOM_NAME_RE})\s*" +
                               labelled_floats(("C6", "R0")), line):
            dftd["species"][match["spec"]] = {"c6": float(match["C6"]),
                                              "r0": float(match["R0"])}

    return dftd


def _process_occupancies(block: Block) -> list[Occupancies]:
    label = ("band", "eigenvalue", "occupancy")

    accum = [dict(zip(label, numbers)) for line in block if (numbers := get_numbers(line))]
    for elem in accum:
        fix_data_types(elem, {"band": int,
                              "eigenvalue": float,
                              "occupancy": float})
    return cast(List[Occupancies], accum)


def _process_wvfn_line_min(block: Block) -> WvfnLineMin:
    accum: WvfnLineMin = {}
    for line in block:
        if "initial" in line:
            accum["init_energy"], accum["init_de_dstep"] = to_type(get_numbers(line), float)
        elif line.strip().startswith("| step"):
            accum["steps"] = to_type(get_numbers(line), float)
        elif line.strip().startswith("| gain"):
            accum["gain"] = to_type(get_numbers(line), float)

    return accum


def _process_autosolvation(block: Block) -> dict[str, float]:

    accum = {}
    for line in block:
        if len(match := line.split("=")) > 1:
            key = normalise_key(match[0])
            val = cast(float, to_type(get_numbers(line)[0], float))
            accum[key] = val

    return accum


def _process_phonon(block: Block, logger) -> list[QData]:
    qdata: dict[str, Any] = defaultdict(list)
    accum: list[QData] = []

    for line in block:
        if match := REs.PHONON_RE.match(line):
            if qdata["qpt"] and qdata["qpt"] not in (phonon["qpt"]
                                                     for phonon in accum):
                accum.append(_process_qdata(qdata))

            qdata = defaultdict(list)
            qdata["qpt"] = match["qpt"].split()

            logger("Reading qpt %s", qdata["qpt"], level="debug")

        elif match := REs.PROCESS_PHONON_RE.match(line):
            # ==By mode
            # qdata["modes"].append(match.groupdict())
            # ==By prop
            stack_dict(qdata, match.groupdict())

        elif char_table := Block.from_re(line, block,
                                         r"Rep\s+Mul", gen_table_re("[-=]+", r"\+"),
                                         eof_possible=True):
            headers = next(char_table).split()[4:]
            next(char_table)
            char: list[CharTable] = []
            for char_line in char_table:
                if re.search("[-=]{4,}", char_line):
                    break

                head, tail = char_line.split("|")
                _, rep, *name, mul = head.split()
                *vals, _ = tail.split()
                char.append({"chars": tuple(zip(headers, map(int, vals))),
                             "mul": int(mul),
                             "rep": rep,
                             "name": name})

            for row in char:
                if not row["name"]:
                    del row["name"]
                else:
                    row["name"] = row["name"][0]

            qdata["char_table"] = char

    if qdata["qpt"] and qdata["qpt"] not in (phonon["qpt"] for phonon in accum):
        accum.append(_process_qdata(qdata))

    return accum


def _process_dipole(block: Block) -> DipoleTable:

    accum: DipoleTable = {}

    for line in block:
        if match := re.search(r"Total\s*(?P<type>\w+)", line):
            accum[f"total_{match['type']}"] = float(get_numbers(line)[0])

        elif "Centre" in line:
            key = "centre_electronic" if "elec" in line else "centre_positive"
            accum[key] = cast(ThreeVector, to_type(get_numbers(next(block)), float))

        elif "Magnitude" in line:
            accum["dipole_magnitude"] = cast(float, to_type(get_numbers(line)[0], float))

        elif "Direction" in line:
            accum["dipole_direction"] = cast(ThreeVector, to_type(get_numbers(line), float))

    return accum


def _process_pair_params(block_in: Block) -> dict[str, dict[str, dict | str]]:

    accum: dict[str, Any] = {}
    for line in block_in:
        # Two-body
        if block := Block.from_re(line, block_in, "Two Body", r"^\w*\s*\*+\s*$"):
            for blk_line in block:
                if REs.PAIR_POT_RES["two_body_spec"].search(blk_line):
                    matches = REs.PAIR_POT_RES["two_body_spec"].finditer(blk_line)
                    labels = tuple(match.groups() for match in matches)

                elif match := REs.PAIR_POT_RES["two_body_val"].match(blk_line):
                    tag, typ, lab = match.group("tag", "type", "label")
                    if tag:
                        typ = f"{tag}_{typ}"
                    if typ not in accum:
                        accum[typ] = {}
                    if lab not in accum[typ]:
                        accum[typ][lab] = {}

                    accum[typ][lab].update(zip(labels,
                                               to_type(match["params"].split(),
                                                       float)))

                elif match := REs.PAIR_POT_RES["two_body_one_spec"].match(blk_line):
                    labels = ((match["spec"],),)

        # Three-body
        elif block := Block.from_re(line, block_in, "Three Body", r"^\s*\*+\s*$"):
            for blk_line in block:
                if match := REs.PAIR_POT_RES["three_body_spec"].match(blk_line):
                    labels = (tuple(match["spec"].split()),)

                elif match := REs.PAIR_POT_RES["three_body_val"].match(blk_line):
                    tag, typ, lab = match.group("tag", "type", "label")

                    if tag:
                        typ = f"{tag}_{typ}"
                    if typ not in accum:
                        accum[typ] = {}
                    if lab not in accum[typ]:
                        accum[typ][lab] = {}

                    accum[typ][lab].update(zip(labels,
                                               to_type(match["params"].split(),
                                                       float)))

        # Globals
        elif match := REs.PAIR_POT_RES["three_body_val"].match(line):
            tag, typ, lab = match.group("tag", "type", "label")

            if tag:
                typ = f"{tag}_{typ}"
            if typ not in accum:
                accum[typ] = {}

            accum[typ][lab] = to_type(match["params"], float)

    return accum


def _process_geom_table(block: Block) -> GeomTable:

    accum: GeomTable = {}
    for line in block:
        if match := REs.GEOMOPT_MIN_TABLE_RE.match(line):
            val = match.groupdict()
            fix_data_types(val, {key: float for key in ("lambda", "fdelta", "enthalpy")})

            key = normalise_string(val.pop("step"))
            accum[key] = cast(Dict[str, Union[bool, float]], val)

        elif match := REs.GEOMOPT_TABLE_RE.match(line):
            val = match.groupdict()
            fix_data_types(val, {key: float for key in ("value", "tolerance")})

            val["converged"] = val["converged"] == "Yes"

            key = normalise_key(val.pop("parameter"))
            accum[key] = cast(Dict[str, Union[bool, float]], val)

    return accum


def _process_final_config_block(block_in: Block) -> FinalConfig:

    accum: dict[str, Any] = {}
    for line in block_in:
        if block := Block.from_re(line, block_in, r"\s*Unit Cell\s*", REs.EMPTY, n_end=3):
            accum["cell"] = _process_unit_cell(block)

        elif block := Block.from_re(line, block_in,
                                    gen_table_re("Cell Contents"),
                                    gen_table_re("", "x+"), n_end=2):
            accum["atoms"] = _process_atreg_block(block)

        elif match := re.match(rf"^\s*(?:{REs.MINIMISERS_RE}):"
                               r"(?P<key>[^=]+)=\s*"
                               f"(?P<value>{REs.EXPFNUMBER_RE}).*",
                               line, re.IGNORECASE):

            key, val = normalise_key(match["key"]), to_type(match["value"], float)
            accum[key] = val

    return accum


def _process_elastic_properties(block: Block) -> ElasticProperties:
    accum: dict[str, float | ThreeVector | SixVector | ThreeByThreeMatrix] = {}
    val: float | ThreeVector | SixVector | ThreeByThreeMatrix | tuple[float, ...]

    for line in block:
        if "::" in line:
            key = line.split("::")[0]
            val = cast(Union[ThreeVector, SixVector], to_type(get_numbers(line), float))

            if len(val) == 1:
                val = val[0]

            accum[normalise_key(key)] = val
        elif blk := Block.from_re(line, block, "Speed of Sound", REs.EMPTY):

            accum["speed_of_sound"] = cast(ThreeByThreeMatrix,
                                           tuple(to_type(numbers, float)
                                                 for blk_line in blk
                                                 if (numbers := get_numbers(blk_line))),
                                           )

    return accum
