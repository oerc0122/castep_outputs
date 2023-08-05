"""
Run main castep parser
"""
from typing import Callable, Optional, TextIO, Union
from pathlib import Path
import logging
import fileinput
import io
import sys

from .args import (parse_args, args_to_dict)
from .utility import (json_safe, flatten_dict, get_dumpers)
from .castep_file_parser import parse_castep_file
from .cell_param_file_parser import parse_cell_param_file
from .md_geom_file_parser import parse_md_geom_file
from .extra_files_parser import (parse_bands_file, parse_hug_file, parse_phonon_dos_file,
                                 parse_efield_file, parse_xrd_sf_file, parse_elf_fmt_file,
                                 parse_chdiff_fmt_file, parse_pot_fmt_file, parse_den_fmt_file,
                                 parse_elastic_file, parse_ts_file)
from .constants import OutFormats

PARSERS = {
    ".castep": parse_castep_file,
    ".cell": parse_cell_param_file,
    ".param": parse_cell_param_file,
    ".geom": parse_md_geom_file,
    ".md": parse_md_geom_file,
    ".bands": parse_bands_file,
    ".hug": parse_hug_file,
    ".phonon_dos": parse_phonon_dos_file,
    ".efield": parse_efield_file,
    ".xrd_sf": parse_xrd_sf_file,
    ".elf_fmt": parse_elf_fmt_file,
    ".chdiff_fmt": parse_chdiff_fmt_file,
    ".pot_fmt": parse_pot_fmt_file,
    ".den_fmt": parse_den_fmt_file,
    ".elastic": parse_elastic_file,
    ".ts": parse_ts_file
    }


def parse_single(in_file: Union[Path, TextIO], parser: Callable = None,
                 out_format: OutFormats = "print",
                 *, loglevel: int = logging.WARNING, testing: bool = False):
    """
    Parse a file using the given parser and post-process according to options
    """

    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    if not isinstance(in_file, (io.TextIOBase, Path)):
        in_file = Path(in_file)

    if parser is None:
        ext = in_file.suffix

        if ext not in PARSERS:
            raise KeyError(f"Parser for file {in_file} (assumed type: {ext}) not found")

        parser = PARSERS[ext]

    if isinstance(in_file, io.TextIOBase):
        data = parser(in_file)
    else:
        with fileinput.FileInput(in_file, mode='r', encoding='utf-8') as file:
            data = parser(file)

    if out_format == "json" or testing:
        data = json_safe(data)

    if testing:
        if isinstance(data, list):
            data = [flatten_dict(run) for run in data]
        else:
            data = flatten_dict(data)

    return data


def parse_all(output: Optional[Path] = None, out_format: OutFormats = "json",
              *, loglevel: int = logging.WARNING, testing: bool = False, **files):
    """ Parse all files in files dict """
    file_dumper = get_dumpers(out_format)

    for typ, paths in files.items():
        parser = PARSERS[f".{typ}"]
        for path in paths:
            data = parse_single(path, parser, out_format, loglevel=loglevel, testing=testing)

            if output is None:
                file_dumper(data, sys.stdout)
                print()
            elif isinstance(output, io.TextIOBase):
                file_dumper(data, output)
            else:
                with open(output, 'a+', encoding='utf-8') as out_file:
                    file_dumper(data, out_file)


def main():
    """ Run the main program from command line """
    args = parse_args()
    dict_args = args_to_dict(args)

    parse_all(output=args.output,
              loglevel=getattr(logging, args.log.upper()),
              testing=args.testing,
              out_format=args.out_format,
              **dict_args)


if __name__ == "__main__":
    main()
