from collections.abc import Iterable, Mapping
from typing import TextIO

from castep_outputs.parsers.cell_param_file_parser import CellParamData
from castep_outputs.utilities.utility import file_or_path


@file_or_path(mode="w")
def _write_input(output: TextIO, param: CellParamData) -> None:
    """Dump a cell/param file to output.

    Parameters
    ----------
    output : TextIO
        Output file.
    param : CellParamData
        Parameters to write.
    """

    def write(*args, **kwargs) -> None:
        print(*args, **kwargs, file=output)

    for key, val in param.items():
        if key in _DUMPERS:
            _DUMPERS[key](output, val)

        match val:
            case Mapping():
                print("Map:", key, val)
                write(f"%block {key}")
                for _key, _val in val.items():
                    if isinstance(_val, Iterable):
                        write(_key, *_val)
                        continue
                    write(_key, _val)
                write(f"%endblock {key}")
            case (_val, unit):
                print("_:", key, val)
                write(f"{key}: {_val} {unit}")
            case str():
                print("_:", key, val)
                write(f"{key}: {val}")
            case Iterable():
                print("It:", key, val)
                write(f"%block {key}")
                for _val in val:
                    if isinstance(_val, Iterable):
                        write(_key, *_val)
                        continue
                    write(_key, _val)
                write(f"%endblock {key}")
            case _:
                print("_:", key, val)
                write(f"{key}: {val}")


def _dump_devel_code(output: TextIO)

_DUMPERS = {"devel_code": _dump_devel_code}


write_cell_file = _write_input
write_param_file = _write_input
