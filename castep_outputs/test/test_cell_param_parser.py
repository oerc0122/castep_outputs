# pylint: skip-file

import io
import pprint
import unittest

from castep_outputs.parsers import parse_cell_param_file


class test_cell_parser(unittest.TestCase):

    def test_parse_lattice_abc(self):
        test_text = io.StringIO("""
%BLOCK LATTICE_ABC
    8.9780000000    5.7400000000	9.9690000000
    90.000000000    90.000000000	90.000000000
%ENDBLOCK LATTICE_ABC
    """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'lattice_abc': {'data': [(8.978, 5.74, 9.969),
                                                              (90.0, 90.0, 90.0)]}})

    def test_parse_lattice_cart(self):
        test_text = io.StringIO("""
%BLOCK LATTICE_CART
ang    # angstrom units
   6.314500000000000   0.000000000000000   0.000000000000000
   0.000000000000000   6.314500000000000   0.000000000000000
   0.000000000000000   0.000000000000000   6.314500000000000
%ENDBLOCK LATTICE_CART
    """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'lattice_cart': {'data': [(6.3145, 0.0, 0.0),
                                                               (0.0, 6.3145, 0.0),
                                                               (0.0, 0.0, 6.3145)],
                                                      'units': 'ang'}})

    def test_parse_mixture(self):
        test_text = io.StringIO("""
%BLOCK POSITIONS_FRAC
    Al    0.2500000000    0.5000000000    0.0000000000 MIXTURE:(   1  0.666667)
    Al   -0.2500000000   -0.5000000000    0.0000000000 MIXTURE:(   2  0.666667)
    Al    0.2500000000    0.0000000000    0.5000000000 MIXTURE:(   3  0.666667)
    Si    0.2500000000    0.5000000000    0.0000000000 MIXTURE:(   1  0.333333)
    Si   -0.2500000000   -0.5000000000    0.0000000000 MIXTURE:(   2  0.333333)
    Si    1/4    0    1/2 MIXTURE:(   3  0.333333)
%ENDBLOCK POSITIONS_FRAC
    """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'positions_frac': {('Al', 1): {'mixed': 1,
                                                                    'pos': (0.25, 0.5, 0.0),
                                                                    'ratio': 0.666667},
                                                        ('Al', 2): {'mixed': 2,
                                                                    'pos': (-0.25, -0.5, 0.0),
                                                                    'ratio': 0.666667},
                                                        ('Al', 3): {'mixed': 3,
                                                                    'pos': (0.25, 0.0, 0.5),
                                                                    'ratio': 0.666667},
                                                        ('Si', 1): {'mixed': 1,
                                                                    'pos': (0.25, 0.5, 0.0),
                                                                    'ratio': 0.333333},
                                                        ('Si', 2): {'mixed': 2,
                                                                    'pos': (-0.25, -0.5, 0.0),
                                                                    'ratio': 0.333333},
                                                        ('Si', 3): {'mixed': 3,
                                                                    'pos': (0.25, 0.0, 0.5),
                                                                    'ratio': 0.333333}}})

    def test_parse_spin_magmom(self):
        test_text = io.StringIO("""
%BLOCK POSITIONS_FRAC
    Fe 0.00    0.00    0.00
    Fe 0.50    0.50    0.00 SPIN= 1/2
    Fe 0.50    0.00    0.50 SPIN : -2
    Fe 0.00    0.50    0.50 MAGMOM 4
%ENDBLOCK POSITIONS_FRAC
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'positions_frac': {('Fe', 1): {'pos': (0.0, 0.0, 0.0)},
                                                        ('Fe', 2): {'pos': (0.5, 0.5, 0.0), 'spin': 0.5},
                                                        ('Fe', 3): {'pos': (0.5, 0.0, 0.5), 'spin': -2.0},
                                                        ('Fe', 4): {'pos': (0.0, 0.5, 0.5), 'spin': 4.0}}})

    def test_parse_position_abs(self):
        test_text = io.StringIO("""
%BLOCK POSITIONS_ABS
    O     6.2450000000   -2.3470000000    3.0440000000
    Al    5.7110000000    2.3470000000    5.0230000000
    Al    1    1/2  1/3
%ENDBLOCK POSITIONS_ABS
    """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'positions_abs': {('Al', 1): {'pos': (5.711, 2.347, 5.023)},
                                                       ('Al', 2): {'pos': (1.0, 1/2, 1/3)},
                                                       ('O', 1): {'pos': (6.245, -2.347, 3.044)}}})

    def test_parse_cell_constraints(self):
        test_text = io.StringIO("""
%BLOCK CELL_CONSTRAINTS
       1       2       3
       0       0       0
%ENDBLOCK CELL_CONSTRAINTS
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'cell_constraints': {'data': [(1.0, 2.0, 3.0),
                                                                   (0.0, 0.0, 0.0)]}})

    def test_parse_ionic_constraints(self):
        test_text = io.StringIO("""
%BLOCK IONIC_CONSTRAINTS
       1       W       1    1.0000000000    0.0000000000    0.0000000000
       2       W       1    0.0000000000    1.0000000000    0.0000000000
       3       W       1    0.0000000000    0.0000000000    1.0000000000
       4       W       2    1.0000000000    0.0000000000    0.0000000000
%ENDBLOCK IONIC_CONSTRAINTS
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'ionic_constraints': {('W', 1): [(1.0, 0.0, 0.0),
                                                                      (0.0, 1.0, 0.0),
                                                                      (0.0, 0.0, 1.0)],
                                                           ('W', 2): [(1.0, 0.0, 0.0)]}})

    def test_parse_nonlinear_constraints(self):
        test_text = io.StringIO("""
%BLOCK NONLINEAR_CONSTRAINTS
distance       H  4  0  0  0       O  2  0  1  0
    bend       H  5  0  0  0       C  1  1  0  1       H  2  0  0  0
 torsion       H  6  0  0  0       H  3  1  0  0       H  1  0  0  1       H  9  1  1  0
%ENDBLOCK NONLINEAR_CONSTRAINTS
    """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'nonlinear_constraints': [{'key': 'distance',
                                                                'atoms': {('H', 4): (0, 0, 0),
                                                                          ('O', 2): (0, 1, 0)},
                                                                },
                                                               {'key': 'bend',
                                                                'atoms': {('C', 1): (1, 0, 1),
                                                                          ('H', 2): (0, 0, 0),
                                                                          ('H', 5): (0, 0, 0)},
                                                                },
                                                               {'key': 'torsion',
                                                                'atoms': {('H', 1): (0, 0, 1),
                                                                          ('H', 3): (1, 0, 0),
                                                                          ('H', 6): (0, 0, 0),
                                                                          ('H', 9): (1, 1, 0)},
                                                                }]})

    def test_parse_external_pressure(self):
        test_text = io.StringIO("""
    %BLOCK EXTERNAL_PRESSURE
GPa
    5.0000000000    0.0000000000    0.0000000000
                    5.0000000000    0.0000000000
                                    5.0000000000
%ENDBLOCK EXTERNAL_PRESSURE

        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'external_pressure': {'data': [(5.0, 0.0, 0.0),
                                                                    (5.0, 0.0),
                                                                    (5.0,)],
                                                           'units': 'GPa'}})

    def test_parse_weighted_kpoints(self):
        test_text = io.StringIO("""
%BLOCK SUPERCELL_KPOINT_LIST
    0.0000000000    0.0000000000    0.0000000000    0.0800000000
    0.0000000000    0.0833333333    0.0000000000    0.0400000000
    0.0000000000    0.1666666667    0.0000000000    0.0400000000
%ENDBLOCK SUPERCELL_KPOINT_LIST
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'supercell_kpoint_list': {'data': [(0.0, 0.0, 0.0, 0.08),
                                                                        (0.0, 0.0833333333, 0.0, 0.04),
                                                                        (0.0, 0.1666666667, 0.0, 0.04)]}})

    def test_parse_supercell_matrix(self):
        test_text = io.StringIO("""
%BLOCK PHONON_SUPERCELL_MATRIX
 2 2 0
 0 2 2
 2 0 2
%ENDBLOCK PHONON_SUPERCELL_MATRIX
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'phonon_supercell_matrix': {'data': [(2.0, 2.0, 0.0),
                                                                          (0.0, 2.0, 2.0),
                                                                          (2.0, 0.0, 2.0)]}})

    def test_parse_symops(self):
        test_text = io.StringIO("""
%BLOCK SYMMETRY_OPS
    # SYM OP 1
   -1.0000000000    0.0000000000    0.0000000000
    0.0000000000   -1.0000000000    0.0000000000
    0.0000000000    0.0000000000    1.0000000000
    0.5000000000    0.0000000000    0.5000000000
    # SYM OP 2
    1.0000000000    0.0000000000    0.0000000000
    0.0000000000    1.0000000000    0.0000000000
    0.0000000000    0.0000000000    1.0000000000
    0.5000000000    0.0000000000    0.5000000000
%ENDBLOCK SYMMETRY_OPS
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'symmetry_ops': [{'r': [(-1.0, 0.0, 0.0),
                                                             (0.0, -1.0, 0.0),
                                                             (0.0, 0.0, 1.0)],
                                                       't': (0.5, 0.0, 0.5)},
                                                      {'r': [(1.0, 0.0, 0.0),
                                                             (0.0, 1.0, 0.0),
                                                             (0.0, 0.0, 1.0)],
                                                       't': (0.5, 0.0, 0.5)}]})


    def test_parse_quantisation_axis(self):
        test_text = io.StringIO("""
QUANTIZATION_AXIS : 1 1 -1
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'quantization_axis': (1, 1, -1)})

    def test_parse_external_efield(self):
        test_text = io.StringIO("""
%BLOCK EXTERNAL_EFIELD
HARTREE/BOHR/E
0.0 1.0 0.1
%ENDBLOCK EXTERNAL_EFIELD
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'external_efield': {'data': [(0.0, 1.0, 0.1)],
                                                         'units': 'HARTREE/BOHR/E'}})

    def test_parse_ionic_velocities(self):
        test_text = io.StringIO("""
%BLOCK IONIC_VELOCITIES
ang/ps
 1.000  2.000  1.000
 2.000  3.000  3.000
-2.000 -3.000 -3.000
-1.000 -2.000 -1.000
%ENDBLOCK IONIC_VELOCITIES
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'ionic_velocities': {'data': [(1.0, 2.0, 1.0),
                                                                   (2.0, 3.0, 3.0),
                                                                   (-2.0, -3.0, -3.0),
                                                                   (-1.0, -2.0, -1.0)],
                                                          'units': 'ang/ps'}})

    def test_parse_kpoint_path(self):
        test_text = io.StringIO("""
%BLOCK BS_KPOINT_PATH
    0.3333333333    0.3750000000    0.3333333333
    0.3333333333    0.3750000000    0.0000000000
    1/3             1/8             1/3
%ENDBLOCK BS_KPOINT_PATH
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'bs_kpoint_path': {'data': [(0.3333333333, 0.375, 0.3333333333),
                                                                 (0.3333333333, 0.375, 0.0),
                                                                 (0.3333333333333333, 0.125, 0.3333333333333333),
                                                                 ]}})

    def test_parse_kpoint_spacing(self):
        test_text = io.StringIO("""
KPOINT_MP_SPACING = 0.25 1/Ang
BS_KPOINT_PATH_SPACING : 0.125
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {"kpoint_mp_spacing": (0.25, '1/Ang'),
                                     "bs_kpoint_path_spacing": 0.125})

    def test_parse_fix(self):
        test_text = io.StringIO("""
FIX_ALL_CELL : F
FIX_ALL_IONS : T
FIX_COM = false
FIX_VOL TRUE
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'fix_all_cell': False,
                                     'fix_all_ions': True,
                                     'fix_com': False,
                                     'fix_vol': True})

    def test_parse_lcao(self):
        test_text = io.StringIO("""
%BLOCK SPECIES_LCAO_STATES
       O         1
      Al         2
      Ti:tag     3
%ENDBLOCK SPECIES_LCAO_STATES
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'species_lcao_states': {'data': {'Al': 2,
                                                                      'O': 1,
                                                                      'Ti:tag': 3}}})

    def test_get_species_mass(self):
        test_text = io.StringIO("""
%BLOCK SPECIES_MASS
       O     15.9989995956
      Al     26.9820003510
      Ti:Tag 47.9000015259
      Cs    132.9049987793
%ENDBLOCK SPECIES_MASS
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'species_mass': {'data': {'Al': 26.982000351,
                                                               'Cs': 132.9049987793,
                                                               'O': 15.9989995956,
                                                               'Ti:Tag': 47.9000015259}}})

    def test_parse_sedc_params(self):
        test_text = io.StringIO("""
%BLOCK SEDC_CUSTOM_PARAMS
H C6:0.0 R0:1.6404 alpha:0.6668
Ti:Tag C6:1.0 R0:3.6404 alpha:-0.6668
%ENDBLOCK SEDC_CUSTOM_PARAMS
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'sedc_custom_params': {'H': {'C6': 0.0,
                                                                  'R0': 1.6404,
                                                                  'alpha': 0.6668},
                                                            'Ti:Tag': {'C6': 1.0,
                                                                       'R0': 3.6404,
                                                                       'alpha': -0.6668}}})

    def test_parse_hubbard_u(self):
        test_text = io.StringIO("""
%BLOCK HUBBARD_U
  eV
    Sm 1   f: 6.1
    Ni     d: 2.4
    U 2  d: 1.2 f: 2.1
%ENDBLOCK HUBBARD_U
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'hubbard_u': {'units': 'eV',
                                                   'Ni': {'d': 2.4},
                                                   ('Sm', 1): {'f': 6.1},
                                                   ('U', 2): {'d': 1.2, 'f': 2.1}}})


class test_param_parser(unittest.TestCase):
    def test_int_params(self):
        test_text = io.StringIO("""
BACKUP_INTERVAL : 3600
RUN_TIME=360
NLXC_PPD_SIZE_X  4
NLXC_PPD_SIZE_Y = 2
NLXC_PPD_SIZE_Z  -2
        """)
        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'backup_interval': 3600,
                                     'nlxc_ppd_size_x': 4,
                                     'nlxc_ppd_size_y': 2,
                                     'nlxc_ppd_size_z': -2.0,
                                     'run_time': 360})

    def test_bool_params(self):
        test_text = io.StringIO("""
CALCULATE_STRESS : TRUE
CALCULATE_DENSDIFF = TRUE
CALCULATE_ELF  F
CALCULATE_HIRSHFELD : False
        """)
        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'calculate_densdiff': True,
                                     'calculate_elf': False,
                                     'calculate_hirshfeld': False,
                                     'calculate_stress': True})

    def test_string_params(self):
        test_text = io.StringIO("""
charge_unit: e
CHECKPOINT : test.check
CONTINUATION : DEFAULT
PSPOT_BETA_PHI_TYPE = REAL
SMEARING_SCHEME  ColdSmearing
File_param aa.bbb
""")
        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'charge_unit': 'e',
                                     'checkpoint': 'test.check',
                                     'continuation': 'DEFAULT',
                                     'file_param': 'aa.bbb',
                                     'pspot_beta_phi_type': 'REAL',
                                     'smearing_scheme': 'ColdSmearing'})

    def test_vector_params(self):
        test_text = io.StringIO("""
kpoints_mp_grid : 10 10 10
        """)
        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'kpoints_mp_grid': (10, 10, 10)})

    def test_physical_params(self):
        test_text = io.StringIO("""
geom_energy_tol : 0.00005 eV
GEOM_MODULUS_EST = 125.4 GPa
MIX_METRIC_Q : 20.0
        """)

        test_dict = parse_cell_param_file(test_text)[0]

        self.assertEqual(test_dict, {'geom_energy_tol': (5e-05, 'eV'),
                                     'geom_modulus_est': (125.4, 'GPa'),
                                     'mix_metric_q': 20.0})

    def test_devel_code(self):
        test_text = io.StringIO("""
%block devel_code
bool_value=F
true_val=True
int_value=31
string_value=Hello
float_number=15.12
PP: test_par=1 :ENDPP
%endblock devel_code
        """)
        test_dict = parse_cell_param_file(test_text)[0]
        self.assertEqual(test_dict, {'devel_code': {'pp': {'test_par': 1},
                                                    'bool_value': False,
                                                    'true_val': True,
                                                    'float_number': 15.12,
                                                    'int_value': 31,
                                                    'string_value': 'Hello'}})


if __name__ == "__main__":
    unittest.main()
