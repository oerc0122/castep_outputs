"""Parse parameters dump from check/castep_bin."""

from __future__ import annotations

from typing import Any, BinaryIO

from castep_outputs.utilities.utility import file_or_path

from .fortran_bin_parser import FortranBinaryReader

INIT = {
    "_begin_parameters_dump": str,
    "version_str": str,
}

TERM = {
    "_end_parameters_dump": str,
}

GENERAL_BLOCK = {
    (0, 0): {
        "_begin_general": str,
        "seedname": str,  # seed for filenames
        "comment": str,  # label for output
        "iprint": int,  # verbosity control
        "continuation": str,  # continuation filename
        "reuse": str,  # reuse filename
        "checkpoint": str,  # checkpoint filename
        "task": str,  # type of calc'n
        "calculate_stress": bool,  # turn on stress calculation
        "run_time": int,  # <=0 no time limit, >0 max sec
        "num_backup_iter": int,  # md/geom iterations between backups
        "print_clock": bool,  # print time as calculation progresses
        "length_unit": str,  # default units
        "mass_unit": str,
        "time_unit": str,
        "charge_unit": str,
        "energy_unit": str,
        "force_unit": str,
        "velocity_unit": str,
        "pressure_unit": str,
        "inv_length_unit": str,
        "frequency_unit": str,
        "page_wvfns": int,  # <0 page all wvfns, =0 no paging, >0 page if too big
        "rand_seed": int,  # =0 for random randoms, <>0 for setting seed
        "data_distribution": str,  # Choose data distribution
        "opt_strategy": str,  # Choose optimization strategy
    },
    (3, 0): {
        "backup_interval": int,  # <=0 no timed backups, >0 max secs between backups
        "force_constant_unit": str,
        "volume_unit": str,
        "opt_strategy_bias": int,  # Choose optimization strategy
    },
    (3, 1): {
        "calculate_densdiff": bool,  # turn on density difference calculation
        "num_farms_requested": int,
        "num_proc_in_smp": int,
    },
    (3, 2): {
        "num_proc_in_smp_fine": int,
        "message_size": int,
        "requested_seed": int,  # need for parameters_output
    },
    (4, 0): {
        "ir_intensity_unit": str,
    },
    (4, 1): {
        "print_memory_usage": bool,
        "write_formatted_potential": bool,
        "write_formatted_density": bool,
        "dipole_unit": str,
        "efield_unit": str,
        "calc_molecular_dipole": bool,
    },
    (4, 2): {
        "write_orbitals": bool,
    },
    (4, 3): {
        "calculate_elf": bool,  # turn on ELF
        "write_formatted_elf": bool,
        "cml_output": bool,
        "_dummy_fname": str,  # cml_filename no longer used
    },
    (5, 0): {
        "calculate_hirshfeld": bool,  # turn on Hirshfeld analysis
    },
    (5, 5): {
        "entropy_unit": str,
        "write_cif_structure": bool,
        "write_cell_structure": bool,
    },
    (6, 0): {
        "write_bib": bool,
    },
    (8, 0): {
        "write_checkpoint": str,
        "spin_unit": str,
    },
    (9, 0): {
        "write_otfg": bool,
    },
    (17, 0): {
        "write_cst_esp": bool,
        "write_bands": bool,
        "write_geom": bool,
    },
    (18, 0): {
        "verbosity": str,
        "write_none": bool,
        "write_md": bool,
    },
    (19, 0): {
        "bfield_unit": str,
    },
    (20, 1): {
        "efield_chi2_unit": str,
    },
    (21, 1): {
        "calculate_polarisation": bool,
    },
    (26, 1): {
        "iterative_hirshfeld": bool,
        "hirshfeld_pop_tol": float,
        "hirshfeld_max_iter": int,
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

XC_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "xc_functional": str,
        "xc_vxc_deriv_epsilon": float,  # obsolete in v4.3 onwards
    },
    (3, 0): {
        "nlxc_page_ex_pot": int,
        "nlxc_ppd_integral": bool,
        "nlxc_ppd_size_x": int,
        "nlxc_ppd_size_y": int,
        "nlxc_ppd_size_z": int,
        "nlxc_impose_trs": bool,
        "nlxc_exchange_reflect_kpts": bool,
        "nlxc_k_scrn_den_function": str,
        "nlxc_k_scrn_averaging_scheme": str,
        "nlxc_re_est_k_scrn": bool,
        "nlxc_calc_full_ex_pot": bool,
    },
    (4, 0): {
        "nlxc_div_corr_on": bool,
        "nlxc_div_corr_S_width": float,
        "nlxc_div_corr_tol": float,
        "nlxc_div_corr_npts_step": int,
    },
    (5, 0): {
        "sedc_apply": bool,
        "sedc_scheme": str,
        "nlxc_exchange_screening": float,
    },
    (6, 1): {
        "nlxc_exchange_fraction": float,
    },
    (7, 0): {
        "sedc_sr_TS": float,
        "sedc_d_TS": float,
        "sedc_s6_G06": float,
        "sedc_d_G06": float,
        "sedc_lambda_OBS": float,
        "sedc_n_OBS": float,
        "sedc_sr_JCHS": float,
        "sedc_s6_JCHS": float,
        "sedc_d_JCHS": float,
    },
    (8, 0): {
        "relativistic_treatment": str,
    },
    (9, 0): {
        "_xc_definition_size": int,
        "xc_definition": str,
    },
    (21, 0): {
        "sedc_a1_XDM": float,
        "sedc_a2_XDM": float,
        "sedc_sc_XDM": float,
        "sedc_c9_XDM": bool,
    },
    (25, 1): {
        "xc_functional": str,  # full-length version
        "nlxc_method": str,
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

PSPOT_BLOCK = {
    (0, 0): {
        "_header": str,
        "pspot_nonlocal_type": str,
        "pspot_beta_phi_type": str,
    },
    (9, 0): {
        "spin_orbit_coupling": bool,
    },
    (18, 0): {
        "spinors_spin_polarized": bool,
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

BASIS_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "basis_precision": str,  # Atomic convergence
        "cut_off_energy": float,  # Alt. basis_precision
        "grid_scale": float,  # Std grid size
        "fine_gmax": float,  # Fine grid size
        "finite_basis_corr": int,  # energy/stress fixup
        "basis_de_dloge": float,  # user value
        "finite_basis_npoints": int,  # auto differentiation
        "finite_basis_spacing": float,
    },
    (3, 0): {
        "fixed_npw": bool,
    },
    (4, 0): {
        "fine_grid_scale": float,  # Fine grid scale
    },
    (4, 4): {
        "fft_max_prime_factor": int,
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

ELECTRONIC_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "nelectrons": int,  # real from v4.1       #alt. charge
        "nup": int,  # real from v4.1       #alt. number spin up
        "ndown": int,  # real from v4.1       #alt. number spin down
        "_null": int,  # Was:current_params%nspins
        "nbands": int,  # max. number of bands
        "elec_temp": float,  # electron temperature
    },
    (3, 2): {
        "spin": int,  # real from v4.1       #for parameters_output
        "charge": int,  # real from v4.1       #for parameters_output
        "spin_polarized": bool,  # for parameters_output
        "electronic_minimizer": str,  # for parameters_output
    },
    (4, 1): {
        "nelectrons": float,  # alt. charge
        "nup": float,  # alt. number spin up
        "ndown": float,  # alt. number spin down
        "spin": float,  # for parameters_output
        "charge": float,  # for parameters_output
    },
    (9, 0): {
        "spin_treatment": str,
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

ELEC_MIN_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "max_SD_steps": int,  # max. number of steepest descent steps
        "max_CG_steps": int,  # max. number of conjugate gradient steps
        "max_DIIS_steps": int,  # max. number of RMM/DIIS steps
        "metals_method": str,  # how to treat metals
        "elec_energy_tol": float,  # eV per atom
        "elec_eigenvalue_tol": float,  # eV per eigenvalue
        "elec_convergence_win": int,  # iterations
        "max_SCF_cycles": int,  # stop runaway calcs
        "spin_fix": int,  # <0 spin always fixed, >=0 vary after # iters
        "fix_occupancy": bool,
        "smearing_scheme": str,  # only if a metal
        "smearing_width": float,  # in Kelvins
        "efermi_tol": float,  # metal or etemp>0
        "num_occ_cycles": int,  # " + EDFT
        "elec_dump_file": str,  # periodic dumps
        "num_dump_cycles": int,  # frequency
        "elec_restore_file": str,  # reuse/continuation
    },
    (4, 1): {  # end of keywords for this block in version 2.2
        "elec_force_tol": float,  # eV/Ang/atom
    },
    (6, 1): {
        "dipole_correction": str,
        "dipole_dir": str,
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

DM_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "mixing_scheme": str,  # DM scheme
        "mix_history_length": int,  # DM history
        "mix_charge_amp": float,  # DM amplitude
        "mix_charge_gmax": float,  # max DM gvec ang-1
        "mix_spin_amp": float,  # DM amplitude
        "mix_spin_gmax": float,  # max DM gvec ang-1
        "mix_cut_off_energy": float,  # DM cut off energy
        "mix_metric_q": float,  # DM metric coefficient
    },
    (20, 1): {
        "mix_ked_charge_amp": float,  # KED DM amplitude
        "mix_ked_charge_gmax": float,  # KED max DM gvec ang-1
        "mix_ked_spin_amp": float,  # KED DM amplitude
        "mix_ked_spin_gmax": float,  # KED max DM gvec ang-1
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

POPN_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "popn_calculate": bool,  # do population analysis?
        "popn_bond_cutoff": float,  # cutoff radius in popn analysis
        "pdos_calculate_weights": bool,  # do partial DOS analysis?
    },
    (18, 0): {
        "popn_write": str,  # detail level
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

BS_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "bs_max_iter": int,  # band structure
        "bs_max_CG_steps": int,  # cg steps in bs calculation
        "bs_nbands": int,  # bands/kpoint
        "bs_eigenvalue_tol": float,  # eV per eigenvalue
    },
    (3, 0): {
        "bs_xc_functional": str,  # v25: Trim to 15 to fit old file format
        "bs_re_est_k_scrn": bool,
    },
    (4, 4): {
        "bs_write_eigenvalues": bool,
    },
    (9, 0): {
        "_bs_xc_definition_size": int,
        "bs_xc_definition": str,
    },
    (25, 1): {
        "bs_xc_functional": str,  # full-length version
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

GEOM_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "geom_method": str,  # Geom optimizer
        "geom_max_iter": int,  # Max # iters
        "geom_energy_tol": float,  # eV/atom
        "geom_force_tol": float,  # eV/ang
        "geom_disp_tol": float,  # ang
        "geom_stress_tol": float,  # GPa
        "geom_convergence_win": int,  # iterations
        "geom_modulus_est": float,  # estimated bulk modulus
        "geom_frequency_est": float,  # estimated <frequency> at gamma point
    },
    (4, 0): {
        # end of keywords for this block in version 2.2
        "geom_spin_fix": int,  # <0 spin always fixed, >=0 vary after # iters
        "geom_linmin_tol": float,  # line minimizer tolerance
    },
    (5, 5): {
        "geom_use_linmin": bool,
    },
    (5, 1): {
        "geom_lbfgs_max_updates": int,
        "geom_tpsd_init_stepsize": float,
        "geom_tpsd_iterchange": int,
    },
    (19, 1): {
        "geom_preconditioner": str,
        "geom_precon_scale_cell": bool,
        "geom_precon_exp_c_stab": float,
        "geom_precon_exp_A": float,
        "geom_precon_exp_r_NN": float,
        "geom_precon_exp_r_cut": float,
        "geom_precon_exp_mu": float,
        "geom_precon_ff_c_stab": float,
        "geom_precon_ff_r_cut": float,
    },
    (25, 1): {
        # end of keywords for this block in version 19.1
        "geom_run_time": int,
    },
    (0, 0.1): {
        # end of keywords for this block in version 25.1
        "_end_header": str,
    },
}

MD_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "md_num_iter": int,  # iterations
        "md_delta_t": float,  # ps time step
        "md_ensemble": str,  # or NVT etc.
        "md_temperature": float,  # in Kelvins
        "md_thermostat": str,  # Nose-Hoover/Langevin
        "_md_ion_t_hoover": float,  # characteristic time (NH/NHL)
        "_md_ion_t_langevin": float,  # characteristic time (Lang)
        "md_extrap": str,  # wvfn extrapolate
        "md_extrap_fit": bool,  # T => best-fit, F => fixed
        "md_damping_scheme": str,  # damping scheme
        "md_damping_reset": int,  # reset frequency
        "md_opt_damped_delta_t": bool,  # T => optimal dt, F => fixed dt
        "md_elec_energy_tol": float,  # eV/atom for MD
        "md_elec_eigenvalue_tol": float,  # eV/atom for MD
        "md_elec_convergence_win": int,  # iterations for MD
    },
    (3, 0): {
        "md_barostat": str,  # Andersen-Hoover/Parrinello-Rahman
        "md_ion_t": float,  # ions characteristic time
        "md_cell_t": float,  # cell characteristic time
        "md_nhc_length": int,  # Nose-Hoover chain length
    },
    (3, 1): {
        "md_use_pathint": bool,
        "md_num_beads": int,
    },
    (4, 0): {
        "md_pathint_staging": bool,
        "md_pathint_num_stages": int,
        "md_sample_iter": int,
    },
    (4, 1): {
        "md_eqm_method": str,
        "md_eqm_ion_t": float,
        "md_eqm_cell_t": float,
        "md_eqm_t": float,
        "md_elec_force_tol": float,  # eV/Ang/atom
    },
    (5, 5): {
        "md_pathint_init": str,
    },
    (5, 0): {
        "md_use_plumed": bool,
    },
    (8, 0): {
        "md_xlbomd": bool,
        "md_xlbomd_history": int,
    },
    (9, 0): {
        "md_hug_method": str,
        "md_hug_t": float,
        "md_hug_compression": float,
    },
    (17, 0): {
        "md_hug_dir": str,
    },
    (21, 1): {
        "md_cell_damp_ringing": bool,
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

OPTICS_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "optics_nbands": int,  # max. no. of bands in optics
    },
    (3, 0): {
        "optics_xc_functional": str,  # v25: Trim to 15 to fit old file format
    },
    (9, 0): {
        "_optics_xc_definition_size": int,
        "optics_xc_definition": str,
        # end of keywords for this block in version 9.0
        "optics_xc_functional": str,  # full-length version
        # end of keywords for this block in version 25.1
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

TSSEARCH_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "tssearch_method": str,
        "tssearch_lstqst_protocol": str,
        "tssearch_qst_max_iter": int,
        "tssearch_CG_max_iter": int,
        "tssearch_force_tol": float,
        "tssearch_disp_tol": float,
    },
    (7, 0): {
        "tssearch_max_path_points": int,
        "tssearch_energy_tol": float,
    },
    (21, 1): {
        "tssearch_NEB_spring_constant": float,
        "tssearch_NEB_tangent_mode": str,
        "tssearch_NEB_method": str,
        "tssearch_NEB_max_iter": int,
        "tssearch_NEB_climbing": bool,
        "tssearch_NEB_normed": bool,
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

PHONON_BLOCK = {
    (0, 0): {
        "_begin_header": str,
        "_phonon_const_basis": bool,  # withdrawn
        "phonon_energy_tol": float,  # convergence tolerance
        "phonon_max_CG_steps": int,  # max cg before reset to sd
        "phonon_max_cycles": int,  # max # minimizer steps
        "phonon_convergence_win": int,  # iterations for LR minimiser
        "phonon_preconditioner": str,  # scheme to use for LR minimiser
        "phonon_use_kpoint_symmetry": bool,  # T=> LR with reduced symmetry, F=> full symmetry
    },
    (3, 0): {
        # end of keywords for this block in version 2.2
        "phonon_dos_spacing": float,
        "phonon_finite_disp": float,
        "_phonon_method": str,  # now obsolete - kept for backwards compatibility
        "phonon_calc_lo_to_splitting": bool,
        "phonon_sum_rule": bool,
        "calculate_born_charges": bool,
        "born_charge_sum_rule": bool,
    },
    (3, 1): {
        "phonon_calculate_dos": bool,
        "phonon_dos_limit": float,
        "phonon_force_constant_cutoff": float,
        "phonon_fine_method": str,
        "phonon_method": str,  # was secondd_method
    },
    (4, 4): {
        "phonon_force_constant_cut_scale": float,  # alias for ellipsoid
        "phonon_sum_rule_method": str,
        "calculate_raman": bool,
    },
    (5, 0): {
        "phonon_fine_cutoff_method": str,
    },
    (6, 6): {
        "phonon_dfpt_method": str,
        "raman_range_low": float,
        "raman_range_high": float,
        "phonon_write_force_constants": bool,
        "phonon_write_dynamical": bool,
    },
    (17, 2): {
        "raman_method": str,
    },
    (25, 1): {
        "raman_sum_rule": bool,
    },
    (0, 0.1): {
        "_end_header": str,
    },
}

EFIELD_BLOCK = {
    (3, 0): {
        "_begin_header": str,
        "efield_max_CG_steps": int,
        "efield_max_cycles": int,
        "efield_convergence_win": int,
        "efield_energy_tol": float,
        "efield_calc_ion_permittivity": bool,
        "efield_ignore_molec_modes": str,
        "excited_state_scissors": float,
    },
    (4, 0): {
        "efield_freq_spacing": float,
        "efield_oscillator_Q": float,
    },
    (6, 0): {
        "efield_dfpt_method": str,
    },
    (20, 1): {
        "efield_calculate_nonlinear": str,
    },
    (2, 99): {
        "_end_header": str,
    },
}

THERMODYNAMICS_BLOCK = {
    (3, 1): {
        "_begin_header": str,
        "thermo_calculate_helmholtz": bool,
        "thermo_t_start": float,
        "thermo_t_stop": float,
        "thermo_t_npoints": int,
    },
    (3, 2): {
        "thermo_t_spacing": float,  # for parameters_output
    },
    (3, 0.9): {
        "_end_header": str,
    },
}

WANNIER_BLOCK = {
    (3, 1): {
        "_begin_header": str,
        "wannier_spread_type": str,
        "_dummy_real": float,  # wannier_spread_tol_resta deleted
        "__dummy_real": float,  # wannier_spread_tol_vanderbilt deleted
        "___dummy_real": float,  # wannier_occ_tol deleted
        "wannier_min_algor": str,
        "wannier_max_SD_steps": int,
        "wannier_SD_step": float,
        "wannier_ion_moments": bool,
        "wannier_ion_rmax": float,
        "wannier_ion_cut": bool,
        "wannier_ion_cut_fraction": float,
    },
    (4, 0): {
        "wannier_spread_tol": float,
        "wannier_print_cube": int,
        "wannier_ion_cut_tol": float,
        "wannier_restart": str,
        "wannier_ion_cmoments": bool,
    },
    (3, 0.9): {
        "_end_header": str,
    },
}


MAGRES_BLOCK = {
    (3, 1): {
        "_begin_header": str,
        "magres_task": str,
        "magres_method": str,
        "magres_max_CG_steps": int,
        "dfpt_convergence_win": int,  # alias
        "dfpt_eigenvalue_tol": float,  # alias
        "magres_xc_functional": str,  # v25: Trim to 15 to fit old file format
    },
    (4, 3): {
        "magres_max_sc_cycles": int,
        "magres_jcoupling_task": str,
        "magres_write_response": bool,
    },
    (9, 0): {
        "_magres_xc_definition_size": int,
        "magres_xc_definition": str,
    },
    (25, 1): {
        "magres_xc_functional": str,  # full-length version
        "dfpt_residual_norm": float,
    },
    (3, 0.9): {
        "_end_header": str,
    },
}

ELNES_BLOCK = {
    (4, 4): {
        "_begin_header": str,
        "elnes_nbands": int,
        "elnes_xc_functional": str,  # v25: Trim to 15 to fit old file format
        "elnes_eigenvalue_tol": float,
    },
    (9, 0): {
        "_elnes_xc_definition_size": int,
        "elnes_xc_definition": str,
    },
    (25, 1): {
        "elnes_xc_functional": str,  # full-length version
    },
    (4, 3.9): {
        "_end_header": str,
    },
}

SPECTRAL_BLOCK = {
    (6, 1): {
        "_begin_header": str,
        "spectral_theory": str,
        "spectral_task": str,
        "spectral_max_iter": int,  # spectral calculation
        "spectral_max_steps_per_iter": int,  # steps per iter in spectral
        "spectral_nbands": int,  # bands/kpoint
        "spectral_eigenvalue_tol": float,  # eV per eigenvalue
        "spectral_xc_functional": str,  # v25: Trim to 15 to fit old file format
        "spectral_re_est_k_scrn": bool,
        "spectral_write_eigenvalues": bool,
    },
    (9, 0): {
        "_spectral_xc_definition_size": int,
        "spectral_xc_definition": str,
    },
    (24, 1): {
        "spectral_restart": str,
    },
    (25, 1): {
        "spectral_xc_functional": str,  # full-length version
    },
    (6, 0.9): {
        "_end_header": str,
    },
}


NONSCF_BLOCK = {
    (25, 1): {
        "_begin_header": str,
        "nonscf_eigenvalue_tol": float,
        "nonscf_residual_norm": float,
        "nonscf_max_iter": int,
        "nonscf_max_steps_per_iter": int,
    },
    (25, 0.9): {
        "_end_header": str,
    },
}

TDDFT_BLOCK = {
    (6, 1): {
        "_begin_header": str,
        "tddft_on": bool,  # private variable needed for parameters_output
        "tddft_num_states": int,  # number of excited states
        "tddft_selected_state": int,  # TDDFT state to use in geometry/MD
        "tddft_eigenvalue_tol": float,  # tolerance for each eigenvalue
        "tddft_convergence_win": int,
        "tddft_max_iter": int,
        "tddft_nextra_states": int,  # extra states to improve convergence
        "tddft_xc_functional": str,  # v25: Trim to 15 to fit old file format
        "tddft_method": str,  # TDDFT approach
        "tddft_eigenvalue_method": str,  # TDDFT solver for Hutter approach
        "tddft_approximation": str,  # control Tamm-Dancoff approx. etc
    },
    (9, 0): {
        "_tddft_xc_definition_size": int,
        "tddft_xc_definition": str,
        "tddft_position_method": str,  # control position operator method
    },
    (25, 1): {
        "tddft_xc_functional": str,  # full-length version
    },
    (6, 0.9): {
        "_end_header": str,
    },
}

GA_BLOCK = {
    (4, 1): {
        "_begin_header": str,
        "ga_pop_size": int,  # number of GA members in population
        "ga_max_gens": int,  # max no. of GA generations
        "ga_mutate_rate": float,  # mutation rate per dof
        "ga_mutate_amp": float,  # mutation amp per dof (length)
        "ga_fixed_N": bool,  # T => fixed atom number
        "ga_bulk_slice": bool,  # T => bulk, F=> surface
    },
    (19, 1): {
        "ga_spin_mutate_rate": float,  # spin mutation rate per ion
        "ga_spin_mutate_amp": float,  # spin mutation amp per ion (dipole moment?)
    },
    (25, 1): {
        "ga_run_time": int,  # <=0 no time limit>0 max seconds
    },
    (4, 0.9): {
        "_end_header": str,
    },
}

SOLVENT_BLOCK = {
    (19, 1): {
        "_begin_header": str,
        "boundary_type": str,  # open or periodic, in 1D/2D/3D
        "use_smeared_ions": bool,  # need if non-vacuum
        "mg_fd_order": int,  # finite difference order
        "mg_padding": int,  # pad grid prior to passing
        "dielec_emb_cavity_type": str,  # is cavity FIXED or?
        "dielec_emb_func_method": str,  # use Fattebert-Gygi?
        "dielec_emb_param_set": str,  # use DEFAULT or ?
        "dielec_emb_bulk_permittivity": float,  # relative permittivity
        "write_formatted_dielec_perm": bool,  # T=> final dielectric function
        "implicit_solvent_apolar_term": bool,  # T=> turn on apolar term
        "implicit_solvent_surface_tension": float,  # as used in apolar part
        "implicit_solvent_apolar_factor": float,  # as used in apolar part
        "implicit_solvent_rescale_apolar": bool,  # T=> apply scale factor
    },
    (19, 0.9): {
        "_end_header": str,
    },
}

DELTASCF_BLOCK = {
    (20, 1): {
        "_begin_header": str,
        "calculate_modos": bool,
        "modos_checkpoint": str,
        "_modos_states_size": int,
        "modos_states": str,
        "calculate_deltascf": bool,
        "deltascf_checkpoint": str,
        "deltascf_mode": int,
        "deltascf_dftu_checkpoint": str,
        "deltascf_overlap_cutoff": float,
        "deltascf_excite": bool,
        "deltascf_smearing": float,
        "deltascf_net_spin_1": float,
        "deltascf_net_spin_2": float,
        "_deltascf_constraints_size": int,
        "deltascf_constraints": str,
    },
    (20, 0.9): {
        "_end_header": str,
    },
}

ELASTIC_BLOCK = {
    (25, 1): {
        "_begin_header": str,
        "elastic_method": str,
        "elastic_dfpt_method": str,
        "elastic_ignore_molec_modes": str,
        "elastic_max_CG_steps": int,
        "elastic_max_cycles": int,
        "elastic_convergence_win": int,
        "elastic_energy_tol": float,
        "elastic_finite_strain": float,
        "internal_strain_force_response": bool,
        "internal_strain_sum_rule": bool,
        "elastic_calc_deformation_pot": bool,
        "elastic_calc_elastic_ion_corr": bool,
        "elastic_calc_piezo": bool,
        "elastic_calc_piezo_ion_corr": bool,
    },
    (25, 0.9): {
        "_end_header": str,
    },
}

SOCKETS_BLOCK = {
    (22, 1): {
        "_begin_header": str,
        "socket_host": str,
        "socket_port": int,
    },
    (22, 0.9): {
        "_end_header": str,
    },
}

KOOPMANS_BLOCK = {
    (26, 1): {
        "_begin_header": str,
        "koopmans_method": str,
        "koopmans_LR_method": str,
    },
    (26, 0.9): {
        "_end_header": str,
    },
}

DEVEL_BLOCK = {
    (3, 0): {
        "_begin_header": str,
        "devel_code": str,
    },
    (8, 0): {
        "_devel_block_size": int,
        "devel_block": str,
    },
    (2, 99): {
        "_end_header": str,
    },
}

PARAM_BLOCKS = {
    "general": GENERAL_BLOCK,
    "xc": XC_BLOCK,
    "pspot": PSPOT_BLOCK,
    "basis": BASIS_BLOCK,
    "electronic": ELECTRONIC_BLOCK,
    "electronic_minimisation": ELEC_MIN_BLOCK,
    "density_mixing": DM_BLOCK,
    "population_analysis": POPN_BLOCK,
    "band_structure": BS_BLOCK,
    "geometry_optimisation": GEOM_BLOCK,
    "md": MD_BLOCK,
    "optics": OPTICS_BLOCK,
    "tssearch": TSSEARCH_BLOCK,
    "phonon": PHONON_BLOCK,
    "efield": EFIELD_BLOCK,
    "thermodynamics": THERMODYNAMICS_BLOCK,
    "wannier": WANNIER_BLOCK,
    "magres": MAGRES_BLOCK,
    "elnes": ELNES_BLOCK,
    "spectral": SPECTRAL_BLOCK,
    "nonscf": NONSCF_BLOCK,
    "tddft": TDDFT_BLOCK,
    "ga": GA_BLOCK,
    "solvent": SOLVENT_BLOCK,
    "deltascf": DELTASCF_BLOCK,
    "elastic": ELASTIC_BLOCK,
    "sockets": SOCKETS_BLOCK,
    "koopmans": KOOPMANS_BLOCK,
    "devel": DEVEL_BLOCK,
}


@file_or_path(mode="rb")
def parse_parameters_dump(
    in_file: BinaryIO | FortranBinaryReader,
) -> dict[str, Any]:
    reader = in_file if isinstance(in_file, FortranBinaryReader) else FortranBinaryReader(in_file)

    out = reader.get_dtype_dict(INIT)

    tmp_version = out["version_str"].split(".")

    accum = {
        "version_str": out["version_str"],
        "version": (int(tmp_version[0]), int(tmp_version[1][0])),
        "params": {},
    }

    file_version = accum["version"]
    accum["params"] = {}

    for key, dtypes_dict in PARAM_BLOCKS.items():
        accum["params"][key] = {}
        for minver, dtypes in dtypes_dict.items():
            if minver > file_version:
                continue

            out = reader.get_dtype_dict(dtypes)

            accum["params"][key].update(
                {key: val for key, val in out.items() if not key.startswith("_")},
            )

    reader.get_dtype_dict(TERM)

    return accum
