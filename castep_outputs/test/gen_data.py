# pylint: skip-file
import pathlib

from castep_outputs.cli.castep_outputs_main import parse_all

for type_ in ('castep', 'bands', 'cell', 'param', 'elastic', 'md', 'ts', 'efield',
              'den_fmt', 'chdiff_fmt', 'pot_fmt', 'elf_fmt', 'xrd_sf', 'phonon_dos',
              'magres', 'efield', 'tddft', 'err', ('pp-md', 'castep')):
    for fmt in ('json', 'yaml'):
        print(type_, fmt)
        if isinstance(type_, tuple):
            name, typ = type_
            in_name = name
        else:
            name = typ = type_
            in_name = "test"

        # Delete existing
        pth = pathlib.Path(f"{name}.{fmt}")
        if pth.exists():
            pth.unlink()
        parse_all(output=str(pth), out_format=fmt, **{typ: [f"{in_name}.{typ}"]})
