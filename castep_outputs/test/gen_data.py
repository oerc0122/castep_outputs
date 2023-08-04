# pylint: skip-file
import pathlib

from castep_outputs.castep_outputs_main import parse_all

for typ in ('castep', 'bands', 'cell', 'param', 'elastic', 'md'):
    for fmt in ('json', 'yaml'):
        print(typ, fmt)
        # Delete existing
        pth = pathlib.Path(f"{typ}.{fmt}")
        if pth.exists():
            pth.unlink()
        parse_all(output=str(pth), out_format=fmt, **{typ: [f"test.{typ}"]})
