# pylint: skip-file
from castep_outputs.castep_outputs_main import parse_all

for typ in ('castep', 'bands', 'cell', 'param'):
    for fmt in ('json', 'yaml'):
        print(typ, fmt)
        parse_all(output=f"{typ}.{fmt}", out_format=fmt, **{typ: [f"test.{typ}"]})
