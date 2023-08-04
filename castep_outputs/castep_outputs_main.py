"""
Run main castep parser
"""
import logging
import fileinput
import io
import sys
import os.path

from .args import (parse_args, args_to_dict)
from .utility import (json_safe, flatten_dict, get_dumpers)
from .parse_castep_file import parse_castep_file
from .parse_cell_param_file import parse_cell_param_file
from .parse_md_geom_file import parse_md_geom_file
from .parse_extra_files import (parse_bands_file, parse_hug_file, parse_phonon_dos_file,
                                parse_efield_file, parse_xrd_sf_file, parse_elf_fmt_file,
                                parse_chdiff_fmt_file, parse_pot_fmt_file, parse_den_fmt_file,
                                parse_elastic_file, parse_ts_file)


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


def parse_single(in_file, parser: callable = None, out_format="json",
                 *, loglevel=logging.WARNING, testing=False):
    """
    Parse a file using the given parser and post-process according to options
    """

    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    if parser is None:
        _, ext = os.path.splitext(in_file)
        parser = PARSERS.get(ext, None)
        if not parser:
            raise KeyError(f"Parser for file {in_file} (assumed type: {ext}) not found")

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


def parse_all(output=None, out_format="json", loglevel=logging.WARNING, *, testing=False, **files):
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
