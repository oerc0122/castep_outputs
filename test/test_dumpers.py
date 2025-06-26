"""Test dumping works correcly."""

import io
import json
from functools import partial
from pathlib import Path

import pytest

from castep_outputs.cli.castep_outputs_main import parse_all, parse_single
from castep_outputs.utilities.utility import normalise

_DATA_FOLDER = Path(__file__).parent / "data_files"

def _to_complex(complx):
    if (isinstance(complx, dict) and not complx.keys() ^ {"real", "imag"}):
        return complex(**complx)
    return complx

@pytest.mark.parametrize("file,typ,ref", [
    ("test.cell", "cell", "cell"),
    ("test.param", "param", "param"),
    ("test.castep", "castep", "castep"),
    ("pp-md.castep", "castep", "pp-md"),
    ("si8-md.castep", "castep", "si8-md"),
    ("test.bands", "bands", "bands"),
    ("test.md", "md", "md"),
    ("test.elastic", "elastic", "elastic"),
    ("test.ts", "ts", "ts"),
    ("test.chdiff_fmt", "chdiff_fmt", "chdiff_fmt"),
    ("test.den_fmt", "den_fmt", "den_fmt"),
    ("test.pot_fmt", "pot_fmt", "pot_fmt"),
    ("test.elf_fmt", "elf_fmt", "elf_fmt"),
    ("test.xrd_sf", "xrd_sf", "xrd_sf"),
    ("test.phonon_dos", "phonon_dos", "phonon_dos"),
    ("test.efield", "efield", "efield"),
    ("test.magres", "magres", "magres"),
    ("test.tddft", "tddft", "tddft"),
    ("test.err", "err", "err"),
    ("test.phonon", "phonon", "phonon"),
    ("test.cst_esp", "cst_esp", "cst_esp"),
    ("test.epme", "epme", "epme"),
])
@pytest.mark.parametrize("out_format", ("json", "ruamel", "pyyaml"))
def test_dump(file, typ, ref, out_format):
    """Test dumpers work correctly."""
    # Get loaders
    if out_format == "json":
        loader = json.load
    elif out_format == "ruamel":
        module = pytest.importorskip("ruamel.yaml")
        yaml_eng = module.YAML(typ="unsafe")
        loader = yaml_eng.load
    elif out_format == "pyyaml":
        module = pytest.importorskip("yaml")
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader

        loader = partial(module.load, Loader=Loader)

    file = _DATA_FOLDER / file

    # Load reference data
    ref_file = _DATA_FOLDER / f"{ref}.{out_format}"
    with ref_file.open(encoding="utf-8") as test_file:
        ref_dict = loader(test_file)
    ref_dict = normalise(ref_dict, {dict: _to_complex})

    # Check produced data files identical
    test = io.StringIO()
    parse_all(test, out_format=out_format, **{typ: [file]})
    test.seek(0)

    comp_dict = loader(test)
    comp_dict = normalise(comp_dict, {dict: _to_complex})
    assert comp_dict == ref_dict

    # Check parse_single (i.e. wrapper) gives same result as specific loader
    comp_dict = parse_single(file, out_format=out_format)
    comp_dict = normalise(comp_dict, {dict: _to_complex})

    assert comp_dict == ref_dict


if __name__ == "__main__":
    pytest.main()
