import pprint
import io
from unittest import (TestCase, main)
from castep_outputs import parse_castep_file


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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'build_info':
                                     {'summary': ('Compiled for GNU 12.2.1 on 14-04-2023 15:14:41 '
                                                  'from code version 2c6c6d262 update-jenkins '
                                                  'Fri Apr 14 15:13:22 2023 +0100'),
                                      'Compiler': 'GNU Fortran 12.2.1; Optimisation: FAST',
                                      'Comms': 'Open MPI v4.1.4',
                                      'MATHLIBS': 'blas (LAPACK version 3.11.0)',
                                      'FFT Lib': 'fftw3 version fftw-3.3.10-sse2-avx',
                                      'Fundamental constants values': 'CODATA 2018'}})

    def test_get_final_printout(self):
        test_text = io.StringIO("""
Initialisation time =      1.07 s
Calculation time    =    135.01 s
Finalisation time   =      0.03 s
Total time          =    136.11 s
Peak Memory Use     = 149108 kB

Overall parallel efficiency rating: Satisfactory (64%)
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

    def test_get_title(self):
        test_text = io.StringIO("""
************************************ Title ************************************
 CASTEP calculation for SSEC2016

        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

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

  **********************************************************
  *** There were at least     1 warnings during this run ***
  *** => please check the whole of this file carefully!  ***
  **********************************************************

        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

    def test_get_supercell(self):
        test_text = io.StringIO("""
    Supercell generated using matrix  [1,1,-1; 1,-1,1; -1,1,1]
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

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
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

    def test_get_atom_velocities(self):
        test_text = io.StringIO("""
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x  Element    Atom        User Supplied Ionic Velocities   x
            x            Number          Vx         Vy         Vz      x
            x----------------------------------------------------------x
            x  Si           1         3.601230   0.986420   2.774470   x
            x  Si           2         1.855230   3.245360   6.707270   x
            x  Si           3         5.867920   2.404810   1.768580   x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

    def test_get_atom_spin_params(self):
        test_text = io.StringIO("""
         xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
         |  Element    Atom         Initial            Initial magnetic       |
         |            Number    spin polarization        moment (uB)     Fix? |
         |--------------------------------------------------------------------|
         | Cr             1         0.500000              3.000       F       |
         | Cr             2        -0.500000             -3.000       F       |
         xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_pspot(self):
        test_text = io.StringIO("""
        Run started:
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
   |          3s1/2            2.000           -3.132         |
   |          3p1/2            2.000           -2.001         |
   |          3p1/2            2.000           -2.001         |
   |          3d3/2            2.000           -0.258         |
   |          3d3/2            2.000           -0.258         |
   |          4s1/2            2.000           -0.194         |
   |                                                          |
   |                 Pseudopotential Definition               |
   |      Beta    l   2j     e      Rc     scheme   norm      |
   |        1     0    1   -3.132   1.803     qc     0        |
   |        2     0    1   -0.194   1.803     qc     0        |
   |        3     0    1    0.250   1.803     qc     0        |
   |        4     1    3   -2.001   1.803     qc     0        |
   |        5     1    1   -2.001   1.803     qc     0        |
   |        6     1    3    0.250   1.803     qc     0        |
   |        7     1    1    0.250   1.803     qc     0        |
   |        8     2    5   -0.258   1.803     qc     0        |
   |        9     2    3   -0.258   1.803     qc     0        |
   |       10     2    5    0.250   1.803     qc     0        |
   |       11     2    3    0.250   1.803     qc     0        |
   |       loc    3    0    0.000   1.803     pn     0        |
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

        """)
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        del test_dict["time_started"]

        self.assertEqual(test_dict, {'species_properties':
                                     {'Mn': {'pseudo_atomic_energy': -2901.7207}}
                                     })

    def test_get_species_prop(self):
        test_text = io.StringIO("""
        Run started: 1984
                           -------------------------------
                                   Details of Species
                           -------------------------------

                                  Files used for pseudopotentials:
                                    Mn 3|1.8|1.8|0.6|12|14|16|30U:40:31:32(qc=7)
                                    O  my_pot.usp

                               Mass of species in AMU
                                    Mn   54.9380500
                                    O    15.9993815

                          Electric Quadrupole Moment (Barn)
                                    Mn    0.3300000 Isotope 55
                                    O     1.0000000 No Isotope Defined
        """)
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        del test_dict['time_started']

        self.assertEqual(test_dict, {'species_properties': {'Mn': {'mass': 54.93805,
                                                                   'elec_quad': 0.33,
                                                                   'pseudopot': '3|1.8|1.8|0.6|12|14|16|30U:40:31:32(qc=7)'},
                                                            'O': {'mass': 15.9993815,
                                                                  'elec_quad': 1.0,
                                                                  'pseudopot': 'my_pot.usp'}
                                                            }
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

 *******************************************************************************
        """)
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'options':
                                     {'general': {'output verbosity': 'normal (1)',
                                                  'write checkpoint data to': 'beta-mn.check',
                                                  'output length unit': 'A'
                                                  },
                                      'density mixing': {'density-mixing scheme': 'Broyden',
                                                         'max. length of mixing history': '20'}
                                      }
                                     })

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
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
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

             +++++++++++++++++++++++++++++++++++++++++++++++++++++++
             +  Number       Fractional coordinates        Weight  +
             +-----------------------------------------------------+
             +     1   0.000000   0.000000   0.000000   1.0000000  +
             +++++++++++++++++++++++++++++++++++++++++++++++++++++++

        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

    def test_get_symmetry(self):
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

        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

    def test_get_constraints(self):
        test_text = io.StringIO("""
             Set iprint > 1 for details on symmetry rotations/translations

                         Centre of mass is constrained
             Set iprint > 1 for details of linear ionic constraints

                         Number of cell constraints= 0
                         Cell constraints are:  1 2 3 4 5 6


                         Centre of mass is constrained

            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx....
            x  Species       atom   co-ordinate  constraints.....
            x-------------------------------------------------------------....
            x Br                1       x       145656.0817      0.0000      0.0000
            x Br                1       y            0.0000 145656.0817      0.0000
            x Br                1       z            0.0000      0.0000 145656.0817
            x Rb                1       x       155798.2686      0.0000      0.0000
            x Rb                1       y            0.0000 155798.2686      0.0000
            x Rb                1       z            0.0000      0.0000 155798.2686
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx....

                         Number of cell constraints= 5
                         Cell constraints are:  1 1 1 0 0 0

        """)

        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

    def test_get_target_stress(self):
        test_text = io.StringIO("""
                         External pressure/stress (GPa)
                          0.00000   0.00000   0.00000
                                    0.00000   0.00000
                                              0.00000
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

    def test_get_scf(self):
        test_text = io.StringIO("""
------------------------------------------------------------------------ <-- SCF
SCF loop      Energy           Fermi           Energy gain       Timer   <-- SCF
                               energy          per atom          (sec)   <-- SCF
------------------------------------------------------------------------ <-- SCF
Initial  -8.43823694E+002  0.00000000E+000                         2.77  <-- SCF
      1  -8.55962165E+002  6.11993396E+000   1.51730885E+000       3.54  <-- SCF
      2  -8.55990255E+002  6.11946292E+000   3.51127330E-003       4.50  <-- SCF
      3  -8.55296355E+002  6.32342274E+000  -8.67376091E-002       5.43  <-- SCF
      4  -8.55251213E+002  6.40840823E+000  -5.64263304E-003       6.35  <-- SCF
      5  -8.55252149E+002  6.41285289E+000   1.16974969E-004       7.32  <-- SCF
      6  -8.55252287E+002  6.41587053E+000   1.72377084E-005       8.24  <-- SCF
      7  -8.55252287E+002  6.41594067E+000   3.26253889E-008       9.06  <-- SCF
      8  -8.55252287E+002  6.41596323E+000   3.51299774E-009       9.66  <-- SCF
      9  -8.55252287E+002  6.41596472E+000   5.97688637E-011      10.30  <-- SCF
------------------------------------------------------------------------ <-- SCF
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
 Norm of density residual is    1.8198587767920434E-002
      4  -3.20251292E+001 -1.00896738E+000  -5.04402177E-003       0.19  <-- SCF
 Norm of density residual is    4.8336394509986705E-003
      5  -3.20274863E+001 -9.34431339E-001   1.17854441E-003       0.20  <-- SCF
 Norm of density residual is    2.4445419297668830E-003
      6  -3.20288644E+001 -8.52312336E-001   6.89044014E-004       0.21  <-- SCF
 Norm of density residual is    4.1821859010725970E-004
      7  -3.20290142E+001 -8.38552464E-001   7.48852904E-005       0.22  <-- SCF
 Norm of density residual is    1.8888756088306457E-004
      8  -3.20290606E+001 -8.30220252E-001   2.32236773E-005       0.22  <-- SCF
 Norm of density residual is    1.9031324234710340E-005
      9  -3.20290615E+001 -8.29618993E-001   4.28146102E-007       0.23  <-- SCF
 Norm of density residual is    8.5739705761819795E-006
     10  -3.20290616E+001 -8.29279474E-001   7.35217415E-008       0.24  <-- SCF
 Norm of density residual is    2.7992383582111372E-006
     11  -3.20290616E+001 -8.29253836E-001   2.93980395E-011       0.25  <-- SCF
 Norm of density residual is    9.7598758436062017E-007
------------------------------------------------------------------------ <-- SCF
Total energy has converged after 11 SCF iterations.
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

        test_text = io.StringIO("""
Norm of density residual is    4.3364941873131582E-004
Symmetrising density
Calculating local potential
Calculating non-local weights
Starting SCF cycle     7 of up to    30
 no. bands in each block=           6
Kinetic eigenvalue #   1 =     0.91360283E+01
Kinetic eigenvalue #   2 =     0.17477724E+02
Kinetic eigenvalue #   3 =     0.24139426E+02
Kinetic eigenvalue #   4 =     0.36507521E+02
Kinetic eigenvalue #   5 =     0.56139250E+02
Kinetic eigenvalue #   6 =     0.62117028E+02
Kinetic eigenvalue #   7 =     0.37538708E+02
Kinetic eigenvalue #   8 =     0.48623103E+02
Kinetic eigenvalue #   9 =     0.54559209E+02
Kinetic eigenvalue #  10 =     0.59832639E+02
 Calculating the R matrix for the precon Sinv operator
 Diagonalising expanded subspace
 Copying updated data back
eigenvalue    1 init= -20.09     fin= -20.09     change= 0.1500E-06
eigenvalue    2 init= -15.74     fin= -15.74     change= 0.1570E-06
eigenvalue    3 init= -7.181     fin= -7.181     change= 0.4702E-06
eigenvalue    4 init= -4.213     fin= -4.213     change= 0.2768E-06
eigenvalue    5 init= -1.423     fin= -1.423     change= 0.1818E-06
eigenvalue    6 init= 0.6796     fin= 0.6796     change= 0.5603E-06
 Checking convergence criteria
Calculating KE and non-local eigenvalues to find total energy

End of SCF cycle energies
Exchange-correlation energy      =      -285.30695035635665135 eV
+Hartree energy                  =       149.79508122031259632 eV
+Local pseudopotential energy    =      -478.54332484459945363 eV
----------------------------------
Potential energy (total)         =      -614.07079171278496688 eV

+Kinetic energy                  =       776.02296679748712904 eV
+Non-local energy                =      -288.24562390518951815 eV
+Ewald energy (const)            =     -1089.18583097099849510 eV
+non-Coulombic energy (const)    =       146.91503528947745849 eV
----------------------------------
Total energy                     =     -1068.56424450200847787 eV

(XC correction to eigenvalue sum =        86.52766346075705428 eV)
(Apolar corr to eigenvalue sum   =         0.00000000000000000 eV)
(Hubbard U correction to eigenvalu         0.00000000000000000 eV)
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

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
            self.skipTest("Not implemented yet")
            test_dict = parse_castep_file.parse_castep_file(test_text)[0]
            pprint.pprint(test_dict)
            self.assertEqual(test_dict, {})

    def test_get_line_min(self):
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
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'energies': (-1267.604578357, -855.4591023999, -855.471052),
                                     'free_energies': [-855.462566483],
                                     'dedlne': [-3.335211]})

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

        """)
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'forces':
                                     {'non-descript': [{
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
        self.skipTest('Not implemented yet')
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'stresses':
                                     {
                                         'non-descript': (10.491143, -1.300645, -2.326648,
                                                          3.068913, -5.026993,
                                                          6.215774),
                                         'fun': (10.882675, 0.0, 0.0,
                                                 10.882675, -0.0,
                                                 10.882675)
                                     }
                                     }
                         )

    def test_get_md_data(self):
        test_text = io.StringIO("""
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            x                                               MD Data:     x
            x                                                            x
            x              time :      0.012000                   ps     x
            x                                                            x
            x   Potential Energy:   -856.781164                   eV     x
            x   Kinetic   Energy:      1.153823                   eV     x
            x   Total     Energy:   -855.627341                   eV     x
            x           Enthalpy:   -855.627341                   eV     x
            x   Hamilt    Energy:   -853.038128                   eV     x
            x                                                            x
            x        Temperature:   1115.796413                    K     x
            x      T/=0 Pressure:     -5.803316                  GPa     x
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """)
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'md':
                                     [{'time': 0.012,
                                       'Potential Energy': -856.781164,
                                       'Kinetic Energy': 1.153823,
                                       'Total Energy': -855.627341,
                                       'Enthalpy': -855.627341,
                                       'Hamilt Energy': -853.038128,
                                       'Temperature': 1115.796413}
                                      ]}
                         )

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

        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
  -------------------------------------------
                           Total:      19.999
  -------------------------------------------
The total projected population is   19.999   0.000

        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_bond(self):
        test_text = io.StringIO("""
                 Bond                   Population      Length (A)
======================================================================
              Si 1 -- Si 2                   3.06        2.33434
======================================================================
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

    def test_get_pair_params(self):
        test_text = io.StringIO("""
   ************************     PairParams     ************************
   *                                                                  *
   *                               Two Body                           *
   *         H  -H       H  -He      He -H       He -He               *
   *    r      8.51250     8.51250     8.51250     8.51250   A        * <--   LJ
   *    e      0.00009     0.00017     0.00017     0.00017   eV       * <--   LJ
   *    s      1.00000     2.00000     2.00000     2.00000   A        * <--   LJ
   *         H  -H       H  -N       N  -H       N  -N                *
   *    r      8.51250     8.51250     8.51250     8.51250   A        * <--   LJ
   *    e      0.00009     0.00026     0.00026     0.00026   eV       * <--   LJ
   *    s      1.00000     3.00000     3.00000     3.00000   A        * <--   LJ
   *         He -He      He -N       N  -He      N  -N                *
   *    r      8.51250     8.51250     8.51250     8.51250   A        * <--   LJ
   *    e      0.00017     0.00026     0.00026     0.00026   eV       * <--   LJ
   *    s      2.00000     3.00000     3.00000     3.00000   A        * <--   LJ
   ********************************************************************

        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
 +     3      66.963896   b          0.0000000  N                       N     +
 +     4     523.060071   c          0.0000000  N                       Y     +
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
 +     4     416.931632   b                                                   +
 +     5     466.400731   a                                                   +
 +     6     466.400731   a                                                   +
 + .......................................................................... +
 +        Character table from group theory analysis of eigenvectors          +
 +                           Point Group =  32, Oh                            +
 + .......................................................................... +
 +  Rep  Mul |    E   2   2   4   2   I   m   m  -4   m                       +
 +           | ----------------------------------------                       +
 + a       2 |    2   0  -2   0   0   0   0   0   0   0                       +
 + b       1 |    2   0   2   0   0   0   0   0   0   2                       +
 ==============================================================================
        """)
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'phonons': [{'N': (1, 2, 3, 4, 5, 6),
                                                  'active': ['N', 'N', 'N', 'N', 'N', 'N'],
                                                  'frequency': (-0.026685,
                                                                -0.026685,
                                                                66.963896,
                                                                523.060071,
                                                                523.060071,
                                                                523.060071),
                                                  'intensity': (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                                                  'irrep': ['a', 'a', 'b', 'c', 'c', 'c'],
                                                  'qpt': (0.0, 0.0, 0.0),
                                                  'raman_active': ['N', 'N', 'N', 'Y', 'Y', 'Y']},
                                                 {'N': (1, 2, 3, 4, 5, 6),
                                                  'frequency': (151.96043,
                                                                151.96043,
                                                                416.931632,
                                                                416.931632,
                                                                466.400731,
                                                                466.400731),
                                                  'irrep': ['a', 'a', 'b', 'b', 'a', 'a'],
                                                  'qpt': (0.5, 0.5, 0.0)}]})

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
   Phonon Symmetry Analysis:    Phase of dynamical matrix elements
   Normalized to range (-pi/2,pi/2] to remove x,-x ambiguity.
  ************************************************************************
  -0.0   0.0  -0.0   0.0   0.0   0.0   0.0   0.0   0.0  -0.0   0.0   0.0
   0.0   0.0   0.0   0.0  -0.0   0.0   0.0  -0.0   0.0   0.0  -0.0   0.0
   0.0   0.0   0.0   0.0   0.0  -0.0   0.0   0.0   0.0   0.0   0.0   0.0
   0.0   0.0   0.0  -0.0   0.0  -0.0  60.0   0.0  60.0   0.0   0.0  -0.0
   0.0  -0.0   0.0   0.0   0.0   0.0   0.0  60.0   0.0   0.0   0.0   0.0
  -0.0   0.0   0.0   0.0   0.0  -0.0  60.0   0.0  60.0  -0.0   0.0   0.0
  -0.0   0.0  -0.0 -60.0   0.0 -60.0  -0.0   0.0  -0.0 -60.0   0.0 -60.0
   0.0   0.0   0.0   0.0 -60.0   0.0   0.0   0.0   0.0   0.0 -60.0   0.0
  -0.0   0.0  -0.0 -60.0   0.0 -60.0  -0.0   0.0  -0.0 -60.0   0.0 -60.0
   0.0   0.0  -0.0  -0.0   0.0   0.0  60.0   0.0  60.0   0.0   0.0   0.0
   0.0   0.0   0.0   0.0  -0.0   0.0   0.0  60.0   0.0   0.0   0.0   0.0
   0.0   0.0   0.0   0.0   0.0  -0.0  60.0   0.0  60.0  -0.0   0.0   0.0

  ************************************************************************
  Phonon Symmetry Analysis:     Rotation sense of phase +/0/- (0==absolute)
  ************************************************************************
     0     0    -1    -1     0    -1    -1     0    -1    -1     0    -1
     0     0     0     0    -1     0     0    -1     0     0    -1     0
     1     0     0    -1     0    -1    -1     0    -1    -1     0    -1
     1     0     1     0     0    -1    -1     0    -1    -1     0    -1
     0     1     0     0     0     0     0    -1     0     0    -1     0
     1     0     1     1     0     0    -1     0    -1    -1     0    -1
     1     0     1     1     0     1     0     0     1     1     0     1
     0     1     0     0     1     0     0     0     0     0     1     0
     1     0     1     1     0     1    -1     0     0     1     0     1
     1     0     1     1     0     1    -1     0    -1     0     0     1
     0     1     0     0     1     0     0    -1     0     0     0     0
     1     0     1     1     0     1    -1     0    -1    -1     0     0


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
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_dynamical_matrix(self):
        test_text = io.StringIO("""
  ------------------------------------------------------------------------------------------------------------------
            Dynamical matrix
 Ion XYZ        real part  ((cm-1)**2)
   1   1       5500.924553          0.000000         -0.000000      -5318.574282         -0.000000          0.000000
   1   2          0.000000       5500.924553         -0.000000         -0.000000      -5318.574282          0.000000
   1   3          0.000000         -0.000000       5500.924553         -0.000000          0.000000      -5318.574282
   2   1      -5318.574282         -0.000000          0.000000       5142.268276          0.000000         -0.000000
   2   2         -0.000000      -5318.574282          0.000000          0.000000       5142.268276         -0.000000
   2   3         -0.000000          0.000000      -5318.574282         -0.000000         -0.000000       5142.268276
 Ion XYZ        imaginary part  ((cm-1)**2)
   1   1          0.000000          0.000000          0.000000          0.000000          0.000000          0.000000
   1   2          0.000000          0.000000          0.000000          0.000000          0.000000          0.000000
   1   3          0.000000          0.000000          0.000000          0.000000          0.000000          0.000000
   2   1          0.000000          0.000000          0.000000          0.000000          0.000000          0.000000
   2   2          0.000000          0.000000          0.000000          0.000000          0.000000          0.000000
   2   3          0.000000          0.000000          0.000000          0.000000          0.000000          0.000000
  ------------------------------------------------------------------------------------------------------------------
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

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

        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'dc_permittivity': [(4.6507, -0.0, -0.0),
                                                         (-0.0, 4.6507, -0.0),
                                                         (-0.0, -0.0, 4.6507)],
                                     'optical_permittivity': [(2.63735, 0.0, 0.0),
                                                              (0.0, 2.63735, 0.0),
                                                              (0.0, 0.0, 2.63735)]})

        test_text = io.StringIO("""
 =======================================
      Optical Permittivity (f->infinity)
      ----------------------------------
         8.50261     0.00000     0.00000
         0.00000     8.50261     0.00000
         0.00000     0.00000     8.50261
 =======================================
        """)
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'optical_permittivity': [(8.50261, 0.0, 0.0),
                                                               (0.0, 8.50261, 0.0),
                                                               (0.0, 0.0, 8.50261)]})

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

        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'optical_polarisability': [(9.42606, 0.0, 0.0),
                                                                (0.0, 9.42606, 0.0),
                                                                (0.0, 0.0, 9.42606)],
                                     'static_polarisability': [(21.01677, -0.0, -0.0),
                                                               (-0.0, 21.01677, -0.0),
                                                               (-0.0, -0.0, 21.01677)]})
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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'optical_polarisability': [(24.17525, 0.0, 0.0),
                                                                (0.0, 24.17525, 0.0),
                                                                (0.0, 0.0, 24.17525)]})

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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'nlo': [['-1.28186',
                                               '0.01823',
                                               '0.01838',
                                               '23.46304',
                                               '0.01828',
                                               '0.01832'],
                                              ['0.01832',
                                               '-1.28120',
                                               '0.01830',
                                               '0.01831',
                                               '23.46304',
                                               '0.01823'],
                                              ['0.01828',
                                               '0.01831',
                                               '-1.28185',
                                               '0.01830',
                                               '0.01838',
                                               '23.46304']]
                                     })

    def test_get_born_charges(self):
        test_text = io.StringIO("""
 ===================================================
                   Born Effective Charges
                   ----------------------
   Si      1        -2.01676     0.00000    -0.00000
                     0.00000    -3.01676    -0.00000
                     0.00000    -0.00000    -4.01676
   Si      2        -5.01676     0.00000    -0.00000
                     0.00000    -6.01676    -0.00000
                     0.00000    -0.00000    -7.01676
 ===================================================

        """)

        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'born': [{('Si', 1): ((-2.01676, 0.0, -0.0),
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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'raman': [[{'II': 0.0,
                                                 'depolarisation': 0.749632,
                                                 'tensor': ((-0.0, 0.0, -0.0),
                                                            (0.0, 0.0, 0.0),
                                                            (-0.0, 0.0, 0.0)),
                                                 'trace': 0.0},
                                                {'II': 0.79384156,
                                                 'depolarisation': 0.75,
                                                 'tensor': ((0.0, -0.0, -0.0),
                                                            (-0.0, -2.5, -1.3062),
                                                            (-0.0, -1.3062, -1.0)),
                                                 'trace': -3.5}]]}
                         )

    def test_get_mil_dipole(self):
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
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_spin_density(self):
        test_text = io.StringIO("""
Integrated Spin Density     =    0.177099E-07 hbar/2
Integrated |Spin Density|   =     3.07611     hbar/2
            """)
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'spin': [1.77099e-08],
                                     'modspin': [3.07611]})

    def test_get_elf(self):
        test_text = io.StringIO("""
      ELF grid sample
-----------------------
 ELF        1 0.506189
 ELF        2 0.506191
 ELF        3 0.506194
-----------------------
        """)
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

        self.assertEqual(test_dict, {'hirshfeld': {('H', 1): -1.0,
                                                   ('F', 1): 17.0}}
                         )

    def test_lbfgs_output(self):
        test_text = io.StringIO("""
 LBFGS: finished iteration     0 with enthalpy= -1.31770077E+003 eV

 +-----------+-----------------+-----------------+------------+-----+ <-- LBFGS
 | Parameter |      value      |    tolerance    |    units   | OK? | <-- LBFGS
 +-----------+-----------------+-----------------+------------+-----+ <-- LBFGS
 |  dE/ion   |   0.000000E+000 |   2.000000E-005 |         eV | No  | <-- LBFGS
 |  |F|max   |   3.553106E-001 |   5.000000E-003 |       eV/A | No  | <-- LBFGS
 |  |dR|max  |   0.000000E+000 |   1.000000E-003 |          A | No  | <-- LBFGS
 +-----------+-----------------+-----------------+------------+-----+ <-- LBFGS

================================================================================
 Starting LBFGS iteration          1 ...
================================================================================

 +------------+-------------+-------------+-----------------+ <-- min LBFGS
 |    Step    |   lambda    |   F.delta'  |    enthalpy     | <-- min LBFGS
 +------------+-------------+-------------+-----------------+ <-- min LBFGS
 |  previous  |    0.000000 |    0.073978 |    -1317.700775 | <-- min LBFGS
 +------------+-------------+-------------+-----------------+ <-- min LBFGS

 TPSD: finished iteration     0 with enthalpy= -2.16058016E+002 eV

 +------------+-------------+-------------+-----------------+ <-- min TPSD
 |    Step    |   lambda    |   F.delta'  |    enthalpy     | <-- min TPSD
 +------------+-------------+-------------+-----------------+ <-- min TPSD
 |  previous  |    0.000000 |    0.203755 |     -216.058941 | <-- min TPSD
 +------------+-------------+-------------+-----------------+ <-- min TPSD

 +------------+-------------+-------------+-----------------+ <-- min TPSD
 |    Step    |   lambda    |   F.delta'  |    enthalpy     | <-- min TPSD
 +------------+-------------+-------------+-----------------+ <-- min TPSD
 |  previous  |    0.000000 |    0.204256 |     -216.058016 | <-- min TPSD
 | trial step |    0.001727 |    0.204121 |     -216.058941 | <-- min TPSD
 +------------+-------------+-------------+-----------------+ <-- min TPSD

 +-----------+-----------------+-----------------+------------+-----+ <-- TPSD
 | Parameter |      value      |    tolerance    |    units   | OK? | <-- TPSD
 +-----------+-----------------+-----------------+------------+-----+ <-- TPSD
 |  dE/ion   |   0.000000E+000 |   2.000000E-005 |         eV | No  | <-- TPSD
 |  |F|max   |   5.299770E-001 |   5.000000E-002 |       eV/A | No  | <-- TPSD
 |  |dR|max  |   0.000000E+000 |   1.000000E-003 |          A | No  | <-- TPSD
 |   Smax    |   1.736649E+001 |   1.000000E-001 |        GPa | No  | <-- TPSD
 +-----------+-----------------+-----------------+------------+-----+ <-- TPSD

        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

    def test_get_lbfgs_info(self):
        test_text = io.StringIO("""
 LBFGS: Final Enthalpy     = -1.31770414E+003 eV
 LBFGS: Final <frequency>  =    1073.37660 cm-1
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
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
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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

    def test_get_bs_time(self):
        test_text = io.StringIO("""
        Total time to compute matrix elements              1.36 sec |<-- SPEC
        """)
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
  |    H:T                3       28.71       7.26      N/A   1.996E-01   0.01 |
  ===============================================================================
        """)
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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
        self.skipTest("Not implemented yet")
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]
        pprint.pprint(test_dict)
        self.assertEqual(test_dict, {})

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
        test_dict = parse_castep_file.parse_castep_file(test_text)[0]

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


if __name__ == '__main__':
    main()
