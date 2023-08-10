# pylint: skip-file

import unittest
import io
import json
import pprint
from pathlib import Path

from castep_outputs.castep_outputs_main import (parse_all, parse_single)

try:
    from ruamel import yaml
    _YAML_TYPE = "ruamel"
except ImportError:
    try:
        import yaml
        _YAML_TYPE = "yaml"
    except ImportError:
        _YAML_TYPE = None


_TEST_FOLDER = Path(__file__).parent


class test_dumper(unittest.TestCase):

    def _test_dump(self, file, typ, out_format, ref_file=None):
        if out_format == 'yaml' and _YAML_TYPE is None:
            self.skipTest('YAML not found')

        if out_format == 'json':
            loader = json.load
        elif _YAML_TYPE == 'ruamel':
            yaml_eng = yaml.YAML(typ='unsafe')
            loader = yaml_eng.load
        elif _YAML_TYPE == 'yaml':
            loader = yaml.load

        test = io.StringIO()
        parse_all(test, out_format=out_format, **{typ: [file]})
        test.seek(0)

        if ref_file is None:
            ref_file = _TEST_FOLDER / f"{typ}.{out_format}"

        with open(ref_file, 'r', encoding='utf-8') as test_file:
            for test_lines in zip(test, test_file):
                self.assertEqual(*test_lines)

        comp_dict = parse_single(file, out_format=out_format)

        with open(ref_file, 'r', encoding='utf-8') as test_file:
            ref_dict = loader(test_file)

        self.assertEqual(comp_dict, ref_dict)

    def test_dumpers(self):
        for file_type in ("cell", "param", "castep", "bands", "md",
                          "elastic", "ts", "chdiff_fmt", "den_fmt",
                          "pot_fmt", "elf_fmt", "xrd_sf", "phonon_dos",
                          "efield", "magres"):
            for dumper_type in ("json", "yaml"):
                with self.subTest(file=file_type, dumper=dumper_type):
                    self._test_dump(_TEST_FOLDER / f"test.{file_type}",
                                    file_type, dumper_type)


if __name__ == '__main__':
    unittest.main()
