# pylint: skip-file

import io
import json
import pprint
import unittest
from pathlib import Path

from castep_outputs.cli.castep_outputs_main import parse_all, parse_single
from castep_outputs.utilities.utility import normalise

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


def _to_complex(complx):
    if isinstance(complx, dict):
        if len(complx) == 2 and tuple(complx.keys()) == ("real", "imag"):
            return complex(**complx)
    return complx


class test_dumper(unittest.TestCase):

    maxDiff = 9999

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

        comp_dict = normalise(comp_dict, {dict: _to_complex})
        ref_dict = normalise(ref_dict, {dict: _to_complex})

        self.assertEqual(comp_dict, ref_dict)

    def test_cell_json(self):
        self._test_dump(_TEST_FOLDER / "test.cell", "cell", "json")

    def test_cell_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.cell", "cell", "yaml")

    def test_param_json(self):
        self._test_dump(_TEST_FOLDER / "test.param", "param", "json")

    def test_param_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.param", "param", "yaml")

    def test_castep_json(self):
        self._test_dump(_TEST_FOLDER / "test.castep", "castep", "json")

    def test_castep_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.castep", "castep", "yaml")

    def test_md_castep_json(self):
        self._test_dump(_TEST_FOLDER / "pp-md.castep", "castep", "json", _TEST_FOLDER / "pp-md.json")

    def test_md_castep_json(self):
        self._test_dump(_TEST_FOLDER / "pp-md.castep", "castep", "yaml", _TEST_FOLDER / "pp-md.yaml")

    def test_bands_json(self):
        self._test_dump(_TEST_FOLDER / "test.bands", "bands", "json")

    def test_bands_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.bands", "bands", "yaml")

    def test_md_json(self):
        self._test_dump(_TEST_FOLDER / "test.md", "md", "json")

    def test_md_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.md", "md", "yaml")

    def test_elastic_json(self):
        self._test_dump(_TEST_FOLDER / "test.elastic", "elastic", "json")

    def test_elastic_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.elastic", "elastic", "yaml")

    def test_ts_json(self):
        self._test_dump(_TEST_FOLDER / "test.ts", "ts", "json")

    def test_ts_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.ts", "ts", "yaml")

    def test_chdiff_fmt_json(self):
        self._test_dump(_TEST_FOLDER / "test.chdiff_fmt", "chdiff_fmt", "json")

    def test_chdiff_fmt_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.chdiff_fmt", "chdiff_fmt", "yaml")

    def test_den_fmt_json(self):
        self._test_dump(_TEST_FOLDER / "test.den_fmt", "den_fmt", "json")

    def test_den_fmt_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.den_fmt", "den_fmt", "yaml")

    def test_pot_fmt_json(self):
        self._test_dump(_TEST_FOLDER / "test.pot_fmt", "pot_fmt", "json")

    def test_pot_fmt_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.pot_fmt", "pot_fmt", "yaml")

    def test_elf_fmt_json(self):
        self._test_dump(_TEST_FOLDER / "test.elf_fmt", "elf_fmt", "json")

    def test_elf_fmt_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.elf_fmt", "elf_fmt", "yaml")

    # def test_xrd_sf_json(self):
    #     self._test_dump(_TEST_FOLDER / "test.xrd_sf", "xrd_sf", "json")

    def test_xrd_sf_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.xrd_sf", "xrd_sf", "yaml")

    def test_phonon_dos_json(self):
        self._test_dump(_TEST_FOLDER / "test.phonon_dos", "phonon_dos", "json")

    def test_phonon_dos_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.phonon_dos", "phonon_dos", "yaml")

    def test_efield_json(self):
        self._test_dump(_TEST_FOLDER / "test.efield", "efield", "json")

    def test_efield_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.efield", "efield", "yaml")

    def test_magres_json(self):
        self._test_dump(_TEST_FOLDER / "test.magres", "magres", "json")

    def test_magres_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.magres", "magres", "yaml")

    def test_tddft_json(self):
        self._test_dump(_TEST_FOLDER / "test.tddft", "tddft", "json")

    def test_tddft_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.tddft", "tddft", "yaml")

    def test_err_json(self):
        self._test_dump(_TEST_FOLDER / "test.err", "err", "json")

    def test_err_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.err", "err", "yaml")

    def test_phonon_json(self):
        self._test_dump(_TEST_FOLDER / "test.phonon", "phonon", "json")

    def test_phonon_yaml(self):
        self._test_dump(_TEST_FOLDER / "test.phonon", "phonon", "yaml") 

if __name__ == '__main__':
    unittest.main()
