# pylint: disable=too-many-lines, too-many-branches, too-many-statements
"""
Extract results from .castep file for comparison and use
by testcode.pl.

Port of extract_results.pl
"""

from collections import defaultdict
import io
import re
import itertools

from .utility import (EXPNUMBER_RE, FNUMBER_RE, INTNUMBER_RE, SHELL_RE,
                      ATREG, ATOM_NAME_RE, SPECIES_RE, ATDAT3VEC, SHELLS, MINIMISERS,
                      labelled_floats, fix_data_types, add_aliases, to_type,
                      stack_dict, get_block, get_numbers, normalise_string, atreg_to_index)
from .parse_extra_files import (parse_bands_file, parse_hug_file, parse_phonon_dos_file,
                                parse_efield_file, parse_xrd_sf_file, parse_elf_fmt_file,
                                parse_chdiff_fmt_file, parse_pot_fmt_file, parse_den_fmt_file)


# SCF Loop
_SCF_LOOP_RE = re.compile(r"\s*(?:Initial|\d+)\s*"
                          rf"{labelled_floats(('energy', 'fermi_energy', 'energy_gain'))}?\s*"
                          f"{labelled_floats(('time',))}")

# PS Energy
_PS_SHELL_RE = re.compile(
    rf"\s*Pseudo atomic calculation performed for (?P<spec>{SPECIES_RE})(\s+{SHELL_RE})+")

# PS Projector
_PSPOT_PROJ_RE = re.compile(r"(?P<orbital>\d)(?P<shell>\d)(?P<type>U|UU|N)?")
_UNLABELLED_PROJ_RE = r"\d\d(?:UU|U|N)?"


# PSPot String
_PSPOT_RE = re.compile(labelled_floats(("local_channel",
                                        "core_radius",
                                        "beta_radius",
                                        "r_inner",
                                        "coarse",
                                        "medium",
                                        "fine"), sep=r"\|?")
                       +
                       r"\|"
                       rf"(?P<proj>{_UNLABELLED_PROJ_RE}(?::{_UNLABELLED_PROJ_RE})*)"
                       rf"(?:\{{(?P<shell_swp>{SHELL_RE}(?:,{SHELL_RE})*)\}})?"
                       rf"\((?P<opt>[^)]+)\)"
                       rf"(?P<debug>#)?"
                       rf"(?:\[(?P<shell_swp2>{SHELL_RE}(?:,{SHELL_RE})*)\])?"
                       )

# Forces block
_FORCES_BLOCK_RE = re.compile(r" ([a-zA-Z ]*)Forces \*+\s*$", re.IGNORECASE)
# Stresses block
_STRESSES_BLOCK_RE = re.compile(r" ([a-zA-Z ]*)Stress Tensor \*+\s*$", re.IGNORECASE)

# Bonds
_BOND_RE = re.compile(rf"""\s*
                       (?P<spec1>{ATOM_NAME_RE})\s*(?P<ind1>\d+)\s*
                       --\s*
                       (?P<spec2>{ATOM_NAME_RE})\s*(?P<ind2>\d+)\s*
                       {labelled_floats(("population", "length"))}
                       """, re.VERBOSE)

# Orbital population
_ORBITAL_POPN_RE = re.compile(rf"\s*{ATREG}\s*(?P<orb>[SPDF][xyz]?)"
                              rf"\s*{labelled_floats(('charge',))}")

# Regexp to identify phonon block in .castep file
_CASTEP_PHONON_RE = re.compile(
    rf"""
    \s+\+\s+
    q-pt=\s*{INTNUMBER_RE}\s+
    \({labelled_floats(("qpt",), counts=(3,))}\)
    \s+
    ({FNUMBER_RE})\s+\+
    """, re.VERBOSE)

_PROCESS_PHONON_RE = re.compile(
    rf"""\s+\+\s+
    (?P<N>\d+)\s+
    (?P<frequency>{FNUMBER_RE})\s*
    (?P<irrep>[a-zA-V])?\s*
    (?P<intensity>{FNUMBER_RE})?\s*
    (?P<active>[YN])?\s*
    (?P<raman_intensity>{FNUMBER_RE})?\s*
    (?P<raman_active>[YN])?\s*\+""", re.VERBOSE)

_TDDFT_RE = re.compile(
    rf"""\s*\+\s*
    {INTNUMBER_RE}
    {labelled_floats(("energy", "error"))}
    \s*(?P<type>\w+)
    \s*\+TDDFT""", re.VERBOSE)

_BS_RE = re.compile(
    rf"""
    Spin=\s*(?P<spin>{INTNUMBER_RE})\s*
    kpt=\s*{INTNUMBER_RE}\s*
    \({labelled_floats(("kx","ky","kz"))}\)\s*
    kpt-group=\s*(?P<kpgrp>{INTNUMBER_RE})
    """, re.VERBOSE)

_THERMODYNAMICS_DATA_RE = re.compile(labelled_floats(("T", "E", "F", "S", "Cv")))

# Regexp to identify Mulliken ppoulation analysis line
_CASTEP_POPN_RE = re.compile(rf"\s*{ATREG}\s*(?P<spin_sep>up:)?" +
                             labelled_floats((*SHELLS, "total", "charge", "spin")) +
                             "?"   # Spin is optional
                             )

_CASTEP_POPN_RE_DN = re.compile(r"\s+\d+\s*dn:" +
                                labelled_floats((*SHELLS, "total"))
                                )

# Regexp for born charges
_BORN_RE = re.compile(rf"\s+{ATREG}(?P<charges>(?:\s*{FNUMBER_RE}){{3}})")

# MagRes REs
_MAGRES_RE = (
    # "Chemical Shielding Tensor" 0
    re.compile(rf"\s*\|\s*{ATREG}{labelled_floats(('iso','aniso'))}\s*"
               rf"(?P<asym>{FNUMBER_RE}|N/A)\s*\|\s*"),
    # "Chemical Shielding and Electric Field Gradient Tensor" 1
    re.compile(rf"\s*\|\s*{ATREG}{labelled_floats(('iso','aniso'))}\s*"
               rf"(?P<asym>{FNUMBER_RE}|N/A)"
               rf"{labelled_floats(('cq', 'eta'))}\s*\|\s*"),
    # "Electric Field Gradient Tensor" 2
    re.compile(rf"\s*\|\s*{ATREG}{labelled_floats(('cq',))}\s*"
               rf"(?P<asym>{FNUMBER_RE}|N/A)\s*\|\s*"),
    # "(?:I|Ani)sotropic J-coupling" 3
    re.compile(rf"\s*\|\**\s*{ATREG}{labelled_floats(('fc','sd','para','dia','tot'))}\s*\|\s*"),
    # "Hyperfine Tensor" 4
    re.compile(rf"\s*\|\s*{ATREG}{labelled_floats(('iso',))}\s*\|\s*")
    )
# MagRes Tasks
_MAGRES_TASK = (
    "Chemical Shielding",
    "Chemical Shielding and Electric Field Gradient",
    "Electric Field Gradient",
    "(An)Isotropic J-coupling",
    "Hyperfine"
    )


def parse_castep_file(castep_file, verbose=False):
    """ Parse castep file into lists of dicts ready to JSONise """
    # pylint: disable=redefined-outer-name

    runs = []
    curr_run = defaultdict(list)

    for line in castep_file:
        if re.search(r"Run started", line):
            if curr_run:
                runs.append(curr_run)
            curr_run = defaultdict(list)
            curr_run["time_started"] = line.split(":")[1]
            curr_run["species_properties"] = defaultdict(dict)
            if verbose:
                print(f"Found run {len(runs) + 1}")

        # Finalisation
        elif block := get_block(line, castep_file, "Initialisation time", r"^\s*$"):
            if verbose:
                print("Found finalisation")

            curr_run.update(_process_finalisation(block.splitlines()))

        # Title
        elif re.match(r"^\*+\s*Title\s*\*+$", line):
            if verbose:
                print("Found title")

            curr_run["title"] = next(castep_file).strip()

        # Memory estimate
        elif block := get_block(line, castep_file,
                                r"\s*\+-+\sMEMORY AND SCRATCH",
                                r"\s*\+-+\+"):
            if verbose:
                print("Found memory estimate")

            curr_run["memory_estimate"].append(_process_memory_est(block.splitlines()))

        # Parameters
        elif block := get_block(line, castep_file,
                                r"^\s*\*+ .* Parameters \*+$",
                                r"^\s*\*+$"):
            if verbose:
                print("Found options")

            curr_run["options"] = _process_params(block)

        # Build Info
        elif block := get_block(line, castep_file,
                                r"^\s*Compiled for",
                                r"^\s*$"):

            if verbose:
                print("Found build info")

            curr_run["build_info"] = _process_buildinfo(block)

        # Pseudo-atomic energy
        elif block := get_block(line, castep_file, _PS_SHELL_RE, r"^\s*$", cnt=2):

            if verbose:
                print("Found pseudo-atomic energy")

            key, val = _process_ps_energy(iter(block.splitlines()))
            curr_run["species_properties"][key]["pseudo_atomic_energy"] = val

        # Mass
        elif block := get_block(line, castep_file, r"Mass of species in AMU", r"^ *$"):

            if verbose:
                print("Found mass")

            for line in block.splitlines():
                if (words := line.split()) and re.match(rf"{SPECIES_RE}\b", words[0]):
                    key, val = words
                    curr_run["species_properties"][key]["mass"] = float(val)

        # Electric Quadrupole Moment
        elif block := get_block(line, castep_file, r"Electric Quadrupole Moment", r"^ *$"):

            if verbose:
                print("Found electric quadrupole moment")

            for line in block.splitlines():
                if (words := line.split()) and re.match(rf"{SPECIES_RE}\b", words[0]):
                    key, val = words[0:2]
                    curr_run["species_properties"][key]["elec_quad"] = float(val)

        # DFTD
        elif block := get_block(line, castep_file, "DFT-D parameters", r"^\s*x+\s*$", cnt=2):

            if verbose:
                print("Found DFTD block")

            curr_run["dftd"] = _process_dftd(block.splitlines())

        # Pseudopots
        elif block := get_block(line, castep_file, r"Files used for pseudopotentials", r"^ *$"):

            for line in block.splitlines():
                if (words := line.split()) and re.match(rf"{SPECIES_RE}\b", words[0]):
                    key, val = words

                    if "|" in val:
                        val = _process_pspot_string(val)

                    curr_run["species_properties"][key]["pseudopot"] = val

        # SCF
        elif block := get_block(line, castep_file,
                                "SCF loop", "^-+ <-- SCF", cnt=2):
            if verbose:
                print("Found SCF")

            curr_run["scf"].append(_process_scf(block.splitlines()))

        # Line min
        elif block := get_block(line, castep_file,
                                "WAVEFUNCTION LINE MINIMISATION", r"\s*\+(-+\+){2}", cnt=2):
            if verbose:
                print("Found wvfn line min")

            curr_run["wvfn_line_min"].append(_process_wvfn_line_min(block.splitlines()))

        # Occupancy
        elif block := get_block(line, castep_file,
                                "Occupancy", "Have a nice day"):
            if verbose:
                print("Found occupancies")

            curr_run["occupancies"].append(_process_occupancies(block.splitlines()))

        # Energies
        elif any((line.startswith("Final energy, E"),
                  line.startswith("Final energy"),
                  "Total energy corrected for finite basis set" in line,
                  re.search("(BFGS|TPSD): finished iteration.*with enthalpy", line))):
            if verbose:
                print("Found energy")
            curr_run["energies"].append(to_type(get_numbers(line)[-1], float))

        # Free energies
        elif re.match(rf"Final free energy \(E-TS\) += +({EXPNUMBER_RE})", line):
            if verbose:
                print("Found free energy (E-TS)")
            curr_run["free_energies"].append(to_type(get_numbers(line)[-1], float))

        # Solvation energy
        elif line.startswith(" Free energy of solvation"):
            if verbose:
                print("Found solvation energy")
            curr_run["solvation_energies"].append(*to_type(get_numbers(line), float))

        # Spin densities
        elif match := re.search(rf"Integrated \|?Spin Density\|?\s+=\s+({EXPNUMBER_RE})", line):
            if verbose:
                print("Found spin")

            if "|" in line:
                curr_run["modspin"].append(to_type(match.group(1), float))
            else:
                curr_run["spin"].append(to_type(match.group(1), float))

        # Initial cell
        elif block := get_block(line, castep_file,
                                "Unit Cell", r"^\s+$", cnt=3):
            if verbose:
                print("Found cell")

            curr_run["initial_cell"] = _process_unit_cell(block.splitlines())

        # Cell Symmetry and contstraints
        elif block := get_block(line, castep_file,
                                "Symmetry and Constraints", "Cell constraints are"):

            if verbose:
                print("Found symmetries")

            curr_run["symmetries"], curr_run["constraints"] = _process_symmetry(
                iter(block.splitlines())
            )

        # TSS (must be ahead of initial pos)
        elif block := get_block(line, castep_file,
                                "(Reactant|Product)", r"^\s*x+\s*$", cnt=2):

            mode = "reactant" if "Reactant" in line else "product"

            if verbose:
                print(f"Found {mode} initial states")

            curr_run[mode] = _process_atreg_block(block.splitlines())

        # Initial pos
        elif block := get_block(line, castep_file,
                                "Fractional coordinates of atoms", r"^\s*x+\s*$"):
            if verbose:
                print("Found initial positions")

            curr_run["initial_positions"] = _process_atreg_block(block.splitlines())

        elif "Supercell generated" in line:
            accum = iter(get_numbers(line))
            curr_run["supercell"] = tuple(to_type([next(accum) for _ in range(3)], float)
                                          for _ in range(3))

        # Initial vel
        elif block := get_block(line, castep_file,
                                "User Supplied Ionic Velocities", r"^\s*x+\s*$"):
            if verbose:
                print("Found initial velocities")

            curr_run["initial_velocities"] = _process_atreg_block(block.splitlines())

        # Initial spins
        elif block := get_block(line, castep_file,
                                "Initial magnetic", r"^\s*x+\s*$"):
            if verbose:
                print("Found initial spins")

            curr_run["initial_spins"] = _process_initial_spins(block.splitlines())

        # Target Stress
        elif block := get_block(line, castep_file, "External pressure/stress", r"^\s*$"):

            if verbose:
                print("Found target stress")

            for line in block.splitlines():
                curr_run["target_stress"].extend(to_type(get_numbers(line), float))

        # Finite basis correction parameter
        elif match := re.search(rf"finite basis dEtot\/dlog\(Ecut\) = +({FNUMBER_RE})", line):
            if verbose:
                print("Found dE/dlog(E)")
            curr_run["dedlne"].append(to_type(match.group(1), float))

        # K-Points
        elif block := get_block(line, castep_file, "k-Points For BZ Sampling", r"^\s*$"):
            if verbose:
                print("Found k-points")

            curr_run["k-points"] = _process_kpoint_blocks(block.splitlines(), True)

        elif block := get_block(line, castep_file,
                                r"\s*\+\s*Number\s*Fractional coordinates\s*Weight\s*\+",
                                r"^\s*\++\s*$"):
            if verbose:
                print("Found k-points list")

            curr_run["k-points"] = _process_kpoint_blocks(block.splitlines(), False)

        # Forces blocks
        elif block := get_block(line, castep_file, _FORCES_BLOCK_RE, r"^ \*+$"):
            if "forces" not in curr_run:
                curr_run["forces"] = defaultdict(list)

            lines = iter(block.splitlines())
            key, val = _process_forces(lines)

            if verbose:
                print(f"Found {key} forces")

            curr_run["forces"][key].append(val)

        # Stress tensor block
        elif block := get_block(line, castep_file, _STRESSES_BLOCK_RE, r"^ \*+$"):
            if "stresses" not in curr_run:
                curr_run["stresses"] = defaultdict(list)

            lines = iter(block.splitlines())
            key, val = _process_stresses(lines)

            if verbose:
                print(f"Found {key} stress")

            curr_run["stresses"][key].append(val)

        # Phonon block
        elif match := _CASTEP_PHONON_RE.match(line):
            if verbose:
                print("Found phonon")

            qdata = defaultdict(list)

            qdata["qpt"] = match.group("qpt").split()
            if verbose:
                print(f"Reading qpt {' '.join(qdata['qpt'])}")

            for line in castep_file:
                if match := _CASTEP_PHONON_RE.match(line):
                    if qdata["qpt"] and qdata["qpt"] not in (phonon["qpt"]
                                                             for phonon in curr_run["phonons"]):
                        curr_run["phonons"].append(_process_qdata(qdata))
                    qdata = defaultdict(list)
                    qdata["qpt"] = match.group("qpt").split()
                    if verbose:
                        print(f"Reading qpt {' '.join(qdata['qpt'])}")

                elif (re.match(r"\s+\+\s+Effective cut-off =", line) or
                      re.match(rf"\s+\+\s+q->0 along \((\s*{FNUMBER_RE}){{3}}\)\s+\+", line) or
                      re.match(r"\s+\+ -+ \+", line)):
                    continue
                elif match := _PROCESS_PHONON_RE.match(line):

                    # ==By mode
                    # qdata["modes"].append(match.groupdict())
                    # ==By prop
                    stack_dict(qdata, match.groupdict())

                elif re.match(r"\s+\+\s+.*\+", line):
                    continue
                else:
                    break

            else:
                raise IOError(f"Unexpected end of file in {castep_file.name}")

            if qdata["qpt"] and qdata["qpt"] not in (phonon["qpt"]
                                                     for phonon in curr_run["phonons"]):
                curr_run["phonons"].append(_process_qdata(qdata))

            if verbose:
                print(f"Found {len(curr_run['phonons'])} phonon samples")

        # Phonon Symmetry
        elif block := get_block(line, castep_file,
                                "Phonon Symmetry Analysis", r"^\s*$"):

            if verbose:
                print("Found phonon symmetry analysis")

            val = _process_phonon_sym_analysis(iter(block.splitlines()))
            curr_run["phonon_symmetry_analysis"].append(val)

            # Solvation
        elif block := get_block(line, castep_file,
                                "AUTOSOLVATION", r"^\s*\*+\s*$"):
            if verbose:
                print("Found autosolvation")

            curr_run["autosolvation"] = _process_autosolvation(block.splitlines())

        # Dynamical Matrix
        elif block := get_block(line, castep_file,
                                "Dynamical matrix", r"^\s*-+\s*$"):

            if verbose:
                print("Found dynamical matrix")

            val = _process_dynamical_matrix(iter(block.splitlines()))
            curr_run["dynamical_matrix"] = val

        # Raman tensors
        elif block := get_block(line, castep_file,
                                r"^ \+\s+Raman Susceptibility Tensors", r"^\s*$"):
            if verbose:
                print("Found Raman")

            curr_run["raman"].append(_process_raman(block.splitlines()[1:]))

        # Born charges
        elif block := get_block(line, castep_file, r"^\s*Born Effective Charges\s*$", r"^ =+$"):
            if verbose:
                print("Found Born")

            curr_run["born"].append(_process_born(iter(block.splitlines())))

        # Permittivity and NLO Susceptibility
        elif block := get_block(line, castep_file, r"^ +Optical Permittivity", r"^ =+$"):
            if verbose:
                print("Found optical permittivity")

            val = _process_3_6_matrix(block.splitlines(), True)
            curr_run["optical_permittivity"] = val[0]
            if val[1]:
                curr_run["dc_permittivity"] = val[1]

        # Polarisability
        elif block := get_block(line, castep_file, r"^ +Polarisabilit(y|ies)", r"^ =+$"):
            if verbose:
                print("Found polarisability")

            val = _process_3_6_matrix(block.splitlines(), True)
            curr_run["optical_polarisability"] = val[0]
            if val[1]:
                curr_run["static_polarisability"] = val[1]

        # Non-linear
        elif block := get_block(line, castep_file,
                                r"^ +Nonlinear Optical Susceptibility", r"^ =+$"):
            if verbose:
                print("Found NLO")

            curr_run["nlo"], _ = _process_3_6_matrix(block.splitlines(), False)

        # Thermodynamics
        elif block := get_block(line, castep_file,
                                r"\s*Thermodynamics\s*$",
                                r"\s+-+\s*$", cnt=3):
            if verbose:
                print("Found thermodynamics")

            accum = _process_thermodynamics(block.splitlines())
            curr_run["thermodynamics"].append(accum)

        # Mulliken Population Analysis
        elif block := get_block(line, castep_file,
                                r"Species\s+Ion\s+(Spin)?\s+s\s+p\s+d\s+f",
                                r"=+$", cnt=2):
            if verbose:
                print("Found Mulliken")

            curr_run["mulliken_popn"] = _process_mulliken(iter(block.splitlines()))

        # Orbital populations
        elif block := get_block(line, castep_file,
                                r"Orbital Populations",
                                r"The total projected population"):
            if verbose:
                print("Found Orbital populations")

            curr_run["orbital_popn"] = _process_orbital_populations(iter(block.splitlines()))

        # Bond analysis
        elif block := get_block(line, castep_file,
                                r"Bond\s*Population\s*Length", "=+", cnt=2):
            if verbose:
                print("Found bond info")

            curr_run["bonds"] = _process_bond_analysis(iter(block.splitlines()))

        # Hirshfeld Population Analysis
        elif block := get_block(line, castep_file,
                                r"Species\s+Ion\s+Hirshfeld Charge \(e\)",
                                r"=+$", cnt=2):
            if verbose:
                print("Found Hirshfeld")

            curr_run["hirshfeld"] = _process_hirshfeld(block.splitlines())

        # ELF
        elif block := get_block(line, castep_file,
                                r"ELF grid sample",
                                r"^-+$", cnt=2):
            if verbose:
                print("Found ELF")

            curr_run["elf"] = _process_elf(block.splitlines())

        # MD Block
        elif block := get_block(line, castep_file,
                                r"MD Data:",
                                r"^\s*x+\s*$"):

            if verbose:
                print(f"Found MD Block (step {len(curr_run['md'])+1})")

            curr_run["md"].append(_process_md(block.splitlines()))

        # GeomOpt
        elif block := get_block(line, castep_file,
                                "Final Configuration",
                                r"^\s+x+$", cnt=2):

            if "geom_opt" not in curr_run:
                curr_run["geom_opt"] = {}

            if verbose:
                print("Found final geom configuration")

            curr_run["geom_opt"]["final_configuration"] = _process_atreg_block(block.splitlines())

        elif match := re.match(rf"^\s*(?:{'|'.join(MINIMISERS)}):"
                               r"(?P<key>[^=]+)=\s*"
                               f"(?P<value>{EXPNUMBER_RE}).*",
                               line, re.IGNORECASE):

            if "geom_opt" not in curr_run:
                curr_run["geom_opt"] = {}

            key, val = normalise_string(match["key"]).lower(), to_type(match["value"], float)

            if verbose:
                print(f"Found geomopt {key}")

            curr_run["geom_opt"][key] = val

        # TDDFT
        elif block := get_block(line, castep_file,
                                "TDDFT excitation energies",
                                r"^\s*\+\s*=+\s*\+\s*TDDFT", cnt=2):

            if verbose:
                print("Found TDDFT excitations")

            curr_run["tddft"] = _process_tddft(block.splitlines())

        # Old band structure
        elif block := get_block(line, castep_file,
                                r"^\s+\+\s+(B A N D|Band Structure Calculation)",
                                r"^\s+=+$"):
            if verbose:
                print("Found band-structure")

            curr_run["bs"] = _process_band_structure(block)

        # Chemical shielding
        elif block := get_block(line, castep_file,
                                r"Chemical Shielding Tensor",
                                r"=+$"):
            if verbose:
                print("Found Chemical Shielding Tensor")

            val = _parse_magres_block(0, block.splitlines())
            curr_run["magres"].append(val)

        elif block := get_block(line, castep_file,
                                r"Chemical Shielding and Electric Field Gradient Tensor",
                                r"=+$"):
            if verbose:
                print("Found Chemical Shielding + EField Tensor")

            val = _parse_magres_block(1, block.splitlines())
            curr_run["magres"].append(val)

        elif block := get_block(line, castep_file,
                                r"Electric Field Gradient Tensor",
                                r"=+$"):

            if verbose:
                print("Found EField Tensor")

            val = _parse_magres_block(2, block.splitlines())
            curr_run["magres"].append(val)

        elif block := get_block(line, castep_file,
                                r"(?:I|Ani)sotropic J-coupling",
                                r"=+$"):
            if verbose:
                print("Found J-coupling")

            val = _parse_magres_block(3, block.splitlines())
            curr_run["magres"].append(val)

        elif block := get_block(line, castep_file,
                                r"\|\s*Hyperfine Tensor\s*\|",
                                r"=+$"):

            if verbose:
                print("Found Hyperfine tensor")

            val = _parse_magres_block(4, block.splitlines())
            curr_run["magres"].append(val)

        # --- Extra blocks for testing

        # Hugoniot data
        elif block := get_block(line, castep_file,
                                r"BEGIN hug",
                                r"END hug"):
            if verbose:
                print("Found hug block")

            block = io.StringIO(block)
            val = parse_hug_file(block)
            curr_run["hug"].append(val)

        # Bands block (spectral data)
        elif block := get_block(line, castep_file,
                                r"BEGIN bands",
                                r"END bands"):
            if verbose:
                print("Found bands block")

            block = io.StringIO(block)
            val = parse_bands_file(block)
            curr_run["bands"].append(val["bands"])

        elif block := get_block(line, castep_file,
                                r"BEGIN phonon_dos",
                                r"END phonon_dos"):

            if verbose:
                print("Found phonon_dos block")

            block = io.StringIO(block)
            val = parse_phonon_dos_file(block)
            curr_run["phonon_dos"] = val["dos"]
            curr_run["gradients"] = val["gradients"]

        # E-Field
        elif block := get_block(line, castep_file,
                                r"BEGIN efield",
                                r"END efield"):
            if verbose:
                print("Found efield block")

            block = io.StringIO(block)
            val = parse_efield_file(block)
            curr_run["oscillator_strengths"] = val["oscillator_strengths"]
            curr_run["permittivity"] = val["permittivity"]

        # XRD Structure Factor
        elif block := get_block(line, castep_file,
                                r"BEGIN xrd_sf",
                                r"END xrd_sf"):

            if verbose:
                print("Found xrdsf")

            block = "\n".join(block.splitlines()[1:-1])  # Strip begin/end tags lazily
            block = io.StringIO(block)
            val = parse_xrd_sf_file(block)

            curr_run["xrd_sf"] = val

        # ELF FMT
        elif block := get_block(line, castep_file,
                                r"BEGIN elf_fmt",
                                r"END elf_fmt"):

            if verbose:
                print("Found ELF fmt")

            block = "\n".join(block.splitlines()[1:-1])  # Strip begin/end tags lazily
            block = io.StringIO(block)
            val = parse_elf_fmt_file(block)
            if "kpt-data" not in curr_run:
                curr_run["kpt-data"] = val
            else:
                curr_run["kpt-data"].update(val)

        # CHDIFF FMT
        elif block := get_block(line, castep_file,
                                r"BEGIN chdiff_fmt",
                                r"END chdiff_fmt"):

            if verbose:
                print("Found CHDIFF fmt")

            block = "\n".join(block.splitlines()[1:-1])  # Strip begin/end tags lazily
            block = io.StringIO(block)
            val = parse_chdiff_fmt_file(block)
            if "kpt-data" not in curr_run:
                curr_run["kpt-data"] = val
            else:
                curr_run["kpt-data"].update(val)

        # POT FMT
        elif block := get_block(line, castep_file,
                                r"BEGIN pot_fmt",
                                r"END pot_fmt"):

            if verbose:
                print("Found POT fmt")

            block = "\n".join(block.splitlines()[1:-1])  # Strip begin/end tags lazily
            block = io.StringIO(block)
            val = parse_pot_fmt_file(block)
            if "kpt-data" not in curr_run:
                curr_run["kpt-data"] = val
            else:
                curr_run["kpt-data"].update(val)

        # DEN FMT
        elif block := get_block(line, castep_file,
                                r"BEGIN den_fmt",
                                r"END den_fmt"):

            if verbose:
                print("Found DEN fmt")

            block = "\n".join(block.splitlines()[1:-1])  # Strip begin/end tags lazily
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


def _process_ps_energy(block):
    match = _PS_SHELL_RE.search(next(block))
    spec = match["spec"]
    next(block)
    energy = get_numbers(next(block))[1]
    return spec, float(energy)


def _process_tddft(block):
    tddata = [{"energy": float(match["energy"]),
               "error": float(match["error"]),
               "type": match["type"]}
              for line in block
              if (match := _TDDFT_RE.match(line))]
    return tddata


def _process_atreg_block(block):
    accum = {atreg_to_index(match): to_type(match.group("x", "y", "z"), float)
             for line in block
             if (match := ATDAT3VEC.search(line))}
    return accum


def _process_md(block):
    curr_data = {match.group("key").strip(): float(match.group("val"))
                 for line in block
                 if (match := re.search(r"x\s+"
                                        r"(?P<key>[a-zA-Z][A-Za-z ]+):\s*"
                                        rf"(?P<val>{FNUMBER_RE})", line))}

    return {normalise_string(key): val for key, val in curr_data.items()}


def _process_elf(block):
    curr_data = [to_type(match.group(1), float) for line in block
                 if (match := re.match(rf"\s+ELF\s+\d+\s+({FNUMBER_RE})", line))]
    return curr_data


def _process_hirshfeld(block):
    """ Process Hirshfeld block to dict of charges """
    accum = {atreg_to_index(match): float(match["charge"]) for line in block
             if (match := re.match(rf"\s+{ATREG}\s+(?P<charge>{FNUMBER_RE})", line))}
    return accum


def _process_thermodynamics(block):
    """ Process a thermodynamics block into a dict of lists """
    accum = defaultdict(list)
    for line in block:
        if match := _THERMODYNAMICS_DATA_RE.match(line):
            stack_dict(accum, match.groupdict())
        # elif re.match(r"\s+T\(", line):  # Can make dict/re based on labels
        #     thermo_label = line.split()

    fix_data_types(accum, {key: float for
                           key in ("T", "E", "F", "S", "Cv")})
    return accum


def _process_3_6_matrix(block, split):
    """ Process a single or pair of 3x3 matrices or 3x6 matrix """
    fst = [to_type(vals, float) for line in block
           if (vals := get_numbers(line)) and len(vals) in (3, 6)]
    if split and len(fst[0]) == 6:
        fst, snd = [tuple(line[0:3]) for line in fst], [tuple(line[3:6]) for line in fst]
    else:
        snd = []

    return fst, snd


def _process_params(block):
    """ Process a parameters block into a dict of params """

    opt = {}
    curr_opt = {}
    curr_group = ""

    for line in block.splitlines():
        if match := re.match(r"\s*\*+ ([A-Za-z ]+) Parameters \*+", line):
            if curr_opt:
                opt[curr_group] = curr_opt
            curr_group = normalise_string(match.group(1)).lower()
            curr_opt = {}
        elif len(match := line.split(":")) > 1:
            *key, val = map(normalise_string, match)
            curr_opt[" ".join(key).strip()] = val.strip()

    if curr_opt:
        opt[curr_group] = curr_opt

    return opt


def _process_buildinfo(block):
    info = {}
    block = block.splitlines()

    info["summary"] = " ".join(map(normalise_string, block[0:2]))
    for line in block[2:]:
        if ":" in line:
            key, val = map(normalise_string, line.split(":", 1))
            info[key.strip()] = val.strip()
    return info


def _process_unit_cell(block):
    cell = defaultdict(list)
    prop = []
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
                prop.append(to_type(numbers[0], float))

    cell.update({name: val for val, name in zip(prop, ("volume", "density_amu", "density_g"))})

    return cell


def _process_scf(block):
    scf = []
    curr = {}
    for line in block:
        if match := _SCF_LOOP_RE.match(line):
            if curr:
                scf.append(curr)
            curr = match.groupdict()
            fix_data_types(curr, {"energy": float,
                                  "energy_gain": float,
                                  "fermi_energy": float,
                                  "time": float})

        elif "Density was not mixed" in line:
            curr["density_residual"] = None

        elif "Norm of density" in line:
            curr["density_residual"] = to_type(get_numbers(line)[0], float)

        elif "no. bands" in line:
            curr["no_bands"] = to_type(get_numbers(line)[0], int)

        elif "Kinetic eigenvalue" in line:
            if "kinetic_eigenvalue" not in curr:
                curr["kinetic_eigenvalue"] = []
                curr["eigenvalue"] = []

            curr["kinetic_eigenvalue"] = to_type(get_numbers(line)[1], float)
            eig = []

        elif re.match(r"eigenvalue\s*\d+\s*init=", line):
            labels = ("initial", "final", "change")
            numbers = get_numbers(line)
            eig.append({key: val for val, key in zip(numbers[1:], labels)})

        elif "Checking convergence criteria" in line:
            curr["eigenvalue"].append(eig)
            eig = []

        elif match := re.match(r"[+(]?(?P<key>[()0-9A-Za-z -]+)="
                               rf"\s*{labelled_floats(('val',))} eV\)?", line):
            key, val = normalise_string(match["key"]).lower(), float(match["val"])
            curr[key] = val

    if curr:
        scf.append(curr)

    return scf


def _process_forces(block):
    ftype = (ft_guess if (ft_guess := _FORCES_BLOCK_RE.search(next(block)).group(1))
             else "non-descript")

    ftype = normalise_string(ftype).lower()

    accum = _process_atreg_block(block)

    return ftype, accum


def _process_stresses(block):

    ftype = (ft_guess if (ft_guess := _STRESSES_BLOCK_RE.search(next(block)).group(1))
             else "non-descript")

    ftype = normalise_string(ftype).lower()

    accum = []
    for line in block:
        numbers = get_numbers(line)
        if "*  x" in line:
            accum += numbers[0:]
        elif "*  y" in line:
            accum += numbers[1:]
        elif "*  z" in line:
            accum += numbers[2:]

    accum = to_type(accum, float)

    return ftype, accum


def _process_initial_spins(block):

    accum = {}
    for line in block:
        if match := re.match(rf"\s*\|\s*{ATREG}\s*"
                             rf"{labelled_floats(('spin', 'magmom'))}\s*"
                             r"(?P<fix>[TF])\s*\|", line):
            match = match.groupdict()
            ind = atreg_to_index(match)
            accum[ind] = match
    return accum


def _process_born(block):
    """ Process a Born block into a dict of charges """

    born_accum = {}
    for line in block:
        if match := _BORN_RE.match(line):
            born_accum[atreg_to_index(match)] = (to_type(match["charges"].split(), float),
                                                 to_type(next(block).split(), float),
                                                 to_type(next(block).split(), float))
    return born_accum


def _process_raman(block):
    """ Process a Mulliken block into a list of modes """

    modes = []
    curr_mode = {}
    for line in block:
        if "Mode number" in line:
            if curr_mode:
                modes.append(curr_mode)
            curr_mode = {"tensor": [], "depolarisation": None}
        elif numbers := get_numbers(line):
            curr_mode["tensor"].append(to_type(numbers[0:3], float))
            if len(numbers) == 4:
                curr_mode["depolarisation"] = to_type(numbers[3], float)

        elif re.search(r"^ \+\s+\+", line):  # End of 3x3+depol block
            # Compute Invariants Tr(A) and Tr(A)^2-Tr(A^2) of Raman Tensor
            curr_mode["tensor"] = tuple(curr_mode["tensor"])
            tensor = curr_mode["tensor"]
            curr_mode["trace"] = sum(tensor[i][i] for i in range(3))
            curr_mode["II"] = (tensor[0][0]*tensor[1][1] +
                               tensor[0][0]*tensor[2][2] +
                               tensor[1][1]*tensor[2][2] -
                               tensor[0][1]*tensor[1][0] -
                               tensor[0][2]*tensor[2][0] -
                               tensor[1][2]*tensor[2][1])
    if curr_mode:
        modes.append(curr_mode)

    return modes


def _process_mulliken(block):
    """ Process a mulliken block into a dict of points """
    accum = {}

    for line in block:
        if match := _CASTEP_POPN_RE.match(line):
            mull = match.groupdict()
            mull["spin_sep"] = bool(mull["spin_sep"])
            if mull["spin_sep"]:  # We have spin separation
                add_aliases(mull,
                            {orb: f"up_{orb}" for orb in (*SHELLS, "total")},
                            replace=True)
                line = next(block)
                match = _CASTEP_POPN_RE_DN.match(line)
                match = match.groupdict()

                add_aliases(match,
                            {orb: f"dn_{orb}" for orb in (*SHELLS, "total")},
                            replace=True)

                mull.update(match)
                mull["total"] = float(mull["up_total"]) + float(mull["dn_total"])

            ind = atreg_to_index(mull)
            fix_data_types(mull, {**{f"{orb}": float for orb in (*SHELLS, "total",
                                                                 "charge", "spin")},
                                  **{f"up_{orb}": float for orb in (*SHELLS, "total")},
                                  **{f"dn_{orb}": float for orb in (*SHELLS, "total")}})
            accum[ind] = mull

    return accum


def _process_band_structure(block):
    """ Process a band structure into a list of kpts"""

    def fdt(qdat):
        fix_data_types(qdat, {"spin": int,
                              "kx": float,
                              "ky": float,
                              "kz": float,
                              "kpgrp": int,
                              "band": int,
                              "energy": float})

    bands = []
    qdata = {}

    for line in block.splitlines():
        if match := _BS_RE.search(line):
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


def _process_qdata(qdata):
    """ Special parse for phonon qdata """
    qdata = {key: val
             for key, val in qdata.items()
             if any(val) or key == "qpt"}
    fix_data_types(qdata,
                   {"qpt": float,
                    "N": int,
                    "frequency": float,
                    "intensity": float,
                    "raman_intensity": float
                    })
    return qdata


def _parse_magres_block(task, inp):
    """ Parse MagRes data tables from inp according to task """

    data = defaultdict(list)
    data["task"] = _MAGRES_TASK[task]
    curr_re = _MAGRES_RE[task]
    for line in inp:
        if match := curr_re.match(line):
            match = match.groupdict()
            ind = atreg_to_index(match)
            fix_data_types(match, {key: float for key in ("iso", "aniso", "cq", "eta",
                                                          "fc", "sd", "para", "dia", "tot")})

            if "asym" in match:
                match["asym"] = float(match["asym"]) if match["asym"] != "N/A" else None

            data[ind] = match

    return data


def _process_finalisation(block):

    out = {}

    for line in block:
        if line.strip():
            key, val = line.split("=")
            out[normalise_string(key.lower())] = to_type(get_numbers(val)[0], float)
    return out


def _process_memory_est(block):

    accum = {}

    for line in block:
        if match := re.match(r"\s*\|([A-Za-z ]+)" +
                             labelled_floats(('memory', 'disk'), suff=' MB'), line):
            key, memory, disk = match.groups()
            accum[normalise_string(key)] = {"memory": float(memory),
                                            "disk": float(disk)}

    return accum


def _process_phonon_sym_analysis(block):

    accum = {}
    accum["title"] = normalise_string(next(block).split(":")[1])
    next(block)
    accum["mat"] = [to_type(numbers, int) if all(map(lambda x: x.isdigit(), numbers))
                    else to_type(numbers, float)
                    for line in block if (numbers := get_numbers(line))]
    return accum


def _process_kpoint_blocks(block, explicit_kpoints):

    if explicit_kpoints:
        accum = {}
        for line in block:
            if "MP grid size" in line:
                accum["kpoint_mp_grid"] = to_type(get_numbers(line), int)
            elif "offset" in line:
                accum["kpoint_mp_offset"] = to_type(get_numbers(line), float)
            elif "Number of kpoints" in line:
                accum["num_kpoints"] = to_type(get_numbers(line), int)
    else:
        accum = [{"qpt": to_type(match.group("qx", "qy", "qx"), float),
                  "weight": to_type(match["wt"], float)}
                 for line in block
                 if (match := re.match(rf"\s*\+\s*\d\s*{labelled_floats(('qx', 'qy', 'qz', 'wt'))}",
                                       line))]

    return accum


def _process_symmetry(block):

    sym = {}
    con = {}

    for line in block:
        if "=" in line:
            key, val = map(normalise_string, line.split("="))

            if "Number of" in line:
                val = to_type(val, int)

            if "constraints" in key:
                con[key] = val
            else:
                sym[key] = val

        elif re.match(r"\s*\d+\s*rotation\s*", line):
            if "symop" not in sym:
                sym["symop"] = []

            curr_sym = {"rotation": [], "symmetry_related": []}
            for curr_ln in itertools.islice(block, 3):
                curr_sym["rotation"].append(to_type(get_numbers(curr_ln), float))

            next(block)  # elif re.match(r"\s*\d+\s*displacement\s*", line):

            curr_sym["displacement"] = to_type(get_numbers(next(block)), float)

            next(block)  # elif "symmetry related atoms:" in line:

            while line := next(block).strip():
                key, val = line.split(":")
                curr_sym["symmetry_related"].extend((key, int(ind))
                                                    for ind in val.split())

            sym['symop'].append(curr_sym)

        elif "Centre of mass" in line:
            con["com_constrained"] = "NOT" not in line

        elif cons_block := get_block(line, block, r"constraints\.{5}", r"\s*x+\.{4}\s*"):
            con["ionic_constraints"] = defaultdict(list)
            for match in re.finditer(rf"{ATREG}\s*[xyz]\s*" +
                                     labelled_floats(('pos',), counts=(3,)),
                                     cons_block):
                match = match.groupdict()
                ind = atreg_to_index(match)
                con["ionic_constraints"][ind].append(to_type(match["pos"].split(), float))
        elif "Cell constraints are:" in line:
            con["cell_constraints"] = to_type(get_numbers(line), int)

    return sym, con


def _process_dynamical_matrix(block):
    next(block)  # Skip header line
    next(block)

    real_part = []
    for line in block:
        if "Ion" in line:
            break
        numbers = get_numbers(line)
        real_part.append(numbers[2:])

    imag_part = []
    # Get remainder
    for line in block:
        if numbers := get_numbers(line):
            imag_part.append(numbers[2:])

    accum = []
    for real_row, imag_row in zip(real_part, imag_part):
        accum.append(tuple(complex(float(real), float(imag))
                           for real, imag in zip(real_row, imag_row)))

    return tuple(accum)


def _process_pspot_string(string):
    if not (match := _PSPOT_RE.match(string)):
        raise IOError(f"Attempt to parse {string} as PSPot failed")

    pspot = match.groupdict()
    projectors = []
    for proj in pspot["proj"].split(":"):
        pdict = _PSPOT_PROJ_RE.match(proj).groupdict()
        pdict["shell"] = SHELLS[int(pdict["shell"])]
        fix_data_types(pdict, {"orbital": int})
        projectors.append(pdict)

    if not pspot["shell_swp"]:
        del pspot["shell_swp"]

    if not pspot["shell_swp2"]:
        del pspot["shell_swp2"]

    pspot["projectors"] = tuple(projectors)
    pspot["string"] = string

    fix_data_types(pspot, {"beta_radius": float,
                           "r_inner": float,
                           "core_radius": float,
                           "coarse": int,
                           "medium": int,
                           "fine": int,
                           "local_channel": int})

    return pspot


def _process_bond_analysis(block):
    accum = {((match["spec1"], int(match["ind1"])),
              (match["spec2"], int(match["ind2"]))): {"population": float(match["population"]),
                                                      "length": float(match["length"])}
             for line in block
             if (match := _BOND_RE.match(line))}
    return accum


def _process_orbital_populations(block):

    accum = defaultdict(dict)
    for line in block:
        if match := _ORBITAL_POPN_RE.match(line):
            ind = match.groupdict()
            ind = atreg_to_index(ind)
            accum[ind][match["orb"]] = to_type(match["charge"], float)
        elif match := re.match(rf"\s*Total:\s*{labelled_floats(('charge',))}", line):
            accum["total"] = float(match["charge"])
        elif "total projected" in line:
            accum["total_projected"] = to_type(get_numbers(line), float)

    return accum


def _process_dftd(block):
    dftd = {"species": {}}

    for line in block:
        if len(match := line.split(":")) == 2:
            key, val = match
            val = normalise_string(val)
            if "Parameter" in key:
                val = to_type(get_numbers(val)[0], float)
            dftd[normalise_string(key).lower()] = val

        elif match := re.match(rf"\s*x\s*(?P<spec>{ATOM_NAME_RE})\s*" +
                               labelled_floats(('C6', 'R0')), line):
            dftd["species"][match["spec"]] = {"C6": float(match["C6"]),
                                              "R0": float(match["R0"])}

    return dftd


def _process_occupancies(block):
    label = ("band", "eigenvalue", "occupancy")

    accum = [dict(zip(label, numbers)) for line in block if (numbers := get_numbers(line))]
    for elem in accum:
        fix_data_types(elem, {"band": int,
                              "eigenvalue": float,
                              "occupancy": float})
    return accum


def _process_wvfn_line_min(block):
    accum = {}
    for line in block:
        if "initial" in line:
            accum["init_energy"], accum["init_de_dstep"] = to_type(get_numbers(line), float)
        elif line.strip().startswith("| step"):
            accum["steps"] = to_type(get_numbers(line), float)
        elif line.strip().startswith("| gain"):
            accum["gain"] = to_type(get_numbers(line), float)

    return accum


def _process_autosolvation(block):

    accum = {}
    for line in block:
        if len(match := line.split("=")) > 1:
            key = normalise_string(match[0].strip("-( "))
            val = to_type(get_numbers(line)[0], float)
            accum[key] = val

    return accum
