# pylint: disable=import-error
"""
Convert .castep, .md or .geom to ASE atoms objects or dump to file
"""

import argparse
import sys
from pathlib import Path
from typing import Literal, Tuple

from ase import Atoms
from ase.io import write
from ase.io.formats import ioformats

from .. import (parse_single, parse_md_geom_file, parse_castep_file)


_PARSERS = {"castep": parse_castep_file,
            "md": parse_md_geom_file,
            "geom": parse_md_geom_file}


def _parse_args() -> argparse.Namespace:
    """Parse CLI Arguments"""
    arg_parser = argparse.ArgumentParser(
        prog="castep2ase",
        description="Simple .castep, .md, .geom to ASE format tool")

    arg_parser.add_argument("file", help="Source file to convert", type=Path)
    arg_parser.add_argument("-o", "--output",
                            help="Output file to write", type=Path, default=sys.stdout)
    arg_parser.add_argument("-f", "--in-format", help="Parse FILE as this type",
                            choices=_PARSERS.keys())
    arg_parser.add_argument("-F", "--out-format", help="Dump through ASE as this type",
                            choices=[key for key, val in ioformats.items() if val.can_write])
    return arg_parser.parse_args()


def _get_md_geom_struct(parsed: dict) -> Atoms:
    """Construct atoms from .md or .geom"""
    atoms = Atoms(symbols=[symbol for symbol, ind in parsed["R"].keys()],
                  positions=list(parsed["R"].values()),
                  velocities=list(parsed["V"].values()) if "V" in parsed else None,
                  cell=parsed["lattice_vectors"],
                  pbc=True,
                  )

    return atoms


def _get_castep_struct(parsed: dict) -> Tuple[str, Atoms]:
    """Construct atoms from .castep"""
    atoms: Atoms

    if "geom_opt" in parsed:
        source = "Geometry Optimisation"
        if "final_configuration" not in parsed["geom_opt"]:
            raise KeyError("Cannot find final configuration, "
                           "are you sure your geom opt ran to completion?")

        data = parsed["geom_opt"]["final_configuration"]

        atoms = Atoms(symbols=[symbol for symbol, ind in parsed["initial_positions"].keys()],
                      positions=(list(data["atoms"].values())
                                 if "atoms" in data else
                                 list(parsed["initial_positions"].values())),
                      cell=(data["cell"]["real_lattice"]
                            if "cell" in data else
                            parsed["initial_cell"]["real_lattice"]),
                      pbc=True,
                      )

    elif "md" in parsed and "positions" in parsed["md"]:
        source = "Molecular Dynamics"
        data = parsed["md"][-1]

        atoms = Atoms(symbols=[symbol for symbol, ind in data["positions"].keys()],
                      positions=list(data["positions"].values()),
                      cell=(data["cell"]["real_lattice"]
                            if "cell" in data else
                            parsed["initial_cell"]["real_lattice"]),
                      pbc=True,
                      )

    else:
        source = "Initial positions"

        atoms = Atoms(symbols=[symbol for symbol, ind in parsed["initial_positions"].keys()],
                      positions=list(parsed["initial_positions"].values()),
                      cell=parsed["initial_cell"]["real_lattice"],
                      velocities=(list(parsed["initial_velocities"].values())
                                  if "initial_velocities" in parsed else None),
                      pbc=True,
                      )

    return atoms, source


def castep2ase(source: Path, source_format: Literal["geom", "md", "castep", None] = None) -> Atoms:
    """Convert a CASTEP output file into an ASE atoms object"""

    fmt = source_format if source_format else source.suffix[1:]
    if fmt not in _PARSERS:
        raise IOError(f"Do not know how to parse '{fmt}' file.")

    # We always want the last data
    parsed = parse_single(source, parser=_PARSERS[fmt])[-1]

    if fmt in ("geom", "md"):
        atoms = _get_md_geom_struct(parsed)
    elif fmt in ("castep",):
        atoms, _ = _get_castep_struct(parsed)

    return atoms


def _main():
    """Convert a CASTEP output file into an ASE atoms object"""
    args = _parse_args()

    file = args.file
    if not file.exists():
        raise FileNotFoundError(f"File {file} not found.")

    fmt = args.in_format if args.in_format else None
    atoms = castep2ase(file, fmt)

    write(args.output, atoms, args.out_format)


if __name__ == "__main__":
    _main()
