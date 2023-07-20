"""
Run main castep parser
"""

import sys

from .args import (parse_args, args_to_dict)
from .utility import (json_safe_dict, flatten_dict, get_dumpers)
from .parse_castep_file import parse_castep_file
from .parse_cell_param_file import parse_cell_param_file
from .parse_md_geom_file import parse_md_geom_file
from .parse_extra_files import (parse_bands_file, parse_hug_file, parse_phonon_dos_file,
                                parse_efield_file, parse_xrd_sf_file, parse_elf_fmt_file,
                                parse_chdiff_fmt_file, parse_pot_fmt_file, parse_den_fmt_file)


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
    ".den_fmt": parse_den_fmt_file
    }


def parse_single(types: list[str], parser: callable):
    """
    Use a single parser to parse a some classes of files and print to screen
    """
    args = parse_args()
    file_dumper = get_dumpers(args.out_format)

    files = {file for typ in types for file in getattr(args, typ, [])}
    # Handle cases where seedname passed but not as appropriate arg type for
    files |= {arg for arg in args.seedname if os.path.isfile(arg) and arg not in files}

    for seed in files:
        with open(seed, "r", encoding="utf-8") as in_file:
            data = parser(in_file, verbose=True)

        if args.out_format == "json" or args.testing:
            data = [json_safe_dict(run) for run in data]

        if args.testing:
            data = [flatten_dict(run) for run in data]

        file_dumper(data, sys.stdout)


def parse_all(output=None, verbose=False, testing=False, out_format="json", **files):
    """ Parse all files in files dict """
    file_dumper = get_dumpers(out_format)

    for typ, paths in files.items():
        parser = PARSERS[f".{typ}"]
        for path in paths:
            with open(path, 'r', encoding='utf-8') as in_file:
                data = parser(in_file, verbose)

            if out_format == "json" or testing:
                data = [json_safe_dict(run) for run in data]

            if testing:
                data = [flatten_dict(run) for run in data]

            if output is None:
                file_dumper(data, sys.stdout)
            else:
                with open(output, 'a+', encoding='utf-8') as out_file:
                    file_dumper(data, out_file)


def main():
    """ Run the main program from command line """
    args = parse_args()
    dict_args = args_to_dict(args)

    parse_all(output=args.output,
              verbose=args.verbose,
              testing=args.testing,
              out_format=args.out_format,
              **dict_args)


if __name__ == "__main__":
    main()
