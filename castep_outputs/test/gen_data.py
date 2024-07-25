# pylint: skip-file
import pathlib

from castep_outputs.cli.castep_outputs_main import parse_all

for typ in ('castep', 'bands', 'cell', 'param', 'elastic', 'md', 'ts', 'efield',
            'den_fmt', 'chdiff_fmt', 'pot_fmt', 'elf_fmt', 'xrd_sf', 'phonon_dos',
            'magres', 'efield', 'tddft', 'err', 'phonon'):
    for fmt in ('json', 'yaml'):
        print(typ, fmt)
        # Delete existing
        pth = pathlib.Path(f"{typ}.{fmt}")
        if pth.exists():
            pth.unlink()
        parse_all(output=str(pth), out_format=fmt, **{typ: [f"test.{typ}"]})
