# pylint: skip-file

from pathlib import Path
from unittest import TestCase

from castep_outputs import parse_castep_file
from castep_outputs.parsers.castep_file_parser import Filters

_TEST_FOLDER = Path(__file__).parent
_TEST_FILE = _TEST_FOLDER / "test.castep"


class test_castep_filters(TestCase):
    def setUp(self):
        self.test_text = _TEST_FILE.open("r", encoding="utf-8")

    def tearDown(self):
        self.test_text.close()

    def test_filter_all(self):
        for filtery, keys in ((Filters.CELL, ('initial_cell',)),
                              (Filters.PARAMETERS, ('title', 'options', 'initial_spins', 'k-points', 'target_stress')),
                              (Filters.POSITION, ('initial_positions',)),
                              (Filters.PSPOT, ('pspot_detail',)),
                              (Filters.SPECIES_PROPS, ('species_properties',)),
                              (Filters.SYMMETRIES, ('symmetries', 'constraints')),
                              (Filters.SYS_INFO, ('build_info', 'time_started', 'warning', 'memory_estimate')),
                              (Filters.LOW, ('species_properties', 'initial_cell', 'initial_positions')),
                              (Filters.MEDIUM, ('species_properties', 'title', 'options', 'initial_cell',
                                                 'initial_positions', 'initial_spins', 'k-points', 'target_stress')),
                              (Filters.HIGH, ('build_info', 'time_started', 'warning', 'pspot_detail',
                                               'species_properties', 'title', 'options',
                                               'initial_cell', 'initial_positions', 'initial_spins', 'k-points',
                                               'symmetries', 'constraints', 'target_stress', 'memory_estimate')),
                              (Filters.FULL, ('build_info', 'time_started', 'warning', 'pspot_detail',
                                              'species_properties', 'title', 'options', 'initial_cell',
                                              'initial_positions', 'initial_spins', 'k-points', 'symmetries',
                                              'constraints', 'target_stress', 'memory_estimate')),
                              (Filters.TESTING, ('pspot_detail', 'species_properties', 'initial_cell', 'initial_positions'))):
            with self.subTest(filters=filtery.name):
                self.test_text.seek(0)
                data = parse_castep_file(self.test_text, filters=filtery)
                assert all(key in data[0] for key in keys)

    def test_filter_none(self):
        data = parse_castep_file(self.test_text, filters=Filters.NONE)
        assert not data
