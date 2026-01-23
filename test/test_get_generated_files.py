"""Test get_generated_files."""

import pytest

from castep_outputs.tools.get_generated_files import get_generated_files

DUMMY_CELL = {
    "positions_frac": {
        ("Si", 1): {},
        ("N", 1): {},
    },
}


@pytest.mark.parametrize(
    "seedname, expected",
    [
        (
            "test",
            [
                "test.bands",
                "test.bib",
                "test.castep",
                "test.castep_bin",
                "test.check",
                "test.cst_esp",
            ],
        ),
    ],
)
def test_cli_like(seedname: str, expected: list[str]) -> None:
    """Test via the CLI like interface parsing files on-the-fly."""
    assert expected == get_generated_files(seedname)


@pytest.mark.parametrize(
    "cell, param, expected",
    [
        (
            DUMMY_CELL,
            {
                "task": "moleculardynamics",
                "metals_method": "dm",
                "opt_strategy": "memory",
                "xc_functional": "LDA",
                "md_ensemble": "NVE",
                "md_extrap": "mixed",
            },
            {
                "seedname.*.drho2m",
                "seedname.bib",
                "seedname.cst_esp",
                "seedname.*.drhom",
                "seedname.castep",
                "seedname.md",
                "seedname.*.wf2m",
                "seedname.castep_bin",
                "seedname.*.wfm",
                "seedname.bands",
                "seedname.check",
            },
        ),
        (
            DUMMY_CELL
            | {
                "species_pot": {
                    "Si": {
                        "proj": "30N1.9:31N2.1:32N2.1",
                        "opt": [
                            "tm",
                            "nonlcc",
                        ],
                        "print": True,
                        "projectors": [
                            {
                                "orbital": 3,
                                "shell": "s",
                                "type": "N",
                                "de": 1.9,
                            },
                            {
                                "orbital": 3,
                                "shell": "p",
                                "type": "N",
                                "de": 2.1,
                            },
                            {
                                "orbital": 3,
                                "shell": "d",
                                "type": "N",
                                "de": 2.1,
                            },
                        ],
                        "string": "2|1.9|2.1|1.3|3.675|5.512|7.35|30N1.9:31N2.1:32N2.1(tm,nonlcc)[]",
                    },
                },
            },
            {
                "task": "singlepoint",
                "metals_method": "dm",
                "opt_strategy": "memory",
                "xc_definition": {
                    "xc": {
                        "LIBXC_GGA_XC_B97_D": 1.0,
                    },
                },
                "write_otfg": "T",
            },
            {
                "seedname.castep",
                "seedname.cst_esp",
                "Si_EXT_PBE_OTF.gamma",
                "Si_EXT_PBE_OTF.pwave",
                "Si_EXT_PBE_OTF.econv",
                "Si_EXT_PBE_OTF.usp",
                "seedname.bands",
                "Si_EXT_PBE_OTF.beta",
                "seedname.bib",
                "seedname.castep_bin",
                "seedname.check",
            },
        ),
        (
            DUMMY_CELL,
            {
                "task": "energy",
                "write_checkpoint": "none",
                "write_bib": False,
                "devel_code": {
                    "pp": {
                        "buck": True,
                        "pot_print": True,
                        "fd_check": True,
                    },
                    "_pp": True,
                },
            },
            {
                "seedname.castep",
                "seedname.fd",
                "seedname_N_N.pot",
                "seedname_Si_Si.pot",
                "seedname_Si_N.pot",
            },
        ),
        (
            DUMMY_CELL,
            {
                "task": "spectral",
                "xc_functional": "LDA",
                "max_scf_cycles": 30,
                "spectral_task": "bandstructure",
                "opt_strategy": "speed",
                "popn_calculate": False,
                "spin_treatment": "VECTOR",
                "spin_orbit_coupling": True,
                "popn_write": "minimal",
            },
            {
                "seedname.bands",
                "seedname.bib",
                "seedname.castep",
                "seedname.castep_bin",
                "seedname.check",
                "seedname.cst_esp",
                "seedname-out.cell",
                "seedname.*.spec",
            },
        ),
        (
            DUMMY_CELL,
            {
                "task": "ElectronicSpectroscopy",
                "spectral_task": "BandStructure",
                "xc_functional": "PBE",
                "spin_polarized": False,
                "spin_orbit_coupling": False,
                "opt_strategy": "Default",
                "metals_method": "dm",
                "mixing_scheme": "Pulay",
                "calculate_stress": False,
                "calculate_elf": False,
                "popn_calculate": False,
                "calculate_hirshfeld": False,
                "calculate_densdiff": False,
                "pdos_calculate_weights": True,
                "spectral_write_eigenvalues": True,
            },
            {
                "seedname-out.cell",
                "seedname.*.spec",
                "seedname.bib",
                "seedname.castep_bin",
                "seedname.check",
                "seedname.bands",
                "seedname.castep",
                "seedname.cst_esp",
                "seedname.pdos_bin",
            },
        ),
        (
            DUMMY_CELL,
            {
                "cut_off_energy": "250 eV",
                "fix_occupancy": "true",
                "grid_scale": "2",
                "fine_grid_scale": "2.3",
                "task": "electronicspectroscopy",
                "spectral_task": "all",
                "opt_strategy": "speed",
                "nextra_bands": "8",
                "rand_seed": "2781828",
                "elec_energy_tol": "1.0e-7 eV",
                "popn_write": "minimal",
            },
            {
                "seedname.bands",
                "seedname.bib",
                "seedname.castep",
                "seedname.castep_bin",
                "seedname.check",
                "seedname.cst_esp",
                "seedname.dome_bin",
                "seedname.elnes_bin",
                "seedname.ome_bin",
                "seedname-out.cell",
                "seedname.*.spec",
            },
        ),
        (
            {
                "positions_frac": {
                    "Si_1": {},
                    "Si_2": {},
                },
                "species_pot": {
                    "Si": {
                        "proj": "30N1.9:31N2.1:32N2.1",
                        "opt": [
                            "tm",
                            "nonlcc",
                        ],
                        "print": True,
                        "projectors": [
                            {
                                "orbital": 3,
                                "shell": "s",
                                "type": "N",
                                "de": 1.9,
                            },
                            {
                                "orbital": 3,
                                "shell": "p",
                                "type": "N",
                                "de": 2.1,
                            },
                            {
                                "orbital": 3,
                                "shell": "d",
                                "type": "N",
                                "de": 2.1,
                            },
                        ],
                        "string": "2|1.9|2.1|1.3|3.675|5.512|7.35|30N1.9:31N2.1:32N2.1(tm,nonlcc)[]",
                    },
                },
            },
            {
                "opt_strategy": "speed",
                "calculate_stress": True,
                "grid_scale": 1.75,
            },
            {
                "seedname.bands",
                "seedname.castep",
                "seedname.cst_esp",
                "seedname.bib",
                "seedname.castep_bin",
                "seedname.check",
                "Si_EXT_LDA_OTF.beta",
                "Si_EXT_LDA_OTF.econv",
                "Si_EXT_LDA_OTF.gamma",
                "Si_EXT_LDA_OTF.pwave",
                "Si_EXT_LDA_OTF.usp",
            },
        ),
    ],
    ids=[
        "MD/Si8-md-extrapm",
        "LIBXC test",
        "Pair_pot/PP_BUCK",
        "Excitations/GaAs",
        "Excitations/BN_DOS",
        "Excitations/Si2-spectral/Si2-all.param",
        "OTF-Gen/Si2-ps-tm",
    ],
)
def test_expected_files(cell, param, expected) -> None:
    assert expected == set(get_generated_files(param, cell))
