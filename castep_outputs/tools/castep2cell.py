"""
Convert .castep, .md or .geom to castep cell files
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from . import parse_castep_file, parse_md_geom_file, parse_single


PARSERS = {"castep": parse_castep_file,
           "md": parse_md_geom_file,
           "geom": parse_md_geom_file}


def parse_args():
    """Parse CLI arguments"""
    arg_parser = argparse.ArgumentParser(
        prog="castep2cell",
        description="Simple .castep, .md, .geom to .cell tool")

    arg_parser.add_argument("file", help="Source file to convert", type=Path)
    arg_parser.add_argument("-o", "--output", help="File to dump to, default: screen",
                            default=None)
    arg_parser.add_argument("-f", "--format", help="Parse FILE as this type",
                            choices=PARSERS.keys())

    return arg_parser.parse_args()


def atreg_to_list(dict_in: dict, subelem: Optional[str] = None):
    """Transform an atreg block to a list"""
    if subelem is not None:
        return [(*atom, *pos[subelem])
                for atom, pos in dict_in.items()
                if isinstance(atom, tuple)]

    return [(*atom, *pos)
            for atom, pos in dict_in.items()
            if isinstance(atom, tuple)]


def get_md_geom_struct(parsed: dict):
    """Get structure from a parsed .md or .geom file"""
    accum = {}
    accum["positions_abs"] = atreg_to_list(parsed, "R")
    if "V" in parsed:
        accum["ionic_velocities"] = list(parsed["V"].values())
    accum["lattice_cart"] = parsed["lattice_vectors"]

    return accum


def get_castep_struct(parsed: dict):
    """Get structure from a parsed .castep file"""

    accum = {}

    if "geom_opt" in parsed:
        source = "Geometry Optimisation"
        if "final_configuration" not in parsed["geom_opt"]:
            raise KeyError("Cannot find final configuration, "
                           "are you sure your geom opt ran to completion?")

        data = parsed["geom_opt"]["final_configuration"]
        if "atoms" in data:
            accum["positions_abs"] = atreg_to_list(data["atoms"])
        else:
            accum["positions_abs"] = atreg_to_list(parsed["initial_positions"])

        if "cell" in data:
            accum["lattice_cart"] = data["cell"]["real_lattice"]
        else:
            accum["lattice_cart"] = parsed["initial_cell"]["real_lattice"]

    elif "md" in parsed:
        source = "Molecular Dynamics"
        data = parsed["md"][-1]

        accum["positions_abs"] = atreg_to_list(data["positions"])

        if "cell" in data:
            accum["lattice_cart"] = data["cell"]["real_lattice"]
        else:
            accum["lattice_cart"] = parsed["initial_cell"]["real_lattice"]

    else:
        source = "Initial positions"
        accum["positions_abs"] = atreg_to_list(parsed["initial_positions"])
        if "initial_velocities" in parsed:
            accum["ionic_velocities"] = list(parsed["initial_velocities"].values())
        accum["lattice_cart"] = parsed["initial_cell"]["real_lattice"]

    return accum, source


def file_dumper(file: Path, data: dict, source_file: str, source: Optional[str] = None):
    """Dump file in .cell format to file path """
    if file is sys.stdout:
        def dump(*args, **kwargs):
            print(*args, **kwargs)

    else:
        out_file = file.open('w', encoding="utf-8")

        def dump(*args, **kwargs):
            print(*args, **kwargs, file=out_file)

    def dump_block(data, key):
        if key not in data:
            return

        dump(f"%block {key}")
        for row in data[key]:
            dump("\t".join(map(str, row)))
        dump(f"%endblock {key}")
        dump()

    dump("# cell file generated by castep2cell.py")
    if source is not None:
        dump(f"# Generated from {source} calculation from {source_file}")
    else:
        dump(f"# Generated from {source_file}")
    dump()

    for key in data:
        dump_block(data, key)

    if file is not sys.stdout:
        out_file.close()


def main():
    """Parse file and dump as castep .cell format"""
    args = parse_args()

    file = args.file
    if not file.exists():
        raise FileNotFoundError(f"File {file} not found.")

    fmt = args.format if args.format else args.file.suffix[1:]
    if fmt not in PARSERS:
        raise IOError(f"Do not know how to parse '{fmt}' file.")

    output = args.output if args.output else sys.stdout

    # We always want the last data
    parsed = parse_single(file, parser=PARSERS[fmt])[-1]

    source = None
    if fmt in ("geom", "md"):
        accum = get_md_geom_struct(parsed)
    elif fmt in ("castep",):
        accum, source = get_castep_struct(parsed)

    file_dumper(output, accum, file, source)


if __name__ == "__main__":
    main()
