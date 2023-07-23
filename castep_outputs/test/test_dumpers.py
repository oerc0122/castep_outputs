import unittest
import io
from pathlib import Path

from castep_outputs.castep_outputs_main import parse_all

_TEST_FOLDER = Path(__file__).parent


class test_dumper(unittest.TestCase):

    def _test_dump(self, file, typ, out_format, ref_file=None):
        test = io.StringIO()
        parse_all(test, out_format=out_format, **{typ: [file]})
        test.seek(0)


        if ref_file is None:
            ref_file = _TEST_FOLDER / f"{typ}.{out_format}"

        with open(ref_file, 'r', encoding='utf-8') as test_file:
            for test_lines in zip(test, test_file):
                self.assertEqual(*test_lines)

    def test_json_dumper_cell(self):
        self._test_dump(_TEST_FOLDER / 'test.cell', 'cell', 'json')

    def test_yaml_dumper_cell(self):
        self._test_dump(_TEST_FOLDER / 'test.cell', 'cell', 'yaml')

    def test_json_dumper_param(self):
        self._test_dump(_TEST_FOLDER / 'test.param', 'param', 'json')

    def test_yaml_dumper_param(self):
        self._test_dump(_TEST_FOLDER / 'test.param', 'param', 'yaml')

    def test_json_dumper_castep(self):
        self._test_dump(_TEST_FOLDER / 'test.castep', 'castep', 'json')

    def test_yaml_dumper_castep(self):
        self._test_dump(_TEST_FOLDER / 'test.castep', 'castep', 'yaml')

    def test_json_dumper_bands(self):
        self._test_dump(_TEST_FOLDER / 'test.bands', 'bands', 'json')

    def test_yaml_dumper_bands(self):
        self._test_dump(_TEST_FOLDER / 'test.bands', 'bands', 'yaml')


if __name__ == '__main__':
    unittest.main()
