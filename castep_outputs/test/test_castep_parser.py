# pylint: skip-file

import io
import pprint
from unittest import TestCase, main

from castep_outputs.parsers import parse_castep_file
from castep_outputs.parsers.castep_file_parser import (Filters,
                                                       _process_pspot_string)


class test_castep_parser(TestCase):
    def test_get_build_version(self):
        test_text = io.StringIO("""
        Compiled for  GNU 12.2.1 on 14-04-2023 15:14:41
        from code version 2c6c6d262 update-jenkins Fri Apr 14 15:13:22 2023 +0100
        Compiler: GNU Fortran 12.2.1; Optimisation: FAST
        Comms   : Open MPI v4.1.4
        MATHLIBS: blas (LAPACK version 3.11.0)
        FFT Lib : fftw3 version fftw-3.3.10-sse2-avx
        Fundamental constants values: CODATA 2018
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'build_info':
                                     {'summary': ('Compiled for GNU 12.2.1 on 14-04-2023 15:14:41 '
                                                  'from code version 2c6c6d262 update-jenkins '
                                                  'Fri Apr 14 15:13:22 2023 +0100'),
                                      'compiler': 'GNU Fortran 12.2.1; Optimisation: FAST',
                                      'comms': 'Open MPI v4.1.4',
                                      'mathlibs': 'blas (LAPACK version 3.11.0)',
                                      'fft_lib': 'fftw3 version fftw-3.3.10-sse2-avx',
                                      'fundamental_constants_values': 'CODATA 2018'}})

    def test_get_final_printout(self):
        test_text = io.StringIO("""
Initialisation time =      1.07 s
Calculation time    =    135.01 s
Finalisation time   =      0.03 s
Total time          =    136.11 s
Peak Memory Use     = 149108 kB

Overall parallel efficiency rating: Satisfactory (64%)
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'calculation_time': 135.01,
                                     'finalisation_time': 0.03,
                                     'initialisation_time': 1.07,
                                     'peak_memory_use': 149108.0,
                                     'total_time': 136.11,
                                     'parallel_efficiency': 64.0})

    def test_get_title(self):
        test_text = io.StringIO("""
************************************ Title ************************************
 CASTEP calculation for SSEC2016

        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'title': 'CASTEP calculation for SSEC2016'})

    def test_get_warning(self):
        test_text = io.StringIO("""
 WARNING - requested pressure too low to be accurately maintained
         - proceed with caution ...
 Warning - deprecated keyword PHONON_SUM_RULE found in input file
         - preferred usage is PHONON_SUM_RULE_METHOD

 Warning in parameters_validate: current value of
   ELEC_ENERGY_TOL = 0.100000E-07eV
   is too large to achieve desired level of convergence of response properties.
   This may cause convergence failures and/or inaccuracy of results
   of PHONON calculations - recommend you use a smaller value, e.g.
   ELEC_ENERGY_TOL ~ 0.221894E-09eV

 Warning in parameters_validate: current value of
   ELEC_EIGENVALUE_TOL = 0.500000E-08eV
   is too large to achieve desired level of convergence of response properties.
   This may cause convergence failures and/or inaccuracy of results
   of PHONON calculations - recommend you use a smaller value, e.g.
   ELEC_EIGENVALUE_TOL = 0.221894E-09eV

TS: Warning - a minimum between Reactant-TS was found for image   3

  **********************************************************
  *** There were at least     1 warnings during this run ***
  *** => please check the whole of this file carefully!  ***
  **********************************************************

???????????????????????????????????????????????????????????????????????
                     Warning in secondd_find_acoustics
    Failed to identify 3 eigenvectors with acoustic character
    Acoustic sum rule correction will only be applied to 2 mode(s)
????????????????????????????????????????????????????????????????????????
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'warning': ['WARNING - requested pressure too low to be '
                                                 'accurately maintained - proceed with caution ...',

                                                 'Warning - deprecated keyword PHONON_SUM_RULE found '
                                                 'in input file - preferred usage is '
                                                 'PHONON_SUM_RULE_METHOD',

                                                 'Warning in parameters_validate: current value of '
                                                 'ELEC_ENERGY_TOL = 0.100000E-07eV is too large to '
                                                 'achieve desired level of convergence of response '
                                                 'properties. This may cause convergence failures '
                                                 'and/or inaccuracy of results of PHONON calculations '
                                                 '- recommend you use a smaller value, e.g. '
                                                 'ELEC_ENERGY_TOL ~ 0.221894E-09eV',

                                                 'Warning in parameters_validate: current value of '
                                                 'ELEC_EIGENVALUE_TOL = 0.500000E-08eV is too large to '
                                                 'achieve desired level of convergence of response '
                                                 'properties. This may cause convergence failures '
                                                 'and/or inaccuracy of results of PHONON calculations '
                                                 '- recommend you use a smaller value, e.g. '
                                                 'ELEC_EIGENVALUE_TOL = 0.221894E-09eV',

                                                 'TS: Warning - a minimum between Reactant-TS was '
                                                 'found for image   3',

                                                 'Warning in secondd_find_acoustics Failed to identify '
                                                 '3 eigenvectors with acoustic character Acoustic sum '
                                                 'rule correction will only be applied to 2 mode(s)']})

    def test_get_tss_table(self):
        test_text = io.StringIO("""
 |      Initial QST energy path       |
 | Stage |     Image    |    Status   |
 | MEP00 |   Reactant   |  Converged  |
 | MEP00 |   Product    |  Converged  |
 | MEP00 |     TS       |  Converged  |
 | MEP00 |       4      |  Converged  |
 | MEP00 |       5      |  Converged  |
 | MEP00 |       6      |  Converged  |
 | MEP00 |       7      |  Converged  |
 | MEP00 |       8      |  Converged  |
 | MEP00 |       9      |  Converged  |
 |                                MEP iteration  1                              |
 | Stage | Image | |F|max(eV/A) |OK?| |dR|max(A) |OK?| dE/ion(eV) |OK?|  Status |
 |       |       |  Tol:  0.50E+00  | Tol:  0.10E-01 | Tol:  0.22E-03 |         |
 | >  0.11578  < |   0.32E+01   |   |   0.00E+00 |   |   0.00E+00 |   | E  => G |
 | >  0.10974  < |   0.31E+01   |No |   0.10E+01 |No |   0.54E-01 |No | v  => v |
 | >  0.11071  < |   0.33E+01   |No |   0.24E-01 |No |   0.10E-01 |No | v  => ^ |
 | >  0.11187  < |   0.31E+01   |No |   0.71E-02 |Yes|   0.27E-02 |No | ^  => ^ |
 | >  0.11221  < |   0.30E+01   |No |   0.14E-02 |Yes|   0.13E-02 |No | ^  => v |
 | >  0.11223  < |   0.30E+01   |Yes|   0.20E-03 |Yes|   0.74E-05 |Yes| ^  => v |
 | MEP01 |    4  |   0.30E+01   |Yes|   0.20E-03 |Yes|   0.74E-05 |Yes|   Yes   |
 | >  0.23075  < |   0.30E+01   |   |   0.00E+00 |   |   0.00E+00 |   | E  => G |
 | >  0.21945  < |   0.29E+01   |No |   0.13E+01 |No |   0.86E-01 |No | v  => v |
 | >  0.21719  < |   0.32E+01   |No |   0.40E-01 |No |   0.17E-01 |No | v  => ^ |
 | MEP01 |    6  |   0.20E+01   |No |   0.58E-01 |No |   0.17E-04 |Yes|   No    |
 |                                MEP iteration  2                              |
 | MEP09 |    8  |                                                    |Converged|
 | MEP09 |    9  |                                                    |Converged|
 |                                MEP iteration 10                              |
 | Stage | Image | |F|max(eV/A) |OK?| |dR|max(A) |OK?| dE/ion(eV) |OK?|  Status |
 |       |       |  Tol:  0.50E-01  | Tol:  0.10E-02 | Tol:  0.22E-04 |         |
 | MEP10 |    4  |                                                    |Converged|
 | MEP10 |    6  |   0.15E+01   |No |   0.12E-05 |Yes|   0.38E-05 |Yes|   Yes   |
 | MEP10 |    7  |                                                    |Converged|
 | MEP10 |    8  |                                                    |Converged|
 | MEP10 |    9  |                                                    |Converged|
 +------------------------------------------------------------------------------+

        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_mem_est(self):
        test_text = io.StringIO("""
        +---------------- MEMORY AND SCRATCH DISK ESTIMATES PER PROCESS --------------+
        |                                                     Memory          Disk    |
        | Baseline code, static data and system overhead      239.0 MB         0.0 MB |
        | BLAS internal memory storage                          0.0 MB         0.0 MB |
        | Model and support data                             3780.5 MB         0.0 MB |
        | Electronic energy minimisation requirements        6100.6 MB         0.0 MB |
        | Force calculation requirements                        9.8 MB         0.0 MB |
        |                                               ----------------------------- |
        | Approx. total storage required per process        10120.1 MB         0.0 MB |
        |                                                                             |
        | Requirements will fluctuate during execution and may exceed these estimates |
        +-----------------------------------------------------------------------------+
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'memory_estimate':
                                     [{'blas_internal_memory_storage': {'disk': 0.0, 'memory': 0.0},
                                       'electronic_energy_minimisation_requirements': {'disk': 0.0,
                                                                                       'memory': 6100.6},
                                       'force_calculation_requirements': {'disk': 0.0, 'memory': 9.8},
                                       'model_and_support_data': {'disk': 0.0, 'memory': 3780.5}}
                                      ]})

    def test_get_cell_structure(self):

        test_text = io.StringIO("""
                           -------------------------------
                                      Unit Cell
                           -------------------------------
        Real Lattice(A)                      Reciprocal Lattice(1/A)
     6.3145000     0.0000000     0.0000000        0.995040828   0.000000000   0.000000000
     0.0000000     6.3145000     0.0000000        0.000000000   0.995040828   0.000000000
     0.0000000     0.0000000     6.3145000        0.000000000   0.000000000   0.995040828

                       Lattice parameters(A)       Cell Angles
                    a =      6.314500          alpha =   90.000000
                    b =      6.314500          beta  =   90.000000
                    c =      6.314500          gamma =   90.000000

                       Current cell volume =           251.777492       A**3
                                   density =             4.364016   AMU/A**3
                                           =             7.246619     g/cm^3
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'initial_cell':
                                     {'cell_angles': [90.0, 90.0, 90.0],
                                      'density_amu': 4.364016,
                                      'density_g': 7.246619,
                                      'lattice_parameters': [6.3145,
                                                             6.3145,
                                                             6.3145],
                                      'real_lattice': [(6.3145, 0.0, 0.0),
                                                       (0.0, 6.3145, 0.0),
                                                       (0.0, 0.0, 6.3145)],
                                      'recip_lattice': [(0.995040828,
                                                         0.0,
                                                         0.0),
                                                        (0.0,
                                                         0.995040828,
                                                         0.0),
                                                        (0.0,
                                                         0.0,
                                                         0.995040828)],
                                      'volume': 251.777492}})

    def test_get_supercell(self):
        test_text = io.StringIO("""
    Supercell generated using matrix  [1,1,-1; 1,-1,1; -1,1,1]
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'supercell': ((1.0, 1.0, -1.0),
                                                   (1.0, -1.0, 1.0),
                                                   (-1.0, 1.0, 1.0))})

    def test_get_atom_structure(self):
        test_text = io.StringIO("""
                           -------------------------------
                                     Cell Contents
                           -------------------------------

        xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        x  Element    Atom        Fractional coordinates of atoms  x
        x            Number           u          v          w      x
        x----------------------------------------------------------x
        x  Mn           1         0.061000   0.061000   0.061000   x
        x  Mn           2         0.811000   0.311000   0.189000   x
        x  Mn:aTag      3         0.939000   0.561000   0.439000   x
        xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'initial_positions':
                                     {('Mn', 1): (0.061, 0.061, 0.061),
                                      ('Mn', 2): (0.811, 0.311, 0.189),
                                      ('Mn:aTag', 3): (0.939, 0.561, 0.439)}})

    def test_get_atom_struct_labelled(self):
        test_text = io.StringIO("""
     xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     x  Element    Atom        Fractional coordinates of atoms  User-defined  x
     x            Number           u          v          w          LABEL     x
     x------------------------------------------------------------------------x
     x  H            1         0.000000   0.000000   0.000000     H1          x
     x  H            2        -0.000000  -0.000000   0.166667     H2          x
     x  H            3         1.000000  -1.000000   0.000000                 x
     xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'initial_positions': {('H [H1]', 1): (0.0, 0.0, 0.0),
                                                           ('H [H2]', 2): (-0.0, -0.0, 0.166667),
                                                           ('H', 3): (1.0, -1.0, 0.0)},
                                     'labels': {('H', 1): 'H1',
                                                ('H', 2): 'H2',
                                                ('H', 3): 'NULL'}
                                     })

    def test_get_atom_struct_mixed(self):
        test_text = io.StringIO("""
        xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        x  Mixture   Fractional coordinates of atoms  Components  Weights  x
        x   atoms       u          v          w                            x
        x------------------------------------------------------------------x
        x    1        0.000000   0.000000   0.000000   Si        0.750000  x
        x                                              Ge        0.250000  x
        x    2        0.250000   1.250000   0.250000   Si [A1]   0.750000  x
        x                                              Ge:MyTag  0.250000  x
        xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'initial_positions': {
            ('Si', 1): {'pos': (0.0, 0.0, 0.0), 'weight': 0.75},
            ('Ge', 1): {'pos': (0.0, 0.0, 0.0), 'weight': 0.25},
            ('Si [A1]', 2): {'pos': (0.25, 1.25, 0.25), 'weight': 0.75},
            ('Ge:MyTag', 2): {'pos': (0.25, 1.25, 0.25), 'weight': 0.25}
                                     }})

    def test_get_atom_velocities(self):
        test_text = io.StringIO("""
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x  Element    Atom        User Supplied Ionic Velocities   x
            x            Number          Vx         Vy         Vz      x
            x----------------------------------------------------------x
            x  Si           1         3.601230   0.986420   2.774470   x
            x  Si           2         1.855230   3.245360   6.707270   x
            x  Si:aTag      3         5.867920   2.404810   1.768580   x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'initial_velocities':
                                     {('Si', 1): (3.60123, 0.98642, 2.77447),
                                      ('Si', 2): (1.85523, 3.24536, 6.70727),
                                      ('Si:aTag', 3): (5.86792, 2.40481, 1.76858)}})

    def test_get_atom_spin_params(self):
        test_text = io.StringIO("""
         xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
         |  Element    Atom         Initial            Initial magnetic       |
         |            Number    spin polarization        moment (uB)     Fix? |
         |--------------------------------------------------------------------|
         | Cr             1         0.500000              3.000       F       |
         | Cr             2        -0.500000             -3.000       T       |
         xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'initial_spins': {('Cr', 1): {'fix': False,
                                                                   'magmom': 3.0,
                                                                   'spin': 0.5},
                                                       ('Cr', 2): {'fix': True,
                                                                   'magmom': -3.0,
                                                                   'spin': -0.5}}})

    def test_get_pspot(self):
        test_text = io.StringIO("""
 Atomic calculation performed for Mn: 1s2 2s2 2p6 3s2 3p6 3d5 4s2

 Converged in 96 iterations to an ae energy of -31436.261 eV

   ============================================================
   | Pseudopotential Report - Date of generation 14-07-2023   |
   ------------------------------------------------------------
   | Element: Mn Ionic charge: 15.00 Level of theory: LDA     |
   | Atomic Solver: Koelling-Harmon                           |
   |                                                          |
   |               Reference Electronic Structure             |
   |         Orbital         Occupation         Energy        |
   |          2s               2.000           -0.501         |
   |          3s1/2            2.000           -3.132         |
   |          3p1/2            2.000           -2.001         |
   |                                                          |
   |                 Pseudopotential Definition               |
   |      Beta    l   2j     e      Rc     scheme   norm      |
   |        1     0    1   -3.132   1.803     qc     0        |
   |       loc    3    0    0.000   1.803     pn     0        |
   |        3     0        -0.501   1.395     qc     0        |
   |       loc    3         0.000   1.803     pn     0        |
   |                                                          |
   | Augmentation charge Rinner = 0.600                       |
   | Partial core correction Rc = 0.600                       |
   ------------------------------------------------------------
   | "3|1.8|1.8|0.6|12|14|16|30U:40:31:32(qc=7)"              |
   ------------------------------------------------------------
   |      Author: Chris J. Pickard, Cambridge University      |
   ============================================================

 Pseudo atomic calculation performed for Mn 3s2 3p6 3d5 4s2

 Converged in 38 iterations to a total energy of -2901.7207 eV

   ============================================================
   | Pseudopotential Report - Date of generation 14-07-2023   |
   ------------------------------------------------------------
   | Element: Mn Ionic charge: 15.00 Level of theory: LDA     |
   | Atomic Solver: Koelling-Harmon                           |
   |                                                          |
   |               Reference Electronic Structure             |
   |         Orbital         Occupation         Energy        |
   |          2s               2.000           -0.501         |
   |                                                          |
   |                 Pseudopotential Definition               |
   |      Beta    l   2j     e      Rc     scheme   norm      |
   |        1     0    1   -3.132   1.803     qc     0        |
   |                                                          |
   | No charge augmentation                                   |
   | No partial core correction                               |
   ------------------------------------------------------------
   | "2|1.8|3.675|5.512|7.35|30UU:31UU:32LGG{1s1}[]"          |
   ------------------------------------------------------------
   |      Author: Chris J. Pickard, Cambridge University      |
   ============================================================


        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'pspot_detail':
                                     [{'augmentation_charge_rinner': (0.6,),
                                       'element': 'Mn',
                                       'ionic_charge': 15.0,
                                       'level_of_theory': 'LDA',
                                       'partial_core_correction': (0.6,),
                                       'pseudopotential_definition': [{'Rc': 1.803,
                                                                       'beta': 1,
                                                                       'e': -3.132,
                                                                       'j': 1,
                                                                       'l': 0,
                                                                       'norm': 0,
                                                                       'scheme': 'qc'},
                                                                      {'Rc': 1.803,
                                                                       'beta': 'loc',
                                                                       'e': 0.0,
                                                                       'j': 0,
                                                                       'l': 3,
                                                                       'norm': 0,
                                                                       'scheme': 'pn'},
                                                                      {'Rc': 1.395,
                                                                       'beta': 3,
                                                                       'e': -0.501,
                                                                       'j': None,
                                                                       'l': 0,
                                                                       'norm': 0,
                                                                       'scheme': 'qc'},
                                                                      {'Rc': 1.803,
                                                                       'beta': 'loc',
                                                                       'e': 0.0,
                                                                       'j': None,
                                                                       'l': 3,
                                                                       'norm': 0,
                                                                       'scheme': 'pn'}],
                                       'reference_electronic_structure': [{'energy': -0.501,
                                                                           'occupation': 2.0,
                                                                           'orb': '2s'},
                                                                          {'energy': -3.132,
                                                                           'occupation': 2.0,
                                                                           'orb': '3s1/2'},
                                                                          {'energy': -2.001,
                                                                           'occupation': 2.0,
                                                                           'orb': '3p1/2'}],
                                       'solver': 'Koelling-Harmon'},
                                      {'element': 'Mn',
                                       'ionic_charge': 15.0,
                                       'level_of_theory': 'LDA',
                                       'pseudopotential_definition': [{'Rc': 1.803,
                                                                       'beta': 1,
                                                                       'e': -3.132,
                                                                       'j': 1,
                                                                       'l': 0,
                                                                       'norm': 0,
                                                                       'scheme': 'qc'}],
                                       'reference_electronic_structure': [{'energy': -0.501,
                                                                           'occupation': 2.0,
                                                                           'orb': '2s'}],
                                       'solver': 'Koelling-Harmon'}],
                                     'species_properties': {'Mn': {'pseudo_atomic_energy': -2901.7207}}})

    def test_get_pspot_debug(self):
        test_text = io.StringIO("""
 ---------------------------------------
 AE eigenvalue nl 10 = -18.40702924
 AE eigenvalue nl 20 = -0.54031716
 AE eigenvalue nl 21 = -0.01836880
 ---------------------------------------
 PS eigenvalue nl 20 = -0.54026290
 PS eigenvalue nl 21 = -0.01829559
 ---------------------------------------
 Maximum eigenvalue error:   3.26E-05

 Derived cutoff energies: C=  22 M=  27 F=  31 E=  36

 Checking for ghost states up to   1.49010 Ha

 No Ghost States Identified

        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'pspot_debug':
                                     [{'eigenvalue': -18.40702924, 'nl': 10, 'type': 'AE'},
                                      {'eigenvalue': -0.54031716, 'nl': 20, 'type': 'AE'},
                                      {'eigenvalue': -0.0183688, 'nl': 21, 'type': 'AE'},
                                      {'eigenvalue': -0.5402629, 'nl': 20, 'type': 'PS'},
                                      {'eigenvalue': -0.01829559, 'nl': 21, 'type': 'PS'}
                                      ]})

    def test_get_species_prop(self):
        test_text = io.StringIO("""
                           -------------------------------
                                   Details of Species
                           -------------------------------

                               Mass of species in AMU
                                    Mn   54.9380500
                                    O    15.9993815

                          Electric Quadrupole Moment (Barn)
                                    Mn    0.3300000 Isotope 55
                                    O     1.0000000 No Isotope Defined
         xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
         |  Element    Atom         Initial            Initial magnetic       |
         |            Number    spin polarization        moment (uB)     Fix? |
         |--------------------------------------------------------------------|
         | Mn             1         0.166667              2.500       F       |
         | Mn             2         0.166667              2.500       F       |
         xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

         Quantisation axis:    1.00000   2.00000   3.00000

                                  Files used for pseudopotentials:
                                    Mn 3|1.8|1.8|0.6|12|14|16|30U:40:31:32(qc=7)
                                    O  my_pot.usp
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'initial_spins': {('Mn', 1): {'fix': False,
                                                                   'magmom': 2.500,
                                                                   'spin': 0.166667},
                                                       ('Mn', 2): {'fix': False,
                                                                   'magmom': 2.500,
                                                                   'spin': 0.166667}},
                                     'species_properties': {'Mn': {'electric_quadrupole_moment': 0.33,
                                                                   'mass': 54.93805,
                                                                   'pseudopot': {'beta_radius': 1.8,
                                                                                 'coarse': 12.0,
                                                                                 'core_radius': 1.8,
                                                                                 'fine': 16.0,
                                                                                 'local_channel': 3,
                                                                                 'medium': 14.0,
                                                                                 'opt': ['qc=7'],
                                                                                 'print': False,
                                                                                 'proj': '30U:40:31:32',
                                                                                 'projectors': ({'orbital': 3,
                                                                                                 'shell': 's',
                                                                                                 'type': 'U'},
                                                                                                {'orbital': 4,
                                                                                                 'shell': 's',
                                                                                                 'type': None},
                                                                                                {'orbital': 3,
                                                                                                 'shell': 'p',
                                                                                                 'type': None},
                                                                                                {'orbital': 3,
                                                                                                 'shell': 'd',
                                                                                                 'type': None}),
                                                                                 'r_inner': 0.6,
                                                                                 'string': '3|1.8|1.8|0.6|12|14|16|30U:40:31:32(qc=7)'}},
                                                            'O': {'mass': 15.9993815,
                                                                  'electric_quadrupole_moment': 1.0,
                                                                  'pseudopot': 'my_pot.usp'}
                                                            },
                                     'quantisation_axis': (1.0, 2.0, 3.0)
                                     })

    def test_get_params(self):
        test_text = io.StringIO("""
 ***************************** General Parameters ******************************

 output verbosity                               : normal  (1)
 write checkpoint data to                       : beta-mn.check
 output         length unit                     : A

 ************************** Density Mixing Parameters **************************

 density-mixing scheme                          : Broyden
 max. length of mixing history                  :         20

 ************************* Constrained DFT - deltaSCF **************************

 groundstate checkpoint data in                 : N2-base.check
 deltaSCF method                                : simple
 deltaSCF smearing width                        :     0.0100   eV
 deltaSCSF spin moment in channel 1             :     0.0000
 deltaSCSF spin moment in channel 2             :     0.0000

 ******************************* Developer Code ********************************

 DW_FACTOR:
 Si 0.4668
 :ENDDW_FACTOR
 CALCULATE_XRD_SF:
 0 0 0
 1 1 1
 2 2 0
 3 1 1
 2 2 2
 :ENDCALCULATE_XRD_SF

 *******************************************************************************
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'options': {'constrained dft - deltascf':
                                                 {'deltaSCF method': 'simple',
                                                  'deltaSCF smearing width': (0.01,
                                                                              'eV'),
                                                  'deltaSCSF spin moment in channel 1': 0.0,
                                                  'deltaSCSF spin moment in channel 2': 0.0,
                                                  'groundstate checkpoint data in': 'N2-base.check'},
                                                 'density mixing': {'density-mixing scheme': 'Broyden',
                                                                    'max. length of mixing history': 20},
                                                 'devel_code': {'calculate_xrd_sf': {'data': [0, 0, 0,
                                                                                              1, 1, 1,
                                                                                              2, 2, 0,
                                                                                              3, 1, 1,
                                                                                              2, 2, 2]},
                                                                'dw_factor': {'data': ['Si', 0.4668]}},
                                                 'general': {'output verbosity': 'normal (1)',
                                                             'write checkpoint data to': 'beta-mn.check'},
                                                 'output_units': {'length': 'A'}}})

    def test_get_dftd_params(self):
        test_text = io.StringIO("""
                                --------------------
                                  DFT-D parameters
                                --------------------

                          Dispersion-correction scheme : G06
                        Parameter s6 :   0.750000 (default)
                        Parameter d  :  20.000000 (default)

        xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        x              Atomic DFT-D parameters                             x
        x  Species      C6            R0                                   x
        x               eV A^6        Ang                                  x
        x------------------------------------------------------------------x
        x  H             1.4510       1.0010   (default)                   x
        x  N            12.7481       1.3970   (default)                   x
        xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'dftd': {'dispersion_correction_scheme': 'G06',
                                              'parameter_d': 20.0,
                                              'parameter_s6': 0.75,
                                              'species': {'H': {'c6': 1.451, 'r0': 1.001},
                                                          'N': {'c6': 12.7481, 'r0': 1.397}}
                                              }}
                         )

        test_text = io.StringIO("""
                                --------------------
                                  DFT-D parameters
                                --------------------

                          Dispersion-correction scheme : XDM
                        Parameter sc :   1.000000 (default)
                        Parameter a1 :   0.345400 (default)
                        Parameter a2 :   5.229439 (default)

        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'dftd': {'dispersion_correction_scheme': 'XDM',
                                              'parameter_a1': 0.3454,
                                              'parameter_a2': 5.229439,
                                              'parameter_sc': 1.0,
                                              'species': {}}}
                         )

    def test_get_verbose_com_remove(self):
        test_text = io.StringIO("""
firstd_calculate: removing force on centre of mass
 dFx:  -1.0633987424376136E-008 eV/A
 dFy:   4.9260774814424966E-008 eV/A
 dFz:  -9.5379737861699631E-004 eV/A
    """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_k_pts(self):
        test_text = io.StringIO("""
                           -------------------------------
                              k-Points For BZ Sampling
                           -------------------------------
                       MP grid size for SCF calculation is  4  4  4
                            with an offset of   0.000  0.000  0.000
                       Number of kpoints used =            32

        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'k-points': {'kpoint_mp_grid': (4, 4, 4),
                                                  'kpoint_mp_offset': (0.0, 0.0, 0.0),
                                                  'num_kpoints': 32}})

        test_text = io.StringIO("""
                           -------------------------------
                              k-Points For BZ Sampling
                           -------------------------------
                       Number of kpoints used =             2

        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'k-points': {'num_kpoints': 2}})

        test_text = io.StringIO("""
             +++++++++++++++++++++++++++++++++++++++++++++++++++++++
             +  Number       Fractional coordinates        Weight  +
             +-----------------------------------------------------+
             +     1   0.000000   0.000000   0.000000   1.0000000  +
             +     2   4.000000   6.000000   8.000000   5.0000000  +
             +++++++++++++++++++++++++++++++++++++++++++++++++++++++
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'k-points': {'points': [{'qpt': (0.0, 0.0, 0.0), 'weight': 1.0},
                                                             {'qpt': (4.0, 6.0, 4.0), 'weight': 5.0}],
                                                  'num_kpoints': 2}})

    def test_get_applied_efield(self):
        test_text = io.StringIO("""
                          Applied Electric Field (eV/A/e)
                          0.10000   0.10000   0.10000
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'applied_field': (0.1, 0.1, 0.1)})

    def test_charge_spilling(self):
        test_text = io.StringIO("""
 Pseudo atomic calculation performed for Fe 3d6 4s2

 Converged in 29 iterations to a total energy of -490.5382 eV
Charge spilling parameter for spin component 1 = 0.09%
Charge spilling parameter for spin component 2 = 0.44%
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'species_properties':
                                     {'Fe': {'charge_spilling': (0.0009, 0.0044),
                                             'pseudo_atomic_energy': -490.5382}}})

    def test_get_symmetry(self):
        test_text = io.StringIO("""
                           -------------------------------
                               Symmetry and Constraints
                           -------------------------------

                      Cell is a supercell containing 2 primitive cells
                      Maximum deviation from symmetry =  0.00000         ANG

                      Number of symmetry operations   =           1
                      Number of ionic constraints     =           3
                      Point group of crystal =     1: C1, 1, 1
                      Space group of crystal =     1: P1, P 1

             Set iprint > 1 for details on symmetry rotations/translations

                         Centre of mass is constrained
             Set iprint > 1 for details of linear ionic constraints

                         Number of cell constraints= 0
                         Cell constraints are:  1 2 3 4 5 6

        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'constraints': {'number_of_cell_constraints': 0,
                                                     'number_of_ionic_constraints': 3,
                                                     'cell_constraints': (1, 2, 3, 4, 5, 6),
                                                     'com_constrained': True},
                                     'symmetries': {'maximum_deviation_from_symmetry': '0.00000 ANG',
                                                    'number_of_symmetry_operations': 1,
                                                    'point_group_of_crystal': '1: C1, 1, 1',
                                                    'space_group_of_crystal': '1: P1, P 1',
                                                    'n_primitives': 2}})

        test_text = io.StringIO("""
                           -------------------------------
                               Symmetry and Constraints
                           -------------------------------

                      Maximum deviation from symmetry =  0.00000         ANG

                      Number of symmetry operations   =           1
                      Number of ionic constraints     =           3
                      Point group of crystal =     1: C1, 1, 1
                      Space group of crystal =   213: P4_132, P 4bd 2ab 3


                    1 rotation
                 (   1.00000000000   0.00000000000   0.00000000000 )
                 (   0.00000000000   1.00000000000  -0.00000000000 )
                 (  -0.00000000000  -0.00000000000   1.00000000000 )
                    1 displacement
                 (   0.00000000000   0.00000000000  -0.00000000000 )
                      symmetry related atoms:
             Br:    1
             Rb:    1

                    1 rotation
                 (   1.00000000000   0.00000000000   0.00000000000 )
                 (   0.00000000000   1.00000000000   0.00000000000 )
                 (   0.00000000000   0.00000000000   1.00000000000 )
                    1 displacement
                 (   0.00000000000   0.00000000000   0.00000000000 )
                      symmetry related atoms:
             Se:    1    2    3

                         Centre of mass is constrained

            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx....
            x  Species       atom   co-ordinate  constraints.....
            x-------------------------------------------------------------....
            x Se                1       x       143935.2749      0.0000      0.0000
            x Se                1       y            0.0000 143935.2749      0.0000
            x Se                1       z            0.0000      0.0000 143935.2749
            x Se                2       x       143935.2749      0.0000      0.0000
            x Se                2       y            0.0000 143935.2749      0.0000
            x Se                2       z            0.0000      0.0000 143935.2749
            x Se                3       x       143935.2749      0.0000      0.0000
            x Se                3       y            0.0000 143935.2749      0.0000
            x Se                3       z            0.0000      0.0000 143935.2749
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx....

                         Number of cell constraints= 6
                         Cell constraints are:  0 0 0 0 0 0


        """)

        test_dict = parse_castep_file(test_text, Filters.FULL)[0]

        self.assertEqual(test_dict, {'constraints': {'number_of_cell_constraints': 6,
                                                     'number_of_ionic_constraints': 3,
                                                     'cell_constraints': (0, 0, 0, 0, 0, 0),
                                                     'com_constrained': True,
                                                     'ionic_constraints':
                                                     {('Se', 1): [(143935.2749, 0.0, 0.0),
                                                                  (0.0, 143935.2749, 0.0),
                                                                  (0.0, 0.0, 143935.2749)],
                                                      ('Se', 2): [(143935.2749, 0.0, 0.0),
                                                                  (0.0, 143935.2749, 0.0),
                                                                  (0.0, 0.0, 143935.2749)],
                                                      ('Se', 3): [(143935.2749, 0.0, 0.0),
                                                                  (0.0, 143935.2749, 0.0),
                                                                  (0.0, 0.0, 143935.2749)]}},
                                     'symmetries': {'maximum_deviation_from_symmetry': '0.00000 ANG',
                                                    'number_of_symmetry_operations': 1,
                                                    'point_group_of_crystal': '1: C1, 1, 1',
                                                    'space_group_of_crystal': '213: P4_132, P 4bd 2ab 3',
                                                    'symop': [{'displacement': (0.0, 0.0, -0.0),
                                                               'rotation': [(1.0, 0.0, 0.0),
                                                                            (0.0, 1.0, -0.0),
                                                                            (-0.0, -0.0, 1.0)],
                                                               'symmetry_related': [('Br', 1),
                                                                                    ('Rb', 1)]},
                                                              {'displacement': (0.0, 0.0, 0.0),
                                                               'rotation': [(1.0, 0.0, 0.0),
                                                                            (0.0, 1.0, 0.0),
                                                                            (0.0, 0.0, 1.0)],
                                                               'symmetry_related': [('Se', 1),
                                                                                    ('Se', 2),
                                                                                    ('Se', 3)]}]}})

    def test_get_target_stress(self):
        test_text = io.StringIO("""
                         External pressure/stress (GPa)
                          1.00000   2.00000   3.00000
                                    4.00000   5.00000
                                              6.00000
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'target_stress': [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]]})

    def test_delta_scf(self):
        test_text = io.StringIO("""
+-------------------INPUT PARAMETERS-------------------+
Taking band from model   N2-base.check
  MODOS state               1
  MODOS band  nr.           5
  MODOS band has spin       1
  MODOS state               2
  MODOS band  nr.           6
  MODOS band has spin       1
|DeltaSCF| Population of state:     5     1   1.000000
|DeltaSCF| Population of state:     6     1   0.000000

    """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_scf(self):
        test_text = io.StringIO("""
------------------------------------------------------------------------ <-- SCF
SCF loop      Energy           Fermi           Energy gain       Timer   <-- SCF
                               energy          per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -8.43823694E+002  0.00000000E+000                         2.77  <-- SCF
      1  -8.55962165E+002  6.11993396E+000   1.51730885E+000       3.54  <-- SCF
      2  -8.55990255E+002  6.11946292E+000   3.51127330E-003       4.50  <-- SCF
------------------------------------------------------------------------ <-- SCF
        """)
        test_dict = parse_castep_file(test_text, Filters.FULL)[0]

        self.assertEqual(test_dict, {'scf': [[{'energy': -843.823694,
                                               'energy_gain': None,
                                               'fermi_energy': 0.0,
                                               'time': 2.77},
                                              {'energy': -855.962165,
                                               'energy_gain': 1.51730885,
                                               'fermi_energy': 6.11993396,
                                               'time': 3.54},
                                              {'energy': -855.990255,
                                               'energy_gain': 0.0035112733,
                                               'fermi_energy': 6.11946292,
                                               'time': 4.5}]]})

        test_text = io.StringIO("""
------------------------------------------------------------------------ <-- SCF
SCF loop      Energy           Fermi           Energy gain       Timer   <-- SCF
                               energy          per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -2.37153226E+001  0.00000000E+000                         0.17  <-- SCF
      1  -3.23437859E+001 -1.29587284E+000   4.31423163E+000       0.17  <-- SCF
 Density was not mixed in this cycle
      2  -3.23439432E+001 -1.29587691E+000   7.86354909E-005       0.18  <-- SCF
 Norm of density residual is    9.1451037234902971E-002
      3  -3.20352173E+001 -1.10248324E+000  -1.54362953E-001       0.18  <-- SCF
------------------------------------------------------------------------ <-- SCF
Total energy has converged after 11 SCF iterations.
        """)
        test_dict = parse_castep_file(test_text, Filters.FULL)[0]

        self.assertEqual(test_dict, {'scf': [[{'energy': -23.7153226,
                                               'energy_gain': None,
                                               'fermi_energy': 0.0,
                                               'time': 0.17},
                                              {'density_residual': None,
                                               'energy': -32.3437859,
                                               'energy_gain': 4.31423163,
                                               'fermi_energy': -1.29587284,
                                               'time': 0.17},
                                              {'density_residual': 0.09145103723490297,
                                               'energy': -32.3439432,
                                               'energy_gain': 7.86354909e-05,
                                               'fermi_energy': -1.29587691,
                                               'time': 0.18},
                                              {'energy': -32.0352173,
                                               'energy_gain': -0.154362953,
                                               'fermi_energy': -1.10248324,
                                               'time': 0.18}]]})

        test_text = io.StringIO("""
------------------------------------------------------------------------ <-- SCF
SCF loop      Energy           Fermi           Energy gain       Timer   <-- SCF
                               energy          per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -8.45018104E+002  0.00000000E+000                         3.81  <-- SCF
Starting SCF cycle     1 of up to    30
 no. bands in each block=           7
Kinetic eigenvalue #   1 =     0.19929544E+02
Kinetic eigenvalue #   2 =     0.12921903E+02
 Calculating the R matrix for the precon Sinv operator
 Diagonalising expanded subspace
 Copying updated data back
eigenvalue    1 init= -27.89     fin= -28.57     change= 0.6761
eigenvalue    2 init= -19.95     fin= -20.19     change= 0.2477
 Checking convergence criteria
 Diagonalising expanded subspace
 Copying updated data back
eigenvalue    1 init= -27.89     fin= -28.61     change= 0.7169
eigenvalue    2 init= -19.95     fin= -20.22     change= 0.2696
 Checking convergence criteria
(Entering electronic_find_fermi_free)
Fermi energy = -1.0921E+000 eV [lower bound; range =  1.43E-014 eV]
(Leaving electronic_find_fermi_free)
Calculating KE and non-local eigenvalues to find total energy

End of SCF cycle energies
Exchange-correlation energy      =      -232.32975595141911640 eV
+Hartree energy                  =       555.19121174858389622 eV
+Local pseudopotential energy    =     -1615.37738857285035010 eV
----------------------------------
Potential energy (total)         =     -1446.35569943465020515 eV

+Kinetic energy                  =       539.68227753812016090 eV
+Non-local energy                =       126.65142841537570462 eV
+Electronic entropy term (-TS)   =        -0.00000000000000212 eV
+Ewald energy (const)            =       -74.10820452501279476 eV
+non-Coulombic energy (const)    =         6.36149657571428406 eV
----------------------------------
Total free energy (E-TS)         =      -847.76870143045277928 eV

NB est. 0K energy (E-0.5TS)      =      -847.76870143045277928 eV

(XC correction to eigenvalue sum =        65.01253419559009217 eV)
(Apolar corr to eigenvalue sum   =         0.00000000000000000 eV)
(Hubbard U correction to eigenvalu         0.00000000000000000 eV)

      1  -8.47768701E+002 -1.09214177E+000   3.05621978E-001       3.84  <-- SCF
------------------------------------------------------------------------ <-- SCF
        """)
        test_dict = parse_castep_file(test_text, Filters.FULL)[0]

        self.assertEqual(test_dict, {'scf': [[{'energy': -845.018104,
                                               'energy_gain': None,
                                               'fermi_energy': 0.0,
                                               'time': 3.81},
                                              {'debug_info': {'contributions': {
                                                  'apolar_correction': 0.0,
                                                  'electronic_entropy_term_ts': -2.12e-15,
                                                  'ewald_energy_const': -74.1082045250128,
                                                  'exchange_correlation_energy': -232.32975595141912,
                                                  'fermi_energy': -1.0921,
                                                  'hartree_energy': 555.1912117485839,
                                                  'hubbard_u_correction': 0.0,
                                                  'kinetic_energy': 539.6822775381202,
                                                  'local_pseudopotential_energy': -1615.3773885728504,
                                                  'non_coulombic_energy_const': 6.361496575714284,
                                                  'non_local_energy': 126.6514284153757,
                                                  'potential_energy_total': -1446.3556994346502,
                                                  'total_free_energy_e_ts': -847.7687014304528,
                                                  'xc_correction': 65.01253419559009
                                              },
                                                              'eigenvalue': [[{'change': 0.6761,
                                                                               'final': -28.57,
                                                                               'initial': -27.89},
                                                                              {'change': 0.2477,
                                                                               'final': -20.19,
                                                                               'initial': -19.95}],
                                                                             [{'change': 0.7169,
                                                                               'final': -28.61,
                                                                               'initial': -27.89},
                                                                              {'change': 0.2696,
                                                                               'final': -20.22,
                                                                               'initial': -19.95}]],
                                                              'kinetic_eigenvalue': [19.929544,
                                                                                     12.921903],
                                                              'no_bands': 7},
                                               'energy': -847.768701,
                                               'energy_gain': 0.305621978,
                                               'fermi_energy': -1.09214177,
                                               'time': 3.84}]]}
                         )

    def test_get_bsc_scf(self):
        test_text = io.StringIO("""
Calculating finite basis set correction with  3 cut-off energies.
Calculating total energy with cut-off of  150.000 eV.
Calculating approximate eigenstates for fixed initial Hamiltonian
Cut-off for approx. calculation is   80.000 eV
Resetting cut-off to  149.802 eV
------------------------------------------------------------------------ <-- SCF
SCF loop      Energy           Fermi           Energy gain       Timer   <-- SCF
                               energy          per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -2.16330992E+002  0.00000000E+000                         1.21  <-- SCF
      1  -2.16495167E+002  4.14887478E+000   8.20874626E-002       1.33  <-- SCF
------------------------------------------------------------------------ <-- SCF

Final energy, E             =  -216.4191364770     eV
Final free energy (E-TS)    =  -216.4201784468     eV
(energies not corrected for finite basis set)

NB est. 0K energy (E-0.5TS)      =  -216.4196574619     eV

Calculating total energy with cut-off of  155.000 eV.
------------------------------------------------------------------------ <-- SCF
SCF loop      Energy           Fermi           Energy gain       Timer   <-- SCF
                               energy          per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -2.16419103E+002  0.00000000E+000                         2.75  <-- SCF
      1  -2.16446853E+002  4.35498760E+000   1.38746578E-002       2.86  <-- SCF
------------------------------------------------------------------------ <-- SCF

Final energy, E             =  -216.4458405943     eV
Final free energy (E-TS)    =  -216.4469466955     eV
(energies not corrected for finite basis set)

NB est. 0K energy (E-0.5TS)      =  -216.4463936449     eV

Calculating total energy with cut-off of  160.000 eV.
------------------------------------------------------------------------ <-- SCF
SCF loop      Energy           Fermi           Energy gain       Timer   <-- SCF
                               energy          per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -2.16445805E+002  0.00000000E+000                         3.63  <-- SCF
      1  -2.16468756E+002  4.35489704E+000   1.14756678E-002       3.77  <-- SCF
------------------------------------------------------------------------ <-- SCF

Final energy, E             =  -216.4677199357     eV
Final free energy (E-TS)    =  -216.4688283736     eV
(energies not corrected for finite basis set)

NB est. 0K energy (E-0.5TS)      =  -216.4682741546     eV

 For future reference: finite basis dEtot/dlog(Ecut) =      -0.749584eV
 Total energy corrected for finite basis set =    -216.469505 eV

        """)

        test_dict = parse_castep_file(test_text, Filters.FULL)[0]

        self.assertEqual(test_dict, {'bsc_scf': [[{'energy': -216.330992,
                                                   'energy_gain': None,
                                                   'fermi_energy': 0.0,
                                                   'time': 1.21},
                                                  {'energy': -216.495167,
                                                   'energy_gain': 0.0820874626,
                                                   'fermi_energy': 4.14887478,
                                                   'time': 1.33}],
                                                 [{'energy': -216.419103,
                                                   'energy_gain': None,
                                                   'fermi_energy': 0.0,
                                                   'time': 2.75},
                                                  {'energy': -216.446853,
                                                   'energy_gain': 0.0138746578,
                                                   'fermi_energy': 4.3549876,
                                                   'time': 2.86}]],
                                     'bsc_energies': {'est_0K': [-216.4196574619,
                                                                 -216.4463936449],
                                                      'final_energy': [-216.419136477,
                                                                       -216.4458405943],
                                                      'free_energy': [-216.4201784468,
                                                                      -216.4469466955]},
                                     'dedlne': -0.749584,
                                     'energies': {'est_0K': [-216.4682741546],
                                                  'final_basis_set_corrected': [-216.469505],
                                                  'final_energy': [-216.4677199357],
                                                  'free_energy': [-216.4688283736]},
                                     'scf': [{'energy': -216.445805,
                                              'energy_gain': None,
                                              'fermi_energy': 0.0,
                                              'time': 3.63},
                                             {'energy': -216.468756,
                                              'energy_gain': 0.0114756678,
                                              'fermi_energy': 4.35489704,
                                              'time': 3.77}]})

    def test_get_dipole_scf(self):
        test_text = io.StringIO("""
------------------------------------------------------------------------ <-- SCF
SCF loop      Energy           Fermi           Energy gain       Timer   <-- SCF
                               energy          per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -3.02130061E+002  0.00000000E+000                         3.32  <-- SCF
      1  -3.43042177E+002 -7.89452039E+000   2.04560579E+001       3.39  <-- SCF
      2  -3.43046622E+002 -7.89536400E+000   2.22269514E-003       3.44  <-- SCF
 Correcting PBC dipole-dipole with self-consistent method: dE =       0.11814 eV
------------------------------------------------------------------------ <-- SCF
        """)
        test_dict = parse_castep_file(test_text, Filters.FULL)[0]

        self.assertEqual(test_dict, {'scf': [[{'energy': -302.130061,
                                               'energy_gain': None,
                                               'fermi_energy': 0.0,
                                               'time': 3.32},
                                              {'energy': -343.042177,
                                               'energy_gain': 20.4560579,
                                               'fermi_energy': -7.89452039,
                                               'time': 3.39},
                                              {'dipole_corr_energy': 0.11814,
                                               'energy': -343.046622,
                                               'energy_gain': 0.00222269514,
                                               'fermi_energy': -7.895364,
                                               'time': 3.44}]]})

    def test_get_constrained_scf(self):
        test_text = io.StringIO("""
------------------------------------------------------------------------ <-- SCF
SCF loop      Energy           Fermi           Energy gain       Timer   <-- SCF
                               energy          per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -8.74382993E+002 -9.34072274E+000                         3.41  <-- SCF
      1  -8.74894712E+002 -9.12958602E+000   5.11719101E-001      12.16  <-- SCF
 Total constraint energy:   1.0839687043738317E-005 eV
      2  -8.74898726E+002 -9.14432144E+000   4.01413122E-003      23.10  <-- SCF
 Total constraint energy:   2.4886530082978212E-008 eV
------------------------------------------------------------------------ <-- SCF

        """)
        test_dict = parse_castep_file(test_text, Filters.FULL)[0]

        self.assertEqual(test_dict, {'scf': [[{'energy': -874.382993,
                                               'energy_gain': None,
                                               'fermi_energy': -9.34072274,
                                               'time': 3.41},
                                              {'constraint_energy': 1.0839687043738317e-05,
                                               'energy': -874.894712,
                                               'energy_gain': 0.511719101,
                                               'fermi_energy': -9.12958602,
                                               'time': 12.16},
                                              {'constraint_energy': 2.4886530082978212e-08,
                                               'energy': -874.898726,
                                               'energy_gain': 0.00401413122,
                                               'fermi_energy': -9.14432144,
                                               'time': 23.1}]]})

    def test_get_occupancy(self):
        test_text = io.StringIO("""
Bands above band 2 are completely empty                           <- occ
Band energies and occupancies for bands close to Fermi energy     <- occ
Smearing width is  0.200 eV                                       <- occ
Spin 1, kpoint ( 0.000000  0.000000  0.000000 ) weight = 1.000000
+--------+-------------------+----------------+
|  Band  |   Eigenvalue      |    Occupancy   |                   <- occ
+--------+-------------------+----------------+                   <- occ
|     1  |   -.103844E+02    |   1.00000      |                   <- occ
|     2  |   0.326330E+00    |  0.111022E-15  |                   <- occ
+--------+-------------------+----------------+                   <- occ
Have a nice day.
        """)

        test_dict = parse_castep_file(test_text, Filters.FULL)[0]

        self.assertEqual(test_dict, {'occupancies': [[{'band': 1,
                                                       'eigenvalue': -10.3844,
                                                       'occupancy': 1.0},
                                                      {'band': 2,
                                                       'eigenvalue': 0.32633,
                                                       'occupancy': 1.11022e-16}]]})

    def test_wvfn_get_line_min(self):
        test_text = io.StringIO("""
+------------------- WAVEFUNCTION LINE MINIMISATION --------------------+<- line
| Initial energy = -1.031551E+003 eV; initial dE/dstep = -2.376E-001 eV |<- line
|                                                                       |<- line
|            1st step    2nd step    3rd step    4th step    5th step   |<- line
+--------+--------------------------------------------------------------+<- line
| step   |  1.500E+00   1.276E+00* unnecessary unnecessary unnecessary  |<- line
| gain   |  1.469E-01   1.518E-01* unnecessary unnecessary unnecessary  |<- line
+--------+--------------------------------------------------------------+<- line
 * indicates the final, accepted state (should have the lowest energy)
            """)

        test_dict = parse_castep_file(test_text, Filters.FULL)[0]

        self.assertEqual(test_dict, {'wvfn_line_min': [{'gain': (0.1469, 0.1518),
                                                        'init_de_dstep': -0.2376,
                                                        'init_energy': -1031.551,
                                                        'steps': (1.5, 1.276)}]})

    def test_get_energies(self):
        test_text = io.StringIO("""
Final energy =  -1267.604578357     eV
Final energy, E             =  -855.4591023999     eV
Final free energy (E-TS)    =  -855.4625664830     eV
(energies not corrected for finite basis set)

(SEDC) Total Energy Correction : -0.702746E+00 eV

Dispersion corrected final energy* =  -1268.307324500     eV
NB est. 0K energy (E-0.5TS)      =  -855.4608344414     eV

 For future reference: finite basis dEtot/dlog(Ecut) =      -3.335211eV
 Total energy corrected for finite basis set =    -855.471052 eV
        """)

# Dispersion corrected final energy*, Ecor          =  -1034.338872426     eV
# Dispersion corrected final free energy* (Ecor-TS) =  -1134.338872426     eV
# NB dispersion corrected est. 0K energy* (Ecor-0.5TS) =  -1234.338872426     eV

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'dedlne': -3.335211,
                                     'energies': {'disperson_corrected': [-1268.3073245],
                                                  'est_0K': [-855.4608344414],
                                                  'final_basis_set_corrected': [-855.471052],
                                                  'final_energy': [-1267.604578357,
                                                                   -855.4591023999],
                                                  'free_energy': [-855.462566483],
                                                  'sedc_correction': [-0.702746]}})

    def test_get_forces(self):
        test_text = io.StringIO("""
 ************************************** Forces **************************************
 *                                                                                  *
 *                           Cartesian components (eV/A)                            *
 * -------------------------------------------------------------------------------- *
 *                         x                    y                    z              *
 *                                                                                  *
 * Si              1     -2.27362             -0.18351             -0.11133         *
 * Si              2     -2.00300             -0.71954             -0.89066         *
 * Si              3     -1.83082             -0.17303             -0.91369         *
 *                                                                                  *
 ************************************************************************************

 ********************************* Fun Forces ***************************************
 *                                                                                  *
 *                           Cartesian components (eV/A)                            *
 * -------------------------------------------------------------------------------- *
 *                         x                    y                    z              *
 *                                                                                  *
 * Si              1      1.00000              1.00000              1.00000         *
 * Si              2      1.00000              1.00000              1.00000         *
 * Si              3      1.00000              1.00000              1.00000         *
 *                                                                                  *
 ************************************************************************************


 ************** External Efield and/or dipole ***************
 *                                                          *
 *               Cartesian components (eV/A)                *
 * -------------------------------------------------------- *
 *                         x            y            z      *
 *                                                          *
 * H               1      0.00000      0.00000      0.00000 *
 * H               2      0.00000      0.00000      0.00000 *
 *                                                          *
 ************************************************************
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'forces':
                                     {'non_descript': [{
                                         ('Si', 1): (-2.27362, -0.18351, -0.11133),
                                         ('Si', 2): (-2.003, -0.71954, -0.89066),
                                         ('Si', 3): (-1.83082, -0.17303, -0.91369)
                                     }],
                                      'fun': [{
                                          ('Si', 1): (1.0, 1.0, 1.0),
                                          ('Si', 2): (1.0, 1.0, 1.0),
                                          ('Si', 3): (1.0, 1.0, 1.0)
                                      }]
                                      }
                                     })

    def test_get_forces_constrained(self):
        test_text = io.StringIO("""
 ******************************** Constrained Forces ********************************
 *                                                                                  *
 *                           Cartesian components (eV/A)                            *
 * -------------------------------------------------------------------------------- *
 *                         x                    y                    z              *
 *                                                                                  *
 * Si              1      1.00000(cons'd)      2.00000(cons'd)      3.00000(cons'd) *
 * Si              2      0.00818              0.26933              0.30025         *
 *                                                                                  *
 ************************************************************************************

        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'forces':
                                     {'constrained': [{
                                         ('Si', 1): (1.0, 2.0, 3.0),
                                         ('Si', 2): (0.00818, 0.26933, 0.30025)}
                                                      ]}
                                     })

    def test_get_forces_labelled(self):
        test_text = io.StringIO("""
 ************************************** Forces **************************************
 *                                                                                  *
 *                           Cartesian components (eV/A)                            *
 * -------------------------------------------------------------------------------- *
 *                         x                    y                    z              *
 *                                                                                  *
 * H [H1]          1      0.00000              0.00000             -0.06470         *
 * H [H2]          2     -0.00000             -0.00000              0.06470         *
 *                                                                                  *
 ************************************************************************************
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'forces': {'non_descript': [{('H [H1]', 1): (0.0, 0.0, -0.0647),
                                                                  ('H [H2]', 2): (-0.0, -0.0, 0.0647)}]
                                                }})

    def test_get_forces_mixed(self):
        test_text = io.StringIO("""
 ******************************** Symmetrised Forces ********************************
 *                                                                                  *
 *                           Cartesian components (eV/A)                            *
 * -------------------------------------------------------------------------------- *
 *                         x                    y                    z              *
 *                                                                                  *
 * Si              1      0.00000 (mixed)      0.00000 (mixed)      0.00000 (mixed) *
 * Si              2      0.00000 (mixed)      0.00000 (mixed)      0.00000 (mixed) *
 * Ge              1      0.00000 (mixed)      0.00000 (mixed)      0.00000 (mixed) *
 * Ge              2      0.00000 (mixed)      0.00000 (mixed)      0.00000 (mixed) *
 *                                                                                  *
 ************************************************************************************
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'forces':
                                     {'symmetrised': [{('Ge', 1): (0.0, 0.0, 0.0),
                                                      ('Ge', 2): (0.0, 0.0, 0.0),
                                                      ('Si', 1): (0.0, 0.0, 0.0),
                                                      ('Si', 2): (0.0, 0.0, 0.0)}]
                                      }})

    def test_get_stress(self):
        test_text = io.StringIO("""
 ***************** Stress Tensor *****************
 *                                               *
 *          Cartesian components (GPa)           *
 * --------------------------------------------- *
 *             x             y             z     *
 *                                               *
 *  x     10.491143     -1.300645     -2.326648  *
 *  y     -1.300645      3.068913     -5.026993  *
 *  z     -2.326648     -5.026993      6.215774  *
 *                                               *
 *  Pressure:   -6.5919                          *
 *                                               *
 *************************************************

 *************** Fun Stress Tensor ***************
 *                                               *
 *          Cartesian components (GPa)           *
 * --------------------------------------------- *
 *             x             y             z     *
 *                                               *
 *  x     10.882675      0.000000      0.000000  *
 *  y      0.000000     10.882675     -0.000000  *
 *  z      0.000000     -0.000000     10.882675  *
 *                                               *
 *  Pressure:  -10.8827                          *
 *                                               *
 *************************************************

        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'stresses':
                                     {
                                         'non_descript': [(10.491143, -1.300645, -2.326648,
                                                          3.068913, -5.026993,
                                                          6.215774)],
                                         'fun': [(10.882675, 0.0, 0.0,
                                                 10.882675, -0.0,
                                                 10.882675)]
                                     }
                                     }
                         )

    def test_get_md_data(self):
        test_text = io.StringIO("""
================================================================================
 Starting MD iteration          1 ...
================================================================================

+---------------- MEMORY AND SCRATCH DISK ESTIMATES PER PROCESS --------------+
|                                                     Memory          Disk    |
| Model and support data                               27.2 MB         0.0 MB |
| Molecular Dynamics requirements                      13.4 MB         0.0 MB |
|                                               ----------------------------- |
| Approx. total storage required per process           40.6 MB         0.0 MB |
|                                                                             |
| Requirements will fluctuate during execution and may exceed these estimates |
+-----------------------------------------------------------------------------+


                           -------------------------------
                                      Unit Cell
                           -------------------------------
        Real Lattice(A)              Reciprocal Lattice(1/A)
     5.4300000     0.0000000     0.0000000        1.157124366   0.000000000   0.000000000
     0.0000000     5.4300000     0.0000000        0.000000000   1.157124366   0.000000000
     0.0000000     0.0000000     5.4300000        0.000000000   0.000000000   1.157124366

                       Lattice parameters(A)       Cell Angles
                    a =      5.430000          alpha =   90.000000
                    b =      5.430000          beta  =   90.000000
                    c =      5.430000          gamma =   90.000000

                Current cell volume =           160.103007 A**3
                            density =             1.403372 amu/A**3
                                    =             2.330353 g/cm^3

                           -------------------------------
                                     Cell Contents
                           -------------------------------

            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x  Element    Atom        Fractional coordinates of atoms    x
            x            Number           u          v          w        x
            x------------------------------------------------------------x
            x   Si         1          0.001291   0.000320   0.001059     x
            x   Si         2          0.000729   0.504323   0.520521     x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

------------------------------------------------------------------------ <-- SCF
SCF loop      Energy           Fermi           Energy gain       Timer   <-- SCF
                               energy          per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -8.54989696E+002  0.00000000E+000                        17.06  <-- SCF
      1  -8.55716038E+002  6.32845976E+000   9.07927915E-002      17.93  <-- SCF
      2  -8.55717590E+002  6.32839049E+000   1.94010456E-004      18.95  <-- SCF
------------------------------------------------------------------------ <-- SCF

Final energy, E             =  -855.4197401755     eV
Final free energy (E-TS)    =  -855.4236056162     eV
(energies not corrected for finite basis set)

NB est. 0K energy (E-0.5TS)      =  -855.4216728959     eV


 ************************************** Forces **************************************
 *                                                                                  *
 *                           Cartesian components (eV/A)                            *
 * -------------------------------------------------------------------------------- *
 *                         x                    y                    z              *
 *                                                                                  *
 * Si              1     -0.05358             -0.04038              0.69168         *
 * Si              2      0.72539              0.35380             -1.12992         *
 *                                                                                  *
 ************************************************************************************

 ***************** Stress Tensor *****************
 *                                               *
 *          Cartesian components (GPa)           *
 * --------------------------------------------- *
 *             x             y             z     *
 *                                               *
 *  x      2.029699      1.862602      3.129082  *
 *  y      1.862602     -6.100259      5.232356  *
 *  z      3.129082      5.232356     -7.576534  *
 *                                               *
 *  Pressure:    3.8824                          *
 *                                               *
 *************************************************

            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x                                               MD Data:     x
            x                                                            x
            x              time :      0.002000                   ps     x
            x                                                            x
            x   Potential Energy:   -855.432091                   eV     x
            x   Kinetic   Energy:      0.673458                   eV     x
            x   Total     Energy:   -854.758633                   eV     x
            x           Enthalpy:   -854.758633                   eV     x
            x   Hamilt    Energy:   -854.677308                   eV     x
            x                                                            x
            x        Temperature:    651.262915                    K     x
            x      T/=0 Pressure:      4.323390                  GPa     x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


--------------------------------------------------------------------------------
 ... finished MD iteration          1

        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'memory_estimate': [{'model_and_support_data': {'disk': 0.0, 'memory': 27.2},
                                                          'molecular_dynamics_requirements': {'disk': 0.0, 'memory': 13.4}}],
                                     'md': [
                                         {'enthalpy': -854.758633,
                                          'hamilt_energy': -854.677308,
                                          'kinetic_energy': 0.673458,
                                          'potential_energy': -855.432091,
                                          'temperature': 651.262915,
                                          'total_energy': -854.758633,
                                          'energies': {'est_0K': [-855.4216728959],
                                                       'final_energy': [-855.4197401755],
                                                       'free_energy': [-855.4236056162]},
                                          'forces': {'non_descript': [{('Si', 1): (-0.05358, -0.04038, 0.69168),
                                                                       ('Si', 2): (0.72539, 0.3538, -1.12992)}]},
                                          'cell': {'cell_angles': [90.0, 90.0, 90.0],
                                                   'density_amu': 1.403372,
                                                   'density_g': 2.330353,
                                                   'lattice_parameters': [5.43, 5.43, 5.43],
                                                   'real_lattice': [(5.43, 0.0, 0.0),
                                                                    (0.0, 5.43, 0.0),
                                                                    (0.0, 0.0, 5.43)],
                                                   'recip_lattice': [(1.157124366, 0.0, 0.0),
                                                                     (0.0, 1.157124366, 0.0),
                                                                     (0.0, 0.0, 1.157124366)],
                                                   'volume': 160.103007},
                                          'positions': {('Si', 1): (0.001291, 0.00032, 0.001059),
                                                        ('Si', 2): (0.000729, 0.504323, 0.520521)},
                                          'stresses': {'non_descript': [(2.029699, 1.862602, 3.129082, -6.100259, 5.232356, -7.576534)]},
                                          'time': 0.002}]}
                         )

    def test_get_pimd_data(self):
        test_text = io.StringIO("""
================================================================================
 Starting PIMD iteration          1 ...
================================================================================

                         -------------------------------
                                 Centroid positions
                         -------------------------------

          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          x  Element    Atom        Cartesian  MD  Data (user units)       x
          x            Number           X          Y          Z            x
          x----------------------------------------------------------------x
          x   Si      1       1.80684347   6.07556751  -1.07812118     <-R x
          x   Si      2       2.03459465   6.43398655   1.37995423     <-R x
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

   xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   x  Element  Atom    RGY value                  RGY Eigenvector              x
   x          Number   (user units)              X          Y          Z       x
   x---------------------------------------------------------------------------x
   x   Si      1     0.00000000     0.00000007   0.00000006   0.00000007 <-RGY x
   x   Si      1     0.00000000     0.00000006   0.00000004   0.00000006 <-RGY x
   x   Si      1     0.00000000     0.00000007   0.00000006   0.00000007 <-RGY x
   x   Si      2     0.00000000     0.00000007   0.00000006   0.00000007 <-RGY x
   x   Si      2     0.00000000     0.00000006   0.00000004   0.00000006 <-RGY x
   x   Si      2     0.00000000     0.00000007   0.00000006   0.00000007 <-RGY x
   xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


                          -------------------------------
                                 Centroid velocities
                          -------------------------------

          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          x  Element    Atom        Cartesian  MD  Data (user units)       x
          x            Number           X          Y          Z            x
          x----------------------------------------------------------------x
          x   Si      1       1.06922937   0.04473351  -0.53997455     <-V x
          x   Si      2      -1.06922937  -0.04473351   0.53997455     <-V x
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

                          -------------------------------
                                  Centroid forces
                          -------------------------------

          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          x  Element    Atom        Cartesian  MD  Data (user units)       x
          x            Number           X          Y          Z            x
          x----------------------------------------------------------------x
          x   Si      1       0.68288756   1.02202138   0.01854509     <-F x
          x   Si      2      -0.69345522  -1.02350166  -0.02338859     <-F x
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx



                          -------------------------------
                                   Centroid data
                          -------------------------------

         Centre of mass of centroids constrained
         Num. degrees of freedom removed by centroid constraints:  3.0

          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
          x                                               MD Data:         x
          x                                                                x
          x                                                                x
          x   Potential Energy:   -215.059708                   eV <-PI    x
          x   Kinetic   Energy:      0.008772                   eV <-PI    x
          x   Total     Energy:   -215.050937                   eV <-PI    x
          x   Hamilt    Energy:   -215.050937                   eV <-PI    x
          x   Spring    Energy:      0.000000                   eV <-PI    x
          x                                                                x
          x        Temperature:     22.620304                    K <-PI    x
          xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


--------------------------------------------------------------------------------
 ... finished PIMD iteration          1
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_mulliken(self):
        test_text = io.StringIO("""
     Atomic Populations (Mulliken)
     -----------------------------
Species          Ion     s       p       d       f      Total   Charge (e)
==========================================================================
  Si              1     1.319   2.681   0.000   7.000   4.000     0.000
  Si              2     1.319   2.681   3.000   0.000   4.000     2.000
==========================================================================


        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'mulliken_popn': {
            ('Si', 1): {'spin_sep': False,
                        's': 1.319,
                        'p': 2.681,
                        'd': 0.0,
                        'f': 7.0,
                        'total': 4.0,
                        'charge': 0.0,
                        'spin': None},
            ('Si', 2): {'spin_sep': False,
                        's': 1.319,
                        'p': 2.681,
                        'd': 3.0,
                        'f': 0.0,
                        'total': 4.0,
                        'charge': 2.0,
                        'spin': None}}
                                     }
                         )

    def test_get_mulliken_spin(self):
        test_text = io.StringIO("""
     Atomic Populations (Mulliken)
     -----------------------------
Species          Ion Spin      s       p       d       f      Total   Charge(e)   Spin(hbar/2)
==============================================================================================
  Cr              1   up:     0.398   0.037   3.391   0.000   3.826    -0.000        1.653
                  1   dn:     0.341   0.097   1.735   0.000   2.174
  Cr              2   up:     0.341   0.097   1.735   0.000   2.174     0.000       -1.653
                  2   dn:     0.398   0.037   3.391   0.000   3.826
==============================================================================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'mulliken_popn':
                                     {('Cr', 1): {'charge': -0.0,
                                                  'dn_d': 1.735,
                                                  'dn_f': 0.0,
                                                  'dn_p': 0.097,
                                                  'dn_s': 0.341,
                                                  'dn_total': 2.174,
                                                  'spin': 1.653,
                                                  'spin_sep': True,
                                                  'total': 6.0,
                                                  'up_d': 3.391,
                                                  'up_f': 0.0,
                                                  'up_p': 0.037,
                                                  'up_s': 0.398,
                                                  'up_total': 3.826},
                                      ('Cr', 2): {'charge': 0.0,
                                                  'dn_d': 3.391,
                                                  'dn_f': 0.0,
                                                  'dn_p': 0.037,
                                                  'dn_s': 0.398,
                                                  'dn_total': 3.826,
                                                  'spin': -1.653,
                                                  'spin_sep': True,
                                                  'total': 6.0,
                                                  'up_d': 1.735,
                                                  'up_f': 0.0,
                                                  'up_p': 0.097,
                                                  'up_s': 0.341,
                                                  'up_total': 2.174}}})

    def test_get_orbital_populations(self):
        test_text = io.StringIO("""
            Orbital Populations
     Ion    Atom   Orbital             Charge
  -------------------------------------------
      N     1      S                    1.390
      N     1      Px                   1.329
      N     1      Py                   0.979
      N     1      Pz                   1.284
      C     2      S                    3.000
      C     2      Px                   2.000
  -------------------------------------------
                           Total:      19.999
  -------------------------------------------
The total projected population is   19.999   0.000

        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'orbital_popn':
                                     {'total': 19.999,
                                      ('N', 1): {'Px': 1.329,
                                                 'Py': 0.979,
                                                 'Pz': 1.284,
                                                 'S': 1.39},
                                      ('C', 2): {'S': 3.0,
                                                 'Px': 2.0}}})

    def test_get_bond(self):
        test_text = io.StringIO("""
                 Bond                   Population      Length (A)
======================================================================
              Si 1 -- Si 2                   3.06        2.33434
              C  1 -- Si 1                  99.10        3.14159
======================================================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'bonds': {(('C', 1), ('Si', 1)): {'length': 3.14159,
                                                                       'population': 99.1},
                                               (('Si', 1), ('Si', 2)): {'length': 2.33434,
                                                                        'population': 3.06}}})

    def test_get_spin_bond(self):
        test_text = io.StringIO("""
                 Bond                   Population        Spin       Length (A)
================================================================================
              Cr 1 -- Cr 2                   1.66        -0.15          2.48636
================================================================================

        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'bonds': {(('Cr', 1), ('Cr', 2)): {'length': 2.48636,
                                                                        'population': 1.66,
                                                                        'spin': -0.15}}})

    def test_get_pair_params(self):
        test_text = io.StringIO("""
   ************************     PairParams     ************************
   *                                                                  *
   *                               Two Body                           *
   *         H  -H       H  -He      He -H       He -He               *
   *    r      8.51250     8.51250     8.51250     8.51250   A        * <--   LJ
   *    e      0.00009     0.00017     0.00017     0.00017   eV       * <--   LJ
   *    s      1.00000     2.00000     2.00000     2.00000   A        * <--   LJ
   ********************************************************************
   *                             Three Body                           *
   *                            H   H   H                             *
   *    l                      1.0000000000                           * <--   SW
   *    c                      0.1000000000                           * <--   SW
   *    C                      0.0000000000                           * <--   SW
   ********************************************************************
   *                               SW Units                           *
   *    e                      2.1682052121                  eV       * <--   SW
   *    s                      0.1336587852                  A        * <--   SW
   ********************************************************************
   *    A                      0.4000000000                           * <--   DZ
   *    B                      0.1000000000                           * <--   DZ
   *    C                      1.5000000000                           * <--   DZ
   *    D                      0.1000000000                           * <--   DZ
   * CUT1                      1.4000000000                           * <--   DZ
   * CUT2                      3.0000000000                           * <--   DZ
   *  EPS                      0.0002721139                  eV       * <--   DZ
   *  SIG                      4.0000000000                  A        * <--   DZ
   *    m                     18.0000000000                           * <--   DZ
   ********************************************************************

SR ************************     PairParams     ************************
SR *                                                                  *
SR *                               Two Body                           *
SR *                               H                                  *
SR *    r                      3.0000000000                  A        * <--  SHO
SR *  r_d                      3.0000000000                  A        * <--  SHO
SR *    k                      1.0000000000                  eV/A^2   * <--  SHO
SR ********************************************************************

WL ************************     PairParams     ************************
WL *                                                                  *
WL *                               Two Body                           *
WL *                               H                                  *
WL *    r                      3.0000000000                  A        * <--  SHO
WL *  r_d                      3.0000000000                  A        * <--  SHO
WL *    k                      1.0000000000                  eV/A^2   * <--  SHO
WL ********************************************************************
 VERBOSE    = T
 NL         = F
 FD_CHECK   = F
 PRINT_POT  = T
 FIXED_CELL = T
 1BODY      = T
 2BODY      = F
 3BODY      = F
 EWALD      = F
 SPINS      = F
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'pair_params': [{'DZ': {'A': 0.4,
                                                             'B': 0.1,
                                                             'C': 1.5,
                                                             'CUT1': 1.4,
                                                             'CUT2': 3.0,
                                                             'D': 0.1,
                                                             'EPS': 0.0002721139,
                                                             'SIG': 4.0,
                                                             'm': 18.0},
                                                      'LJ': {'e': {('H', 'H'): 9e-05,
                                                                   ('H', 'He'): 0.00017,
                                                                   ('He', 'H'): 0.00017,
                                                                   ('He', 'He'): 0.00017},
                                                             'r': {('H', 'H'): 8.5125,
                                                                   ('H', 'He'): 8.5125,
                                                                   ('He', 'H'): 8.5125,
                                                                   ('He', 'He'): 8.5125},
                                                             's': {('H', 'H'): 1.0,
                                                                   ('H', 'He'): 2.0,
                                                                   ('He', 'H'): 2.0,
                                                                   ('He', 'He'): 2.0}},
                                                      'SW': {'C': {('H', 'H', 'H'): 0.0},
                                                             'c': {('H', 'H', 'H'): 0.1},
                                                             'e': 2.1682052121,
                                                             'l': {('H', 'H', 'H'): 1.0},
                                                             's': 0.1336587852}},
                                                     {'SR_SHO': {'k': {('H',): 1.0},
                                                                 'r': {('H',): 3.0},
                                                                 'r_d': {('H',): 3.0}}},
                                                     {'WL_SHO': {'k': {('H',): 1.0},
                                                                 'r': {('H',): 3.0},
                                                                 'r_d': {('H',): 3.0}}}]})

    def test_get_vibrational_frequencies(self):
        test_text = io.StringIO("""
 ==============================================================================
 +                           Vibrational Frequencies                          +
 +                           -----------------------                          +
 +                                                                            +
 + Performing frequency calculation at  4 wavevectors (q-pts)                 +
 + ========================================================================== +
 +                                                                            +
 + -------------------------------------------------------------------------- +
 +  q-pt=    1 (  0.000000  0.000000  0.000000)     0.2500000000              +
 +  q->0 along (  0.500000  0.500000  0.000000)                               +
 + -------------------------------------------------------------------------- +
 +  Acoustic sum rule correction <   3.703446 cm-1 applied                    +
 +     N      Frequency irrep.    ir intensity active            raman active +
 +                (cm-1)         ((D/A)**2/amu)                               +
 +                                                                            +
 +     1      -0.026685   a          0.0000000  N                       N     +
 +     2      -0.026685   a          0.0000000  N                       N     +
 +     5     523.060071   c          0.0000000  N                       Y     +
 +     6     523.060071   c          0.0000000  N                       Y     +
 + .......................................................................... +
 +        Character table from group theory analysis of eigenvectors          +
 +                           Point Group =  32, Oh                            +
 + (Due to LO/TO splitting this character table may not contain some symmetry +
 +  operations of the full crystallographic point group.  Additional          +
 +  representations may be also be present corresponding to split LO modes.   +
 +  A conventional analysis can be generated by specifying an additional null +
 +  (all zero) field direction or one along any unique crystallographic axis  +
 +  in %BLOCK PHONON_GAMMA_DIRECTIONS in <seedname>.cell.)                    +
 + .......................................................................... +
 +  Rep  Mul |    E  2'   2   4  2"   I m_v m_h  -4 m_v                       +
 +           | ----------------------------------------                       +
 + a Eu    1 |    2   0  -2   0   0  -2   0   2   0   0                       +
 + b A2u   1 |    1  -1   1   1  -1  -1   1  -1  -1   1                       +
 + c Tg    1 |    3  -1  -1  -1   1   3  -1  -1  -1   1                       +
 + -------------------------------------------------------------------------- +
 +  q-pt=    2 (  0.500000  0.500000  0.000000)     0.2500000000              +
 + -------------------------------------------------------------------------- +
 +  Acoustic sum rule correction <   0.045784 cm-1 applied                    +
 +     N      Frequency irrep.                                                +
 +                (cm-1)                                                      +
 +                                                                            +
 +     1     151.960430   a                                                   +
 +     2     151.960430   a                                                   +
 +     3     416.931632   b                                                   +
 + .......................................................................... +
 +        Character table from group theory analysis of eigenvectors          +
 +                           Point Group =  32, Oh                            +
 + .......................................................................... +
 +  Rep  Mul |    E   2   2   4   2   I   m   m  -4   m                       +
 +           | ----------------------------------------                       +
 + a       2 |    2   0  -2   0   0   0   0   0   0   0                       +
 + b       1 |    2   0   2   0   0   0   0   0   0   2                       +
 + -------------------------------------------------------------------------- +
 +  q-pt=    3 (  4.000000  5.000000  6.000000)     1.0000000000              +
 + -------------------------------------------------------------------------- +
 +  Acoustic sum rule correction <  47.527118 cm-1 applied                    +
 +     N      Frequency irrep.    ir intensity active  raman activity  active +
 +                (cm-1)         ((D/A)**2/amu)              (A**4/amu)       +
 +                                                                            +
 +     1      -0.049572   a          0.0000000  N            0.0217793  N     +
 +     2      -0.040470   b          0.0000000  N            0.4453475  N     +
 +     3      -0.028618   c          0.0000000  N            1.0298110  Y     +
 + .......................................................................... +
 +        Character table from group theory analysis of eigenvectors          +
 +                           Point Group =   6, C2v                           +
 + .......................................................................... +
 +  Rep  Mul |    E   2   m   m                                               +
 +           | ----------------                                               +
 + a B1    4 |    1  -1  -1   1                                               +
 + b B2    4 |    1  -1   1  -1                                               +
 + c A1    4 |    1   1   1   1                                               +
 ==============================================================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'phonons': [{'N': (1, 2, 5, 6),
                                                  'active': ['N', 'N', 'N', 'N'],
                                                  'char_table':
                                                  [{'chars': (('E', 2),
                                                              ("2'", 0),
                                                              ('2', -2),
                                                              ('4', 0),
                                                              ('2"', 0),
                                                              ('I', -2),
                                                              ('m_v', 0),
                                                              ('m_h', 2),
                                                              ('-4', 0),
                                                              ('m_v', 0)),
                                                    'mul': 1,
                                                    'name': 'Eu',
                                                    'rep': 'a'},
                                                   {'chars': (('E', 1),
                                                              ("2'", -1),
                                                              ('2', 1),
                                                              ('4', 1),
                                                              ('2"', -1),
                                                              ('I', -1),
                                                              ('m_v', 1),
                                                              ('m_h', -1),
                                                              ('-4', -1),
                                                              ('m_v', 1)),
                                                    'mul': 1,
                                                    'name': 'A2u',
                                                    'rep': 'b'},
                                                   {'chars': (('E', 3),
                                                              ("2'", -1),
                                                              ('2', -1),
                                                              ('4', -1),
                                                              ('2"', 1),
                                                              ('I', 3),
                                                              ('m_v', -1),
                                                              ('m_h', -1),
                                                              ('-4', -1),
                                                              ('m_v', 1)),
                                                    'mul': 1,
                                                    'name': 'Tg',
                                                    'rep': 'c'}],
                                                  'frequency': (-0.026685,
                                                                -0.026685,
                                                                523.060071,
                                                                523.060071),
                                                  'intensity': (0.0, 0.0, 0.0, 0.0),
                                                  'irrep': ['a', 'a', 'c', 'c'],
                                                  'qpt': (0.0, 0.0, 0.0),
                                                  'raman_active': ['N', 'N', 'Y', 'Y']},
                                                 {'N': (1, 2, 3),
                                                  'char_table':
                                                  [{'chars': (('E', 2),
                                                              ('2', 0),
                                                              ('2', -2),
                                                              ('4', 0),
                                                              ('2', 0),
                                                              ('I', 0),
                                                              ('m', 0),
                                                              ('m', 0),
                                                              ('-4', 0),
                                                              ('m', 0)),
                                                    'mul': 2,
                                                    'rep': 'a'},
                                                   {'chars': (('E', 2),
                                                              ('2', 0),
                                                              ('2', 2),
                                                              ('4', 0),
                                                              ('2', 0),
                                                              ('I', 0),
                                                              ('m', 0),
                                                              ('m', 0),
                                                              ('-4', 0),
                                                              ('m', 2)),
                                                    'mul': 1,
                                                    'rep': 'b'}],
                                                  'frequency': (151.96043, 151.96043, 416.931632),
                                                  'irrep': ['a', 'a', 'b'],
                                                  'qpt': (0.5, 0.5, 0.0)},
                                                 {'N': (1, 2, 3),
                                                  'active': ['N', 'N', 'N'],
                                                  'char_table':
                                                  [{'chars': (('E', 1),
                                                              ('2', -1),
                                                              ('m', -1),
                                                              ('m', 1)),
                                                    'mul': 4,
                                                    'name': 'B1',
                                                    'rep': 'a'},
                                                   {'chars': (('E', 1),
                                                              ('2', -1),
                                                              ('m', 1),
                                                              ('m', -1)),
                                                    'mul': 4,
                                                    'name': 'B2',
                                                    'rep': 'b'},
                                                   {'chars': (('E', 1),
                                                              ('2', 1),
                                                              ('m', 1),
                                                              ('m', 1)),
                                                    'mul': 4,
                                                    'name': 'A1',
                                                    'rep': 'c'}],
                                                  'frequency': (-0.049572, -0.04047, -0.028618),
                                                  'intensity': (0.0, 0.0, 0.0),
                                                  'irrep': ['a', 'b', 'c'],
                                                  'qpt': (4.0, 5.0, 6.0),
                                                  'raman_active': ['N', 'N', 'Y'],
                                                  'raman_intensity': (0.0217793,
                                                                      0.4453475,
                                                                      1.029811)}]})

    def test_phonon_symmetry_verbose(self):
        test_text = io.StringIO("""
  ************************************************************************
  Phonon Symmetry Analysis: Elements of D with same absolute magnitude
  ************************************************************************
     1     0     2     3     0     4     5     0     6     7     0     8
     0     9     0     0    10     0     0    11     0     0    12     0
     2     0    13    14     0    15     6     0    16    17     0    18
     3     0    14    19     0    20     7     0    17    21     0    22
     0    10     0     0    23     0     0    12     0     0    24     0
     4     0    15    20     0    25     8     0    18    22     0    26
     5     0     6     7     0     8     1     0     2     3     0     4
     0    11     0     0    12     0     0     9     0     0    10     0
     6     0    16    17     0    18     2     0    13    14     0    15
     7     0    17    21     0    22     3     0    14    19     0    20
     0    12     0     0    24     0     0    10     0     0    23     0
     8     0    18    22     0    26     4     0    15    20     0    25

  ************************************************************************
  Phonon Symmetry Analysis: Elements of BEC  with same absolute magnitude
  ************************************************************************
     1     0     0
     0     1     0
     0     0     1

  ************************************************************************
   Phonon Symmetry Analysis:    Phase of Born Effective Charge elements
  ************************************************************************
   0.0   0.0   0.0
   0.0   0.0   0.0
   0.0   0.0   0.0
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict,
                         {'phonon_symmetry_analysis': [{'mat': ((1, 0, 2, 3, 0, 4, 5, 0, 6, 7, 0, 8),
                                                                (0, 9, 0, 0, 10, 0, 0, 11, 0, 0, 12, 0),
                                                                (2, 0, 13, 14, 0, 15, 6, 0, 16, 17, 0, 18),
                                                                (3, 0, 14, 19, 0, 20, 7, 0, 17, 21, 0, 22),
                                                                (0, 10, 0, 0, 23, 0, 0, 12, 0, 0, 24, 0),
                                                                (4, 0, 15, 20, 0, 25, 8, 0, 18, 22, 0, 26),
                                                                (5, 0, 6, 7, 0, 8, 1, 0, 2, 3, 0, 4),
                                                                (0, 11, 0, 0, 12, 0, 0, 9, 0, 0, 10, 0),
                                                                (6, 0, 16, 17, 0, 18, 2, 0, 13, 14, 0, 15),
                                                                (7, 0, 17, 21, 0, 22, 3, 0, 14, 19, 0, 20),
                                                                (0, 12, 0, 0, 24, 0, 0, 10, 0, 0, 23, 0),
                                                                (8, 0, 18, 22, 0, 26, 4, 0, 15, 20, 0, 25)),
                                                        'title': 'Elements of D with same absolute magnitude'},
                                                       {'mat': ((1, 0, 0),
                                                                (0, 1, 0),
                                                                (0, 0, 1)),
                                                        'title': 'Elements of BEC with same absolute magnitude'},
                                                       {'mat': ((0.0, 0.0, 0.0),
                                                                (0.0, 0.0, 0.0),
                                                                (0.0, 0.0, 0.0)),
                                                        'title': 'Phase of Born Effective Charge elements'}]})

    def test_get_thermodynamics(self):
        test_text = io.StringIO("""
 =====================================================================
                             Thermodynamics
                             ==============

            Zero-point energy =         0.125987  eV
 ------------------------------------------------------------------------------
       T(K)        E(eV)           F(eV)         S(J/mol/K)      Cv(J/mol/K)
 ------------------------------------------------------------------------------
       0.0        0.125987        0.125987           0.000           0.000
     100.0        0.131824        0.123323           8.203          14.858
     200.0        0.156189        0.106755          23.849          30.902
 ------------------------------------------------------------------------------

 ==============================================================================

        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'thermodynamics':
                                     {'zero_point_energy': 0.125987,
                                      'cv': (0.0, 14.858, 30.902),
                                      'e': (0.125987, 0.131824, 0.156189),
                                      'f': (0.125987, 0.123323, 0.106755),
                                      's': (0.0, 8.203, 23.849),
                                      't': (0.0, 100.0, 200.0)}})

    def test_get_dynamical_matrix(self):
        test_text = io.StringIO("""
  ------------------------------------------------------------------------------------------------------------------
            Dynamical matrix
 Ion XYZ        real part  ((cm-1)**2)
   1   1          2.000000          0.000000         -0.000000          6.000000         -0.000000          0.000000
   1   2          0.000000          2.000000         -0.000000         -0.000000          6.000000          0.000000
   1   3          0.000000         -0.000000          2.000000         -0.000000          0.000000          6.000000
   2   1          6.000000         -0.000000          0.000000         -4.000000          0.000000         -0.000000
   2   2         -0.000000          6.000000          0.000000          0.000000         -4.000000         -0.000000
   2   3         -0.000000          0.000000          6.000000         -0.000000         -0.000000         -4.000000
 Ion XYZ        imaginary part  ((cm-1)**2)
   1   1         10.000000          0.000000          0.000000          0.000000          3.000000          0.000000
   1   2          0.000000         10.000000          0.000000         -1.000000          0.000000         -1.000000
   1   3          0.000000          0.000000         10.000000          0.000000          3.000000          0.000000
   2   1          7.000000          0.000000          0.000000          2.000000          2.000000          2.000000
   2   2          0.000000          7.000000          0.000000          2.000000          2.000000          2.000000
   2   3          0.000000          0.000000          7.000000          2.000000          2.000000          2.000000
  ------------------------------------------------------------------------------------------------------------------
        """)
        test_dict = parse_castep_file(test_text)[0]
        self.assertEqual(test_dict, {'dynamical_matrix':
                                     ((2+10j, 0j, 0j, 6, 3j, 0j),
                                      (0j, 2+10j, 0j, -1j, 6, -1j),
                                      (0j, 0j, 2+10j, 0j, 3j, 6),
                                      (6+7j, 0j, 0j, -4+2j, 2j, 2j),
                                      (0j, 6+7j, 0j, 2j, -4+2j, 2j),
                                      (0j, 0j, 6+7j, 2j, 2j, -4+2j))})

    def test_get_optical_permittivity(self):
        test_text = io.StringIO("""
 ===============================================================================
        Optical Permittivity (f->infinity)             DC Permittivity (f=0)
        ----------------------------------             ---------------------
         2.63735     0.00000     0.00000         4.65070    -0.00000    -0.00000
         0.00000     2.63735     0.00000        -0.00000     4.65070    -0.00000
         0.00000     0.00000     2.63735        -0.00000    -0.00000     4.65070
 ===============================================================================
            """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'dc_permittivity': ((4.6507, -0.0, -0.0),
                                                         (-0.0, 4.6507, -0.0),
                                                         (-0.0, -0.0, 4.6507)),
                                     'optical_permittivity': ((2.63735, 0.0, 0.0),
                                                              (0.0, 2.63735, 0.0),
                                                              (0.0, 0.0, 2.63735))})

        test_text = io.StringIO("""
 =======================================
      Optical Permittivity (f->infinity)
      ----------------------------------
         8.50261     0.00000     0.00000
         0.00000     8.50261     0.00000
         0.00000     0.00000     8.50261
 =======================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'optical_permittivity': ((8.50261, 0.0, 0.0),
                                                              (0.0, 8.50261, 0.0),
                                                              (0.0, 0.0, 8.50261))})

    def test_get_polarisabilities(self):
        test_text = io.StringIO("""
  ===============================================================================
                                    Polarisabilities (A**3)
                Optical (f->infinity)                       Static  (f=0)
                ---------------------                       -------------
         9.42606     0.00000     0.00000        21.01677    -0.00000    -0.00000
         0.00000     9.42606     0.00000        -0.00000    21.01677    -0.00000
         0.00000     0.00000     9.42606        -0.00000    -0.00000    21.01677
 ===============================================================================
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'optical_polarisability': ((9.42606, 0.0, 0.0),
                                                                (0.0, 9.42606, 0.0),
                                                                (0.0, 0.0, 9.42606)),
                                     'static_polarisability': ((21.01677, -0.0, -0.0),
                                                               (-0.0, 21.01677, -0.0),
                                                               (-0.0, -0.0, 21.01677))})
        test_text = io.StringIO("""
 =======================================
             Polarisability (A**3)
                   Optical (f->infinity)
                   ---------------------
        24.17525     0.00000     0.00000
         0.00000    24.17525     0.00000
         0.00000     0.00000    24.17525
 =======================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'optical_polarisability': ((24.17525, 0.0, 0.0),
                                                                (0.0, 24.17525, 0.0),
                                                                (0.0, 0.0, 24.17525))})

    def test_get_nlo(self):
        test_text = io.StringIO("""
 ===========================================================================
      Nonlinear Optical Susceptibility (pm/V)
      ---------------------------------------
        -1.28186     0.01823     0.01838    23.46304     0.01828     0.01832
         0.01832    -1.28120     0.01830     0.01831    23.46304     0.01823
         0.01828     0.01831    -1.28185     0.01830     0.01838    23.46304
 ===========================================================================
            """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'nlo': ((-1.28186, 0.01823, 0.01838, 23.46304, 0.01828, 0.01832),
                                             (0.01832, -1.2812, 0.0183, 0.01831, 23.46304, 0.01823),
                                             (0.01828, 0.01831, -1.28185, 0.0183, 0.01838, 23.46304))
                                     })

    def test_get_born_charges(self):
        test_text = io.StringIO("""
 ===================================================
                   Born Effective Charges
                   ----------------------
   Si      1        -2.01676     0.00000    -0.00000 ID=geoff
                     0.00000    -3.01676    -0.00000
                     0.00000    -0.00000    -4.01676
   Si      2        -5.01676     0.00000    -0.00000
                     0.00000    -6.01676    -0.00000
                     0.00000    -0.00000    -7.01676
 ===================================================

        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'born': [{('Si [geoff]', 1): ((-2.01676, 0.0, -0.0),
                                                                   (0.0, -3.01676, -0.0),
                                                                   (0.0, -0.0, -4.01676)),
                                               ('Si', 2): ((-5.01676, 0.0, -0.0),
                                                           (0.0, -6.01676, -0.0),
                                                           (0.0, -0.0, -7.01676))}]}
                         )

    def test_get_raman(self):
        test_text = io.StringIO("""
 ==============================================================================
 +                      Raman Susceptibility Tensors ((A/amu)*0.5)            +
 +----------------------------------------------------------------------------+
 + Mode number:   1 Raman tensor       Depolarisation Ratio                   +
 +    -0.0000    0.0000   -0.0000      0.749632                               +
 +     0.0000    0.0000    0.0000                                             +
 +    -0.0000    0.0000    0.0000                                             +
 +                                                                            +
 + Mode number:   2 Raman tensor       Depolarisation Ratio                   +
 +     0.0000   -0.0000   -0.0000      0.750000                               +
 +    -0.0000   -2.5000   -1.3062                                             +
 +    -0.0000   -1.3062   -1.0000                                             +
 +                                                                            +
 +----------------------------------------------------------------------------+
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'raman': [[{'ii': 0.0,
                                                 'depolarisation': 0.749632,
                                                 'tensor': ((-0.0, 0.0, -0.0),
                                                            (0.0, 0.0, 0.0),
                                                            (-0.0, 0.0, 0.0)),
                                                 'trace': 0.0},
                                                {'ii': 0.79384156,
                                                 'depolarisation': 0.75,
                                                 'tensor': ((0.0, -0.0, -0.0),
                                                            (-0.0, -2.5, -1.3062),
                                                            (-0.0, -1.3062, -1.0)),
                                                 'trace': -3.5}]]}
                         )

    def test_get_mol_dipole(self):
        test_text = io.StringIO("""
  =====================================================================
  +                                                                   +
  +   D I P O L E   O F   M O L E C U L E   I N   S U P E R C E L L   +
  +      Cite: S. J. Clark, et al. Europhys Lett 44, 578 (1998)       +
  +                                                                   +
  +      WARNING: This is only correct for isolated molecules         +
  +                                                                   +
  +    Total  ionic  charge in supercell:       8.0000 electrons      +
  +    Total valence charge in supercell:       8.0000 electrons      +
  +                                                                   +
  +   Centre of electronic charge for system:                         +
  +        3.0848      3.0848      3.0848       ANG                   +
  +   Centre of positive ionic charges:                               +
  +        3.0448      3.0448      3.0448       ANG                   +
  +                                                                   +
  +  Magnitude of Dipole =   2.66023  DEBYE                           +
  +  Direction of Dipole =     0.577350    0.577350    0.577350       +
  +                                                                   +
  =====================================================================
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'molecular_dipole': {'centre_electronic': (3.0848, 3.0848, 3.0848),
                                                          'centre_positive': (3.0448, 3.0448, 3.0448),
                                                          'dipole_direction': (0.57735, 0.57735, 0.57735),
                                                          'dipole_magnitude': 2.66023,
                                                          'total_ionic': 8.0,
                                                          'total_valence': 8.0}})

    def test_get_spin_density(self):
        test_text = io.StringIO("""
Integrated Spin Density     =    0.177099E-07 hbar/2
Integrated |Spin Density|   =     3.07611     hbar/2
            """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'spin': [1.77099e-08],
                                     'modspin': [3.07611]})

        test_text = io.StringIO("""
2*Integrated Spin Density (Sx,Sy,Sz) =            -2.30995        2.30855        2.30970     hbar/2
2*Integrated |Spin Density| (|Sx|,|Sy|,|Sz|) =     2.31007        2.30867        2.30982     hbar/2
            """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'spin': [(-2.30995, 2.30855, 2.30970)],
                                     'modspin': [(2.31007, 2.30867, 2.30982)]})

    def test_get_elf(self):
        test_text = io.StringIO("""
      ELF grid sample
-----------------------
 ELF        1 0.506189
 ELF        2 0.506191
 ELF        3 0.506194
-----------------------
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'elf': [0.506189, 0.506191, 0.506194]})

    def test_get_hirshfeld(self):
        test_text = io.StringIO("""
     Hirshfeld Analysis
     ------------------
Species   Ion     Hirshfeld Charge (e)
======================================
  H        1                -1.00
  F        1                17.00
======================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'hirshfeld': {('H', 1): -1.0,
                                                   ('F', 1): 17.0}}
                         )

    def test_geom_output(self):
        test_text = io.StringIO("""
 LBFGS: finished iteration     0 with enthalpy= -2.29374356E+003 eV

 +-----------+-----------------+-----------------+------------+-----+ <-- LBFGS
 | Parameter |      value      |    tolerance    |    units   | OK? | <-- LBFGS
 +-----------+-----------------+-----------------+------------+-----+ <-- LBFGS
 |  dE/ion   |   0.000000E+000 |   2.500000E-005 |         eV | No  | <-- LBFGS
 |  |F|max   |   4.266993E-001 |   5.000000E-002 |       eV/A | No  | <-- LBFGS
 |  |dR|max  |   0.000000E+000 |   1.000000E-003 |          A | No  | <-- LBFGS
 |   Smax    |   1.278436E+001 |   2.500000E-001 |        GPa | No  | <-- LBFGS
 +-----------+-----------------+-----------------+------------+-----+ <-- LBFGS


================================================================================
 Starting LBFGS iteration          1 ...
================================================================================

 +------------+-------------+-------------+-----------------+ <-- min LBFGS
 |    Step    |   lambda    |   F.delta'  |    enthalpy     | <-- min LBFGS
 +------------+-------------+-------------+-----------------+ <-- min LBFGS
 |  previous  |    0.000000 |    0.306114 |    -2293.743561 | <-- min LBFGS
 +------------+-------------+-------------+-----------------+ <-- min LBFGS


--------------------------------------------------------------------------------
 LBFGS: starting iteration         1 with trial guess (lambda=  1.000000)
--------------------------------------------------------------------------------

+---------------- MEMORY AND SCRATCH DISK ESTIMATES PER PROCESS --------------+
|                                                     Memory          Disk    |
| Model and support data                               64.3 MB         0.0 MB |
| Electronic energy minimisation requirements           4.0 MB         0.0 MB |
| Geometry minimisation requirements                    4.6 MB         0.0 MB |
|                                               ----------------------------- |
| Approx. total storage required per process           72.9 MB         0.0 MB |
|                                                                             |
| Requirements will fluctuate during execution and may exceed these estimates |
+-----------------------------------------------------------------------------+


                           -------------------------------
                                      Unit Cell
                           -------------------------------
        Real Lattice(A)              Reciprocal Lattice(1/A)
     4.6386363     0.0000000     0.0000000        1.354532869   0.000000000   0.000000000
     0.0000000     4.6386363     0.0000000        0.000000000   1.354532869   0.000000000
     0.0000000     0.0000000     2.9814282        0.000000000   0.000000000   2.107441421

                       Lattice parameters(A)       Cell Angles
                    a =      4.638636          alpha =   90.000000
                    b =      4.638636          beta  =   90.000000
                    c =      2.981428          gamma =   90.000000

                Current cell volume =            64.151231 A**3
                            density =             2.489923 amu/A**3
                                    =             4.134614 g/cm^3

                           -------------------------------
                                     Cell Contents
                           -------------------------------

            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x  Element         Atom        Fractional coordinates of atoms  x
            x                 Number           u          v          w      x
            x---------------------------------------------------------------x
            x  O                 1         0.299872   0.299872  -0.000000   x
            x  Ti                1         0.000000   0.000000   0.000000   x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


------------------------------------------------------------------------ <-- SCF
SCF loop      Energy                           Energy gain       Timer   <-- SCF
                                               per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -2.29119717E+003                                         26.80  <-- SCF
      1  -2.29452355E+003                    5.54395796E-001      27.00  <-- SCF
      2  -2.29463448E+003                    1.84884599E-002      27.57  <-- SCF
------------------------------------------------------------------------ <-- SCF

Final energy =  -2293.681052478     eV
(energy not corrected for finite basis set)


 ******************************** Symmetrised Forces ********************************
 *                                                                                  *
 *                           Cartesian components (eV/A)                            *
 * -------------------------------------------------------------------------------- *
 *                         x                    y                    z              *
 *                                                                                  *
 * O               1      0.29759              0.29759             -0.00000         *
 * Ti              1      0.00000              0.00000              0.00000         *
 *                                                                                  *
 ************************************************************************************

 *********** Symmetrised Stress Tensor ***********
 *                                               *
 *          Cartesian components (GPa)           *
 * --------------------------------------------- *
 *             x             y             z     *
 *                                               *
 *  x     -1.624594      0.000000      0.000000  *
 *  y      0.000000     -1.624594      0.000000  *
 *  z      0.000000      0.000000     -0.176493  *
 *                                               *
 *  Pressure:    1.1419                          *
 *                                               *
 *************************************************

 +------------+-------------+-------------+-----------------+ <-- min LBFGS
 |    Step    |   lambda    |   F.delta'  |    enthalpy     | <-- min LBFGS
 +------------+-------------+-------------+-----------------+ <-- min LBFGS
 |  previous  |    0.000000 |    0.306114 |    -2293.743561 | <-- min LBFGS
 | trial step |    1.000000 |   -0.064103 |    -2293.757852 | <-- min LBFGS
 +------------+-------------+-------------+-----------------+ <-- min LBFGS

 LBFGS: finished iteration     1 with enthalpy= -2.29375785E+003 eV

 +-----------+-----------------+-----------------+------------+-----+ <-- TPSD
 | Parameter |      value      |    tolerance    |    units   | OK? | <-- TPSD
 +-----------+-----------------+-----------------+------------+-----+ <-- TPSD
 |  dE/ion   |   0.000000E+000 |   2.000000E-005 |         eV | Yes | <-- TPSD
 |  |F|max   |   0.000000E+000 |   5.000000E-002 |       eV/A | Yes | <-- TPSD
 |  |dR|max  |   0.000000E+000 |   1.000000E-003 |          A | Yes | <-- TPSD
 |   Smax    |   0.000000E+000 |   1.000000E-001 |        GPa | Yes | <-- TPSD
 +-----------+-----------------+-----------------+------------+-----+ <-- TPSD

 BFGS: Geometry optimization completed successfully.

================================================================================
 BFGS: Final Configuration:
================================================================================

                           -------------------------------
                                      Unit Cell
                           -------------------------------
        Real Lattice(A)              Reciprocal Lattice(1/A)
     2.3372228     0.0000000     0.0000000        2.688312529   0.000000000   0.000000000
     0.0000000     2.3372228     0.0000000        0.000000000   2.688312529   0.000000000
     0.0000000     0.0000000     2.3372228        0.000000000   0.000000000   2.688312529

                       Lattice parameters(A)       Cell Angles
                    a =      2.337223          alpha =   90.000000
                    b =      2.337223          beta  =   90.000000
                    c =      2.337223          gamma =   90.000000

                Current cell volume =            12.767337 A**3
                            density =             8.748104 amu/A**3
                                    =            14.526569 g/cm^3

                           -------------------------------
                                     Cell Contents
                           -------------------------------

            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x  Element         Atom        Fractional coordinates of atoms  x
            x                 Number           u          v          w      x
            x---------------------------------------------------------------x
            x  Si                1        -0.006190  -0.000628  -0.000628   x
            x  Si                2         0.246190   0.250628   0.250628   x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


 BFGS: Final Enthalpy     = -2.17004345E+002 eV
 BFGS: Final <frequency>  unchanged from initial value
 BFGS: Final bulk modulus =     392.40598 GPa
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'geom_opt':
                                     {'final_configuration':
                                      {'atoms': {('Si', 1): (-0.00619, -0.000628, -0.000628),
                                                 ('Si', 2): (0.24619, 0.250628, 0.250628)},
                                       'cell': {'cell_angles': [90.0, 90.0, 90.0],
                                                'density_amu': 8.748104,
                                                'density_g': 14.526569,
                                                'lattice_parameters': [2.337223, 2.337223, 2.337223],
                                                'real_lattice': [(2.3372228, 0.0, 0.0),
                                                                 (0.0, 2.3372228, 0.0),
                                                                 (0.0, 0.0, 2.3372228)],
                                                'recip_lattice': [(2.688312529, 0.0, 0.0),
                                                                  (0.0, 2.688312529, 0.0),
                                                                  (0.0, 0.0, 2.688312529)],
                                                'volume': 12.767337},
                                       'final_bulk_modulus': 392.40598,
                                       'final_enthalpy': -217.004345},
                                      'iterations':
                                      [{'enthalpy': [-2293.74356],
                                        'minimisation': [{'smax': {'converged': False,
                                                                   'tolerance': 0.25,
                                                                   'value': 12.78436},
                                                          'de_ion': {'converged': False,
                                                                     'tolerance': 2.5e-05,
                                                                     'value': 0.0},
                                                          'f_max': {'converged': False,
                                                                    'tolerance': 0.05,
                                                                    'value': 0.4266993},
                                                          'dr_max': {'converged': False,
                                                                     'tolerance': 0.001,
                                                                     'value': 0.0}}]},
                                       {'cell': {'cell_angles': [90.0, 90.0, 90.0],
                                                 'density_amu': 2.489923,
                                                 'density_g': 4.134614,
                                                 'lattice_parameters': [4.638636, 4.638636, 2.981428],
                                                 'real_lattice': [(4.6386363, 0.0, 0.0),
                                                                  (0.0, 4.6386363, 0.0),
                                                                  (0.0, 0.0, 2.9814282)],
                                                 'recip_lattice': [(1.354532869, 0.0, 0.0),
                                                                   (0.0, 1.354532869, 0.0),
                                                                   (0.0, 0.0, 2.107441421)],
                                                 'volume': 64.151231},
                                        'energies': {'final_energy': [-2293.681052478]},
                                        'enthalpy': [-2293.75785],
                                        'forces': {'symmetrised': [{('O', 1): (0.29759, 0.29759, -0.0),
                                                                    ('Ti', 1): (0.0, 0.0, 0.0)}]},
                                        'geom_opt': {'trial': [1.0]},
                                        'memory_estimate':
                                        [{'electronic_energy_minimisation_requirements': {'disk': 0.0, 'memory': 4.0},
                                          'geometry_minimisation_requirements': {'disk': 0.0, 'memory': 4.6},
                                          'model_and_support_data': {'disk': 0.0, 'memory': 64.3}}],
                                        'minimisation': [{'previous': {'fdelta': 0.306114,
                                                                       'enthalpy': -2293.743561,
                                                                       'lambda': 0.0}},
                                                         {'previous': {'fdelta': 0.306114,
                                                                       'enthalpy': -2293.743561,
                                                                       'lambda': 0.0},
                                                          'trial step': {'fdelta': -0.064103,
                                                                         'enthalpy': -2293.757852,
                                                                         'lambda': 1.0}},
                                                         {'smax': {'converged': True,
                                                                   'tolerance': 0.1,
                                                                   'value': 0.0},
                                                          'de_ion': {'converged': True,
                                                                     'tolerance': 2e-05,
                                                                     'value': 0.0},
                                                          'f_max': {'converged': True,
                                                                    'tolerance': 0.05,
                                                                    'value': 0.0},
                                                          'dr_max': {'converged': True,
                                                                     'tolerance': 0.001,
                                                                     'value': 0.0}}],
                                        'positions': {('O', 1): (0.299872, 0.299872, -0.0),
                                                      ('Ti', 1): (0.0, 0.0, 0.0)},
                                        'stresses': {'symmetrised': [(-1.624594, 0.0, 0.0,
                                                                      -1.624594, 0.0, -0.176493)]
                                                     }}]}}
                         )

    def test_get_deloc_info(self):
        test_text = io.StringIO("""
  INTERNAL CONSTRAINTS
 #  Type     Target    Actual           Definition

  1 Bond       2.360 Satisfied   4 ( 0 0 0)  5 ( 0 0-1)
  2 Angle     109.47 Satisfied   2 ( 1 0 0)  5 ( 0 0 0)  3 ( 0 0 0)


Message: Generating delocalized internals
 constraint #     1 is a primitive #    15
 constraint #     2 is a primitive #    43

Total number of primitive bonds:             16
Total number of primitive angles:            48
Total number of primitive dihedrals:        144

Total number of primitive internals:        208

Message: Generation of delocalized internals is successful
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_deloc_step(self):
        test_text = io.StringIO("""

 Startup Hessian in Internal Coordinates

 The size of active space is :    19
 There are :     24  degrees of freedom
 There are :     67  primitive internals


  INTERNAL CONSTRAINTS
 #  Type     Target    Actual           Definition

  1 Bond       2.360 Satisfied   4 ( 0 0 0)  5 ( 0 0-1)
  2 Angle     109.47 Satisfied   3 ( 0 0 0)  5 ( 0 0 0)  2 ( 1 0 0)

        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_tss_structure(self):
        test_text = io.StringIO("""

            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x                          Reactant                        x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x  Element    Atom        Fractional coordinates of atoms  x
            x            Number           u          v          w      x
            x----------------------------------------------------------x
            x  H            1         0.000000   0.000000   0.000000   x
            x  H            2        -0.000000  -0.000000   0.195000   x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x                          Product                         x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x  Element    Atom        Fractional coordinates of atoms  x
            x            Number           u          v          w      x
            x----------------------------------------------------------x
            x  H            1         0.000000   0.000000   0.000000   x
            x  H            2        -0.000000  -0.000000   0.805000   x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'product': {('H', 1): (0.0, 0.0, 0.0),
                                                 ('H', 2): (-0.0, -0.0, 0.805)},
                                     'reactant': {('H', 1): (0.0, 0.0, 0.0),
                                                  ('H', 2): (-0.0, -0.0, 0.195)}})

    def test_get_tss_info(self):
        test_text = io.StringIO("""
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Difference vector: Fractional components
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++
    0.000000000    0.000000000    0.000000000
   -0.000000000   -0.000000000    0.610000000
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++

 +++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Reactant
 Path coordinate:                         0.00000
 Energy:                                -32.02905 eV
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++

 +++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Local change at QST maximum:            0.00030
 RMS gradient at QST maximum:            0.17078 eV/A
 Cumulative number of energy/gradient calls:     12
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++

 +++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Transition State Found!
 Energy of reactant:                    -32.02905 eV
 Energy of product:                     -32.02904 eV
 Energy of transition state:            -29.51038 eV
 Location of transition state:            0.50000
 Barrier from reactant:                   2.51867 eV
 Barrier from product:                    2.51867 eV
 Energy of reaction:                      0.00000 eV
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++

            ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                             Coordinates: Fractional components
            ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            +  Element    Atom                                                 +
            +            Number           x          y          z              +
            ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            +H             1          0.000000   0.000000   0.000000           +
            +H             2         -0.000000  -0.000000   0.500000           +
            ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                           Forces: Cartesian components: eV/A
            ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            +  Element    Atom                                                 +
            +            Number           x          y          z              +
            ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            +H             1         -0.000000  -0.000000  -0.000208           +
            +H             2          0.000000   0.000000   0.000208           +
            ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_bs_info(self):
        test_text = io.StringIO("""
  + ================================================================= +
  +                                                                   +
  +     Band Structure Calculation: Progress report on root process   +
  +                                                                   +
  +   There are   10 BS k-points. Root process contains   10 of them. +
  +                                                                   +
  +   Spin= 1 of  1, K-point=   1 of   10 completed, Time:     0.11s. +
  +   Spin= 1 of  1, K-point=   2 of   10 completed, Time:     0.12s. +
  +   Finished BS calculation on root process (waiting for others).   +
  +                                                                   +
  + ================================================================= +
  +                       Electronic energies                         +
  +                       -------------------                         +
  +                                                                   +
  +   Band number   Energy in eV                                      +
  + ================================================================= +
  +                                                                   +
  + ----------------------------------------------------------------- +
  +  Spin=1 kpt=    1 ( -0.375000 -0.375000 -0.125000) kpt-group=  1  +
  + ----------------------------------------------------------------- +
  +                                                                   +
  +           1       -3.923890                                       +
  +           2        1.381011                                       +
  +           3        3.604213                                       +
  + ----------------------------------------------------------------- +
  +  Spin=1 kpt=   10 (  0.375000  0.375000  0.375000) kpt-group=  1  +
  + ----------------------------------------------------------------- +
  +                                                                   +
  +           1       -4.014813                                       +
  +           2        0.312829                                       +
  +           3        5.232953                                       +
  =====================================================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'bs':
                                     [{'band': (1, 2, 3),
                                       'energy': (-3.92389, 1.381011, 3.604213),
                                       'kpgrp': 1,
                                       'kx': -0.375,
                                       'ky': -0.375,
                                       'kz': -0.125,
                                       'spin': 1},
                                      {'band': (1, 2, 3),
                                       'energy': (-4.014813, 0.312829, 5.232953),
                                       'kpgrp': 1,
                                       'kx': 0.375,
                                       'ky': 0.375,
                                       'kz': 0.375,
                                       'spin': 1}]})

    def test_get_chem_shielding(self):
        test_text = io.StringIO("""
  ====================================================================
  |                      Chemical Shielding Tensor                   |
  |------------------------------------------------------------------|
  |     Nucleus                            Shielding tensor          |
  |  Species            Ion            Iso(ppm)   Aniso(ppm)  Asym   |
  |    C                1              162.01     175.31      0.00   |
  |    C                2              162.00     175.31      N/A    |
  |    C:tag            2              162.00     175.31      1.00   |
  ====================================================================
            """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'magres':
                                     [{'task': 'Chemical Shielding',
                                      ('C', 1): {'aniso': 175.31,
                                                 'asym': 0.0,
                                                 'iso': 162.01},
                                      ('C', 2): {'aniso': 175.31,
                                                 'asym': None,
                                                 'iso': 162.0},
                                      ('C:tag', 2): {'aniso': 175.31,
                                                     'asym': 1.0,
                                                     'iso': 162.0}
                                       }
                                      ]}
                         )

    def test_get_j_coupling(self):
        test_text = io.StringIO("""
  ==================================================================================
  |                            Isotropic J-coupling                                |
  |--------------------------------------------------------------------------------|
  |     Nucleus                               J-coupling values                    |
  |  Species          Ion     FC           SD         PARA       DIA       TOT(Hz) |
  |** C                 1     --.--       --.--       --.--      --.--       --.-- |
  |   C                 2    128.25        3.20       -1.22      -0.48      129.75 |
  |                                                                                |
  |** Signifies Perturbing Nucleus A of coupling J_AB                              |
  ==================================================================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'magres':
                                     [{'task': '(An)Isotropic J-coupling',
                                       ('C', 2): {'dia': -0.48,
                                                  'fc': 128.25,
                                                  'para': -1.22,
                                                  'sd': 3.2,
                                                  'tot': 129.75}
                                       }
                                      ]}
                         )

    def test_get_chem_shielding_efg(self):
        test_text = io.StringIO("""
  ===============================================================================
  |                Chemical Shielding and Electric Field Gradient Tensors       |
  |-----------------------------------------------------------------------------|
  |     Nucleus                       Shielding tensor             EFG Tensor   |
  |    Species            Ion    Iso(ppm)   Aniso(ppm)  Asym    Cq(MHz)    Eta  |
  |    H                  1       28.24       8.55      0.11   1.968E-01   0.02 |
  |    H                  2       28.75       9.29      0.22   1.932E-01   0.03 |
  |    H:T                3       28.71       7.26      N/A    1.996E-01   0.01 |
  ===============================================================================
        """)
        test_dict = parse_castep_file(test_text)[0]
        self.assertEqual(test_dict, {'magres':
                                     [{'task': 'Chemical Shielding and Electric '
                                       'Field Gradient',
                                       ('H', 1): {'aniso': 8.55,
                                                  'asym': 0.11,
                                                  'cq': 0.1968,
                                                  'eta': 0.02,
                                                  'iso': 28.24},
                                       ('H', 2): {'aniso': 9.29,
                                                  'asym': 0.22,
                                                  'cq': 0.1932,
                                                  'eta': 0.03,
                                                  'iso': 28.75},
                                       ('H:T', 3): {'aniso': 7.26,
                                                    'asym': None,
                                                    'cq': 0.1996,
                                                    'eta': 0.01,
                                                    'iso': 28.71}}
                                      ]}
                         )

    def test_get_efg(self):
        test_text = io.StringIO("""
  ===============================================================
  |                Electric Field Gradient Tensor               |
  |-------------------------------------------------------------|
  |     Nucleus                              EFG tensor         |
  |    Species            Ion             Cq(MHz)        Asym   |
  |    H                  1             1.968E-01        0.02   |
  |    H                  2             1.932E-01        0.03   |
  |    H:T                3             1.996E-01        N/A    |
  ===============================================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'magres':
                                     [{'task': 'Electric Field Gradient',
                                       ('H', 1): {'asym': 0.02, 'cq': 0.1968},
                                       ('H', 2): {'asym': 0.03, 'cq': 0.1932},
                                       ('H:T', 3): {'asym': None, 'cq': 0.1996}}
                                      ]
                                     }
                         )

    def test_get_hft(self):
        test_text = io.StringIO("""
  ==============================================================
  |                        Hyperfine Tensor                    |
  |------------------------------------------------------------|
  |     Nucleus                         Hyperfine tensor       |
  |    Species          Ion                 Iso(MHz)           |
  |    H                  1                  -1.227E+03        |
  ==============================================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'magres':
                                     [{'task': 'Hyperfine',
                                       ('H', 1): {'iso': -1227.0}}
                                      ]
                                     }
                         )

    def test_get_solvation(self):
        test_text = io.StringIO("""
 ********************** AUTOSOLVATION CALCULATION RESULTS **********************
 Calculation succeeded:
  - Vacuum calculation converged to a ground state
  - Solvent calculation converged to a ground state

 Total energy in solvent          =       -30.70199010998910794 eV
 -Total energy in vacuum          =       -30.72034046140072405 eV
 ----------------------------------
 Free energy of solvation         =         0.01835035141161526 eV

  (Apolar cavitation energy       =         0.23174076832973722 eV)
  (Apolar dis-rep energy          =        -0.16660423187145634 eV)
  (Total apolar solvation energy  =         0.06513653645828089 eV)
  (Total polar solvation energy   =        -0.04678618504666563 eV)
 *******************************************************************************
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'autosolvation': {'apolar_cavitation_energy': 0.23174076832973722,
                                                       'apolar_dis_rep_energy': -0.16660423187145634,
                                                       'free_energy_of_solvation': 0.01835035141161526,
                                                       'total_apolar_solvation_energy': 0.0651365364582809,
                                                       'total_energy_in_solvent': -30.701990109989108,
                                                       'total_energy_in_vacuum': -30.720340461400724,
                                                       'total_polar_solvation_energy': -0.04678618504666563}})

    def test_get_tddft(self):
        test_text = io.StringIO("""
  + ================================================================= +TDDFT
  +                     TDDFT excitation energies                     +TDDFT
  +                     -------------------------                     +TDDFT
  +   State number         Energy in   eV     Estimated error         +TDDFT
  + ================================================================= +TDDFT
  +                                                                   +TDDFT
  +         1     5.753504005347331   3.6998800019E-07     spurious   +TDDFT
  +         2     6.402101261254828   5.3503385576E-07     Singlet    +TDDFT
  +         3     6.402955563292028   5.7075034009E-07     Singlet    +TDDFT
  +                                                                   +TDDFT
  + ================================================================= +TDDFT
  +  TDDFT calculation time:      39.35                               +TDDFT
  + ================================================================= +TDDFT
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'tddft':
                                     [
                                         {'energy': 5.753504005347331,
                                          'error': 3.6998800019e-07,
                                          'type': 'spurious'},
                                         {'energy': 6.402101261254828,
                                          'error': 5.3503385576e-07,
                                          'type': 'Singlet'},
                                         {'energy': 6.402955563292028,
                                          'error': 5.7075034009e-07,
                                          'type': 'Singlet'}
                                     ]}
                         )

    def test_elastic_scf(self):
        test_text = io.StringIO("""
  Generating 0'th order wvfns with non self-consistent calculation :       2.61
  Band structure converged at all 2 kpoints
  Finished generating 0'th order wavefunctions for perturbation    :       2.62

 Strain perturbation    1:  xx                                            2.62s
  8 symmetry operations and 3 k-points for this perturbation
  Parallel strategy changed for perturbation using 3 k-points
  Data is distributed by G-vector(2-way) and k-point(1-way) and band(1-way)
  Generating 0'th order wvfns with non self-consistent calculation :       2.83
  Band structure converged at all 2 kpoints
  Finished generating 0'th order wavefunctions for perturbation    :       2.84
 ---------------------------------------------------------------------- <-- ESCF
 Iter #steps     E_2           efermi_1         E_2 change      Time(s) <-- ESCF
 ---------------------------------------------------------------------- <-- ESCF
    1  19.3      -4.037524655   -0.000000      -4.037524655       2.94  <-- ESCF
    2  16.3      -4.119781099   -0.000000      -0.082256444       3.00  <-- ESCF
 ---------------------------------------------------------------------- <-- ESCF
  1st-order wvfn converged in   9 SCF cycles. Time:               0.47  <-- ELST
<psi^mu|   H^(strain)    |psi^0> ::
   -0.0154669691   -0.0025155337   -0.0017278086    0.0006712021   -0.0003521132    0.0007355814
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_elastic_contributions(self):
        test_text = io.StringIO("""
Ewald Contribution ::
      -0.01327650       0.00132942       0.00132942       0.00000000      -0.00000000       0.00000000
       0.00132942      -0.01327650       0.00132942      -0.00000000      -0.00000000      -0.00000000
       0.00132942       0.00132942      -0.01327650      -0.00000000      -0.00000000       0.00000000
       0.00000000      -0.00000000      -0.00000000       0.01194708       0.00000000      -0.00000000
      -0.00000000      -0.00000000      -0.00000000       0.00000000       0.01194708       0.00000000
       0.00000000      -0.00000000       0.00000000      -0.00000000       0.00000000       0.01194708

<psi^1|H^(1)|psi^0> Contribution ::
      -0.01546697      -0.00212167      -0.00212167       0.00000000       0.00000000       0.00000000
      -0.00212167      -0.01546697      -0.00212167       0.00000000       0.00000000       0.00000000
      -0.00212167      -0.00212167      -0.01546697       0.00000000       0.00000000       0.00000000
       0.00000000       0.00000000       0.00000000      -0.01407441       0.00000000       0.00000000
       0.00000000       0.00000000       0.00000000       0.00000000      -0.01407441       0.00000000
       0.00000000       0.00000000       0.00000000       0.00000000       0.00000000      -0.01407441
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'elastic': {
            '<psi^1|H^(1)|psi^0> Contribution': ((-0.01546697, -0.00212167, -0.00212167, 0.0, 0.0, 0.0),
                                                 (-0.00212167, -0.01546697, -0.00212167, 0.0, 0.0, 0.0),
                                                 (-0.00212167, -0.00212167, -0.01546697, 0.0, 0.0, 0.0),
                                                 (0.0, 0.0, 0.0, -0.01407441, 0.0, 0.0),
                                                 (0.0, 0.0, 0.0, 0.0, -0.01407441, 0.0),
                                                 (0.0, 0.0, 0.0, 0.0, 0.0, -0.01407441)),
            'Ewald Contribution': ((-0.0132765, 0.00132942, 0.00132942, 0.0, -0.0, 0.0),
                                   (0.00132942, -0.0132765, 0.00132942, -0.0, -0.0, -0.0),
                                   (0.00132942, 0.00132942, -0.0132765, -0.0, -0.0, 0.0),
                                   (0.0, -0.0, -0.0, 0.01194708, 0.0, -0.0),
                                   (-0.0, -0.0, -0.0, 0.0, 0.01194708, 0.0),
                                   (0.0, -0.0, 0.0, -0.0, 0.0, 0.01194708))}})

    def test_get_atomic_displacements(self):
        test_text = io.StringIO("""
 ==============================================================================
                      Atomic Displacement Parameters (A**2)
                      ==============================

 ------------------------------------------------------------------------------
      T(K)  Ion        U11       U22       U33       U23       U31       U12
 ------------------------------------------------------------------------------
       0.0  Si 1     0.002399  0.002399  0.002399  0.000000  0.000000 -0.000000
       0.0  Si 2     0.003009  0.003009  0.003009  0.000000 -0.000000  0.000000
     100.0  Si 2     0.003009  0.003009  0.003009  0.000000 -0.000000  0.000000
 ------------------------------------------------------------------------------

        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'atomic_displacements':
                                     {'0.0': {('Si', 1): (0.002399, 0.002399, 0.002399, 0.0, 0.0, -0.0),
                                              ('Si', 2): (0.003009, 0.003009, 0.003009, 0.0, -0.0, 0.0)},
                                      '100.0': {('Si', 2): (0.003009, 0.003009, 0.003009, 0.0, -0.0, 0.0)}}}
                         )

    def test_elastic_constants_tensor(self):
        test_text = io.StringIO("""
 ===============================================================================
                          Elastic Constants Tensor (GPa)
 -------------------------------------------------------------------------------
    167.397133    58.771201    58.771201     0.000000     0.000000    -0.000000
     58.771201   167.397133    58.771201     0.000000     0.000000    -0.000000
     58.771201    58.771201   167.397133     0.000000    -0.000000    -0.000000
      0.000000     0.000000     0.000000   102.034195    -0.000000     0.000000
      0.000000     0.000000    -0.000000    -0.000000   102.034195     0.000000
     -0.000000    -0.000000    -0.000000     0.000000     0.000000   102.034195
 ===============================================================================
        """)
        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'elastic':
                                     {'elastic_constants': ((167.397133, 58.771201, 58.771201, 0.0, 0.0, -0.0),
                                                            (58.771201, 167.397133, 58.771201, 0.0, 0.0, -0.0),
                                                            (58.771201, 58.771201, 167.397133, 0.0, -0.0, -0.0),
                                                            (0.0, 0.0, 0.0, 102.034195, -0.0, 0.0),
                                                            (0.0, 0.0, -0.0, -0.0, 102.034195, 0.0),
                                                            (-0.0, -0.0, -0.0, 0.0, 0.0, 102.034195))
                                      }})

    def test_elastic_compliance_matrix(self):
        test_text = io.StringIO("""
 ===============================================================================
                           Compliance Matrix (GPa^-1)
 -------------------------------------------------------------------------------
   0.007307109 -0.001898796 -0.001898796  0.000000000 -0.000000000  0.000000000
  -0.001898796  0.007307109 -0.001898796 -0.000000000  0.000000000  0.000000000
  -0.001898796 -0.001898796  0.007307109 -0.000000000  0.000000000 -0.000000000
   0.000000000 -0.000000000 -0.000000000  0.009800636  0.000000000 -0.000000000
  -0.000000000  0.000000000  0.000000000  0.000000000  0.009800636 -0.000000000
   0.000000000  0.000000000 -0.000000000 -0.000000000 -0.000000000  0.009800636
 ===============================================================================
        """)
        test_dict = parse_castep_file(test_text)[0]
        self.assertEqual(test_dict, {'elastic':
                                     {'compliance_matrix': ((0.007307109, -0.001898796, -0.001898796, 0.0, -0.0, 0.0),
                                                            (-0.001898796, 0.007307109, -0.001898796, -0.0, 0.0, 0.0),
                                                            (-0.001898796, -0.001898796, 0.007307109, -0.0, 0.0, -0.0),
                                                            (0.0, -0.0, -0.0, 0.009800636, 0.0, -0.0),
                                                            (-0.0, 0.0, 0.0, 0.0, 0.009800636, -0.0),
                                                            (0.0, 0.0, -0.0, -0.0, -0.0, 0.009800636))
                                      }})

    def test_elastic_properties(self):
        test_text = io.StringIO("""
 ===============================================================================
                               Elastic Properties
 -------------------------------------------------------------------------------
                            x              y              z
 -------------------------------------------------------------------------------
  Young's Modulus ::     136.853034     136.853034     136.853034     (GPa)

 -------------------------------------------------------------------------------
                        xy        xz        yx        yz        zx        zy
 -------------------------------------------------------------------------------
  Poisson Ratios  :: 0.259856  0.259856  0.259856  0.259856  0.259856  0.259856

 -------------------------------------------------------------------------------
                          Voigt          Reuss          Hill
 -------------------------------------------------------------------------------
   Bulk Modulus   ::      94.979845      94.979845      94.979845     (GPa)
  Shear Modulus   ::      82.945704      75.499588      79.222646     (GPa)

 -------------------------------------------------------------------------------
                                 Speed of Sound
 -------------------------------------------------------------------------------
                            x              y              z
 -------------------------------------------------------------------------------
                  x       83.994377      49.768951      49.768951     (A/ps)
  (Anisotropic)   y       49.768951      83.994377      49.768951     (A/ps)
                  z       49.768951      49.768951      83.994377     (A/ps)

 Assuming Isotropic material
  Longitudinal waves ::     91.950170   (A/ps)
   Transverse waves  ::     57.783105   (A/ps)
 ===============================================================================
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'elastic':
                                     {'bulk_modulus': (94.979845, 94.979845, 94.979845),
                                      'longitudinal_waves': 91.95017,
                                      'poisson_ratios': (0.259856, 0.259856, 0.259856, 0.259856, 0.259856, 0.259856),
                                      'shear_modulus': (82.945704, 75.499588, 79.222646),
                                      'speed_of_sound': ((83.994377, 49.768951, 49.768951),
                                                         (49.768951, 83.994377, 49.768951),
                                                         (49.768951, 49.768951, 83.994377)),
                                      'transverse_waves': 57.783105,
                                      "young_s_modulus": (136.853034, 136.853034, 136.853034)}})

    def test_get_continuation(self):
        test_text = io.StringIO("""
Reading continuation data from model file BN.check
        """)

        test_dict = parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'continuation': 'BN.check'})


class test_pspot_parser(TestCase):
    def test_pspot_parser(self):
        test_text = io.StringIO("""
1|0.8|11|15|18|10N(qc=8)[]
1|1.2|23|29|33|20N:21L(qc=9)[]
2|1.4|1.4|1.3|6|10|12|20:21(qc=6)
1|0.8|0.8|0.6|2|6|8|10(qc=6)
2|1.0|1.3|0.7|13|16|18|20:21(qc=7)
2|1.8|3.675|5.512|7.35|30UU:31UU:32LGG[]
2|1.8|3.675|5.512|7.35|30UU:31UU:32LGG
2|1.9|2.1|1.3|3.675|5.512|7.35|30N1.9:31N2.1:32N2.1(tm,nonlcc)[]
2|1.75|1.75|1.3|6.4|8.1|11|30N:31N:32L(qc=6.5)[3s2,3p1.5,3d0.25]
2|1.8|1.8|1.3|2|3|4|30:31:32LGG(qc=4)
2|1.8|3.675|5.512|7.35|30UU:31UU:32LGG[]
2|1.8|3.675|5.512|7.35|30UU:31UU:32LGG{1s1}[]
        """)
        self.skipTest("Correct answers not provided")
        for line in test_text:
            if not line.strip():
                continue
            print(f"{line=}")
            test_dict = _process_pspot_string(line)

            pprint.pprint(test_dict)
            # self.assertEqual(test_dict, {})


if __name__ == '__main__':
    main()
