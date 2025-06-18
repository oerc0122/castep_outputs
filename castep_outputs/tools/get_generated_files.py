"""
Attempt to guess the files which will be output by the castep calculation.

Notes
-----
This is based on the working version of CASTEP, so many not exactly align with
the last release.
"""

from __future__ import annotations

import re
from copy import deepcopy
from enum import Enum, auto
from functools import singledispatch
from itertools import combinations_with_replacement
from pathlib import Path
from typing import TypeVar

from ..parsers.cell_param_file_parser import CellParamData, parse_cell_param_file

Self = TypeVar("Self", bound="UCEnum")


class UCEnum(Enum):
    """Auto upperclass enum."""

    @classmethod
    def _missing_(cls, task: str) -> Self:
        task = task.upper()
        return cls[task]


class Task(UCEnum):
    """CASTEP tasks."""

    SINGLEPOINT = auto()
    PHONON = auto()
    PHONON_EFIELD = auto()
    EFIELD = auto()
    THERMODYNAMICS = auto()
    EPCOUPLING = auto()
    # Not implemented yet.
    # ELASTIC = auto()
    GEOMOPT = auto()
    MD = auto()
    SOCKET_DRIVER = auto()
    TRANSITION_STATE_SEARCH = auto()
    WANNIER = auto()
    MAGRES = auto()
    SPECTRAL = auto()
    AUTOSOLVATION = auto()

    # Aliases
    GEOMETRYOPTIMISATION = GEOMOPT
    GEOMETRYOPTIMIZATION = GEOMOPT
    GEOM = GEOMOPT

    SPE = SINGLEPOINT
    ENERGY = SINGLEPOINT

    MOLECULARDYNAMICS = MD
    DYNAMICS = MD

    SOCKETDRIVER = SOCKET_DRIVER

    TSS = TRANSITION_STATE_SEARCH
    TRANSITIONSTATESEARCH = TRANSITION_STATE_SEARCH

    ELECTRONICSPECTROSCOPY = SPECTRAL
    BANDSTRUCTURE = SPECTRAL
    ELNES = SPECTRAL
    OPTICS = SPECTRAL


class MagresTask(UCEnum):
    """Magres tasks."""

    SHIELDING = auto()
    EFG = auto()
    NMR = auto()
    HYPERFINE = auto()
    GTENSOR = auto()
    EPR = auto()
    JCOUPLING = auto()


class SpectralTask(UCEnum):
    """Spectral tasks."""

    CORELOSS = auto()
    BANDSTRUCTURE = auto()
    OPTICS = auto()
    DOS = auto()
    ALL = auto()


class SpectralTheory(UCEnum):
    """Spectral theories."""

    TDDFT = auto()
    DFT = auto()


XC_TO_PS_THEORY = {
    "pw91": "pbe",
    "pbe": "pbe",
    "rpbe": "rpbe",
    "pbesol": "pbesol",
    "wc": "wc",
    "blyp": "blyp",
    "ms2": "ms2",
    "rscan": "rscan",
    "r2scan": "rscan",
    "lda_pw": "lda_pw",
}


def get_spectral_files(
    param_data: CellParamData,
    seedname: str,
    *,
    is_nlxc: bool,
) -> set[str]:
    """Get files associated with Task = Spectral.

    Parameters
    ----------
    param_data : CellParamData
        Dict containing parameters.
    seedname : str
        Current seedname.
    is_nlxc : bool
        Whether XC functional is non-local.

    Returns
    -------
    set[str]
        Files generated in spectral task.

    Raises
    ------
    KeyError
        Impossible combination.
    """
    out_files = set()
    devel_code = param_data.get("devel_code", {})
    raw_task = param_data.get("task", "SINGLEPOINT").upper()
    spectral_theory = SpectralTheory(param_data.get("spectral_theory", "dft"))
    spectral_task = SpectralTask(param_data.get("spectral_task", "bandstructure"))

    out_files.add(f"{seedname}-out.cell")

    if param_data.get("spectral_restart", True):
        out_files.add(f"{seedname}.*.spec")

    if param_data.get("write_orbitals") or raw_task == "BANDSTRUCTURE":
        out_files.add(f"{seedname}.orbitals")
    if spectral_theory is SpectralTheory.TDDFT:
        if spectral_task is SpectralTask.OPTICS:
            spec_calc = {"core": False, "ome": False, "dome": True}
        elif spectral_task in {SpectralTask.DOS, SpectralTask.BANDSTRUCTURE}:
            spec_calc = {"core": False, "ome": False, "dome": False}
        elif spectral_task is SpectralTask.ALL:
            spec_calc = {"core": False, "ome": False, "dome": True}
        else:
            raise KeyError("Invalid param file")
    else:  # noqa: PLR5501
        if spectral_task is SpectralTask.CORELOSS:
            if is_nlxc:
                raise KeyError("Invalid param file")
            spec_calc = {"core": True, "ome": True, "dome": False}
        elif spectral_task is SpectralTask.OPTICS:
            spec_calc = {"core": False, "ome": False, "dome": True}
        elif spectral_task is SpectralTask.DOS:
            spec_calc = {"core": False, "ome": not is_nlxc, "dome": False}
        elif spectral_task is SpectralTask.BANDSTRUCTURE:
            spec_calc = {"core": False, "ome": False, "dome": False}
        elif spectral_task is SpectralTask.ALL:
            spec_calc = {"core": not is_nlxc, "ome": not is_nlxc, "dome": not is_nlxc}
        else:
            raise KeyError("Invalid param file")

    spectral_devel = devel_code.get("spectral", {})
    spec_calc["core"] = spectral_devel.get("calc_core", spec_calc["core"])
    spec_calc["ome"] = spectral_devel.get("calc_ome", spec_calc["ome"])
    spec_calc["pdos"] = spectral_devel.get("calc_pdos", param_data.get("pdos_calculate_weights"))
    spec_calc["dome"] = spectral_devel.get("calc_dome", spec_calc["dome"])

    out_files |= {
        f"{seedname}.{curr}_bin"
        if spectral_theory is SpectralTheory.DFT
        else f"{seedname}_tddft.{curr}_bin"
        for curr in ("core", "ome", "pdos", "dome")
        if spec_calc[curr]
    }

    return out_files


def get_xc_info(param_data: CellParamData) -> set[str]:
    """Get relevant info from the XC parameters.

    Returns a reduced form of libxc

    Parameters
    ----------
    param_data : CellParamData
        Param file data containing functional definition.

    Returns
    -------
    set[str]
        Active xc functionals.

    Examples
    --------
    >>> get_xc_info({"xc_functional": "pbe"})
    {'pbe'}
    >>> get_xc_info({"xc_functional": "pbe",  # xc_definition takes priority like castep.
    ...              "xc_definition": {"xc": {"lda": 1.}}})
    {'lda'}
    >>> sorted(   # Sorted to force set order.
    ... get_xc_info({"xc_definition": {"xc": {"pbe": 0.25,
    ...                                       "libxc_gga_x_2d_b86_mgc": 0.25,
    ...                                       "libxc_lda_c_vwn": 0.25,
    ...                                       "libxc_hyb_mgga_xc_revtpssh": 0.25}}})
    ... )
    ['libxc_gga', 'libxc_hyb_mgga', 'libxc_lda', 'pbe']
    """
    xc_f = param_data.get("xc_functional", "lda").lower()
    xc_d = param_data.get("xc_definition")

    xc = xc_d["xc"].keys() if xc_d else {xc_f}
    xc = map(str.lower, xc)

    return {typ[0] if (typ := re.match(r"libxc(_hyb)?_(m?gga|lda)", key, re.IGNORECASE)) else key
            for key in xc}


@singledispatch
def get_generated_files(
    seedname: Path | str = "seedname",
    /,
    *,
    param_file: Path | None = None,
    cell_file: Path | None = None,
) -> list[str]:
    """Predict files which would be produced by running inputs.

    Parameters
    ----------
    seedname : Path | str, optional
        Seedname of files to parse.
    param_file : Path | str, optional
        Pre-parsed param file.
    cell_file : Path | str, optional
        Pre-parsed cell file.

    Returns
    -------
    set[str]
        Files which would be produced.

    Notes
    -----
    May struggle to get exact information from complex xc_definitions.
    """
    seedname = Path(seedname)
    if param_file is None:
        param_file = seedname.with_suffix(".param")
    if cell_file is None:
        cell_file = seedname.with_suffix(".cell")

    param = parse_cell_param_file(param_file)[0] if param_file.exists() else {}
    cell = parse_cell_param_file(cell_file)[0] if cell_file.exists() else {}
    return get_generated_files(param, cell, seedname.with_suffix(""))


@get_generated_files.register(dict)
def _(
    param_data: CellParamData,
    cell_data: CellParamData | None = None,
    src: Path | str = "seedname",
) -> list[str]:
    if cell_data is None:
        cell_data = {}

    seedname = Path(src).stem
    param_data = deepcopy(param_data)
    devel_code = param_data.get("devel_code", {})
    raw_task = param_data.get("task", "SINGLEPOINT").upper()
    task = Task(raw_task)

    xc = get_xc_info(param_data)

    is_mgga = xc & {"ms2", "rscan", "r2scan", "libxc_mgga", "libxc_hyb_mgga"}
    is_nlxc = bool(xc & {
        "hf",
        "hf-lda",
        "shf",
        "sx-lda",
        "shf-lda",
        "pbe0",
        "b3lyp",
        "hse03",
        "hse06",
        "spbe0",
    })
    is_oep = xc & {"oep", "lfx", "elp", "ceda"}
    is_spin = (
        param_data.get("spin_treatment", "NONE").upper() == "VECTOR"
        or param_data.get("spin_orbit_coupling")
        or param_data.get("spin_polarised")
        or param_data.get("spin_polarized")
    )
    is_pp = devel_code.get("_pp", False)
    tddft_on = param_data.get("tddft_selected_state", 0) > 0

    out_files = {f"{seedname}.castep"}
    if param_data.get("write_none"):
        for i in (
            "write_bib",
            "write_checkpoint",
            "write_cst_esp",
            "write_bands",
            "write_geom",
            "write_md",
        ):
            param_data[i] = False

    write_check = param_data.get("write_checkpoint", "ALL").upper()
    if write_check in {True, "TRUE", "ALL", "BOTH", "FULL"}:
        out_files.add(f"{seedname}.check")
        out_files.add(f"{seedname}.castep_bin")
    elif write_check == "MINIMAL":
        out_files.add(f"{seedname}.castep_bin")
    elif write_check in {False, "FALSE", "NONE"}:
        pass
    else:
        raise NotImplementedError(
            f"Cannot understand checkpoint: {param_data['write_checkpoint']!r}",
        )

    if param_data.get("write_bands", True) and not is_pp:
        out_files.add(
            f"{seedname}.bands"
            if not param_data.get("tddft_selected_state", 0)
            else f"{seedname}_tddft.bands",
        )

    if devel_code.get("write_formatted_bands"):
        out_files.add(f"{seedname}_*.orbit_fmt")

    if param_data.get("write_bib", True):
        out_files.add(f"{seedname}.bib")
    if not is_pp and param_data.get("write_cst_esp", True):
        out_files.add(f"{seedname}.cst_esp")

    if param_data.get("write_formatted_potential"):
        out_files.add(f"{seedname}.pot_fmt")
        if is_oep:
            out_files.add(f"{seedname}.oep_fmt")

    if param_data.get("write_formatted_density"):
        out_files.add(f"{seedname}.den_fmt")

    if param_data.get("calculate_densdiff"):
        out_files.add(f"{seedname}.chdiff")
        if param_data.get("write_formatted_density"):
            out_files.add(f"{seedname}.chdiff_fmt")

    if param_data.get("calculate_elf"):
        out_files.add(f"{seedname}.elf")
        # Commented out
        # out_files.add("rho_test.den_fmt")
        if param_data.get("write_formatted_elf"):
            out_files.add(f"{seedname}.elf_fmt")

    if param_data.get("write_formatted_dielec_perm"):
        out_files.add(f"{seedname}.eps_format")

    if param_data.get("write_orbitals"):
        pass
    if param_data.get("write_cif_structure"):
        out_files.add(f"{seedname}-out.cif")
    if param_data.get("write_cell_structure"):
        out_files.add(f"{seedname}-out.cell")

    if param_data.get("efield_calc_ion_permittivity"):
        out_files.add(f"{seedname}.efield")

    if param_data.get("calculate_modos"):
        out_files.add(f"{seedname}.modos_state*")

    # Devel enabled
    if devel_code.get("zdos_scf"):
        out_files.add(f"{seedname}.scf_zdos")
    if devel_code.get("write_unformatted_density"):
        out_files.add(f"{seedname}.altden")
    if devel_code.get("trace") or devel_code.get("prof") or devel_code.get("profclass"):
        out_files.add(f"{seedname}.*.profile")
    if devel_code.get("write_formatted_bands"):
        out_files.add(f"{seedname}_*.orbit_fmt")
    if devel_code.get("pp_hybrid") and task in {Task.GEOMOPT, Task.MD}:
        out_files.add(f"{seedname}.hybrid-md.xyz")
    if is_spin and devel_code.get("lda_sf_pot_write"):
        out_files.add(f"{seedname}.B_xc.pot_fmt")
    if devel_code.get("calculate_xrd_sf"):
        out_files.add(f"{seedname}.xrd_sf")
    if devel_code.get("zdos_spectral") and task is Task.SPECTRAL:
        out_files.add(f"{seedname}.spectral_zdos")

    if devel_code.get("_pp") and (pp := devel_code.get("pp")):
        if pp.get("pot_print"):
            if cell_data:
                spec = {spec: None for spec, _ind in cell_data.get("positions_frac", {})}
                out_files |= {
                    f"{seedname}_{a}_{b}.pot" for a, b in combinations_with_replacement(spec, 2)
                }

            else:
                out_files.add(f"{seedname}_*_.pot")

        if pp.get("fd_check"):
            out_files.add(f"{seedname}.fd")

    if param_data.get("pdos_calculate_weights") and raw_task not in {
        "BANDSTRUCTURE",
        "ELECTRONICSPECTROSCOPY",
    }:
        out_files.add(f"{seedname}.pdos_weights")

    is_usp = True
    for spec, pot in cell_data.get("species_pot", {}).items():
        if isinstance(pot, str):
            is_usp = is_usp or pot.endswith(".usp", ".uspcc", ".uspso")
            continue

        if xc & {"libxc_mgga", "libxc_hyb_mgga"}:
            theory = "RSCAN"
        elif xc & {"libxc_gga", "libxc_hyb_gga"}:
            theory = "PBE"
        else:
            theory = XC_TO_PS_THEORY.get(next(iter(xc)), "LDA")

        otf_name = f"{spec}_EXT_{theory}_OTF"

        if pot.get("print"):
            out_files.add(f"{otf_name}.gamma")
            out_files.add(f"{otf_name}.pwave")
            out_files.add(f"{otf_name}.beta")
            out_files.add(f"{otf_name}.econv")

        # Commented out 25.1
        # out_files.add(f"{otf_name}.orbs")
        # out_files.add(f"{otf_name}.potential")

        if not is_mgga and param_data.get("write_otfg", True):
            if is_usp:
                if is_spin:
                    out_files.add(f"{otf_name}.uspso")
                else:
                    out_files.add(f"{otf_name}.usp")
            else:
                out_files.add(f"{otf_name}.recpot")

    if devel_code.get("calc_elastic") or "elastic" in devel_code:
        out_files.add(f"{seedname}.elastic")
        if (
            devel_code.get("elastic", {}).get("deform_pot")
            and not is_mgga
            and not is_usp
            and not is_spin
            and not is_nlxc
        ):
            out_files.add(f"{seedname}.dbands_dstrain")

    if task is Task.AUTOSOLVATION:
        out_files.add(f"{seedname}.vacuum_den")
    # elif task is Task.ELASTIC:  # Not implemented yet
    #     out_files.add(f"{seedname}.elastic")
    #     if (
    #             devel_code.get("ELASTIC", {}).get("DEFORM_POT") and
    #             not is_mgga and
    #             not is_usp and
    #             not is_spin and
    #             not is_nlxc
    #     ):
    #         out_files.add(f"{seedname}.dbands_dstrain")

    elif task is Task.EPCOUPLING:
        out_files.add(f"{seedname}.epme")
        out_files.add(f"{seedname}-*-*-*.ep_pot")
    elif task is Task.GEOMOPT:
        if param_data.get("write_geom", True):
            out_files.add(f"{seedname}.geom")
        if param_data.get("geom_method") == "pes":
            out_files.add(f"{seedname}.pes")
    elif task is Task.SPECTRAL:
        out_files |= get_spectral_files(
            param_data,
            seedname,
            is_nlxc=is_nlxc,
        )
    elif task is Task.MD:
        if param_data.get("write_md", True):
            out_files.add(f"{seedname}.md")
        if param_data.get("md_ensemble") in {"nvhug", "nphug"}:
            out_files.add(f"{seedname}.hug")

        extrap = param_data.get("md_extrap", "first").lower()
        opt_mem = (
            param_data.get("opt_strategy", "default").lower() == "memory"
            or param_data.get("opt_strategy_bias", 0) >= 0
        )
        mix_method = param_data.get("metals_method", "dm").lower()
        if mix_method == "dm" and extrap in {"first", "second", "mixed"} and opt_mem:
            out_files.add(f"{seedname}.*.wfm")
            out_files.add(f"{seedname}.*.drhom")
        if mix_method == "dm" and extrap in {"second", "mixed"} and opt_mem:
            out_files.add(f"{seedname}.*.wf2m")
            out_files.add(f"{seedname}.*.drho2m")

        if param_data.get("md_num_beads", 1) > 1 and param_data.get("num_farms", 1) > 1:
            out_files |= {
                f"{seedname}_farm{i:0>3d}.castep" for i in range(param_data.get("num_farms"))
            }

    elif task is Task.MAGRES:
        out_files.add(f"{seedname}.magres")
        if param_data.get("magres_write_response"):
            out_files.add("current.dat")
            out_files.add("gsden.cube")
    elif task is Task.TSS:
        out_files.add(f"{seedname}.ts")
    elif task is Task.THERMODYNAMICS:
        ...  # No extra files? Created in secondd?

    if task in {Task.PHONON, Task.PHONON_EFIELD}:
        out_files.add(f"{seedname}.phonon")
        if param_data.get("phonon_calculate_dos"):
            out_files.add(f"{seedname}.phonon_dos")
        if filename := devel_code.get("phonon", {}).get("write_external_born"):
            out_files.add(filename)
        if devel_code.get("phonon", {}).get("write_first_order_potential"):
            out_files.add(f"{seedname}-*-*-*.ep_pot")

    if task in {Task.EFIELD, Task.PHONON_EFIELD}:
        out_files.add(f"{seedname}.efield")

    if task is Task.WANNIER:
        raise KeyError("Wannier is not supported")
    if task is Task.SOCKET_DRIVER:
        raise NotImplementedError("Unable to know what files may be written as socket driver.")

    if tddft_on:
        out_files.add(f"{seedname}.tddft")
        if devel_code.get("tddft", {}).get("den1_write"):
            out_files.add(f"{seedname}.td_den")
        if devel_code.get("tddft", {}).get("save_td_den_fmt"):
            out_files.add("den_dump*.dat")

    return sorted(out_files)
