#!/usr/bin/env python3

"""Generate testing benchmark files for dumpers."""

from __future__ import annotations

import pathlib
from argparse import REMAINDER, ArgumentParser
from collections.abc import Sequence

from castep_outputs.cli.castep_outputs_main import parse_all

ALL_SETS = (
    "castep",
    "bands",
    "cell",
    "param",
    "elastic",
    "md",
    "ts",
    "efield",
    "cst_esp",
    "den_fmt",
    "chdiff_fmt",
    "pot_fmt",
    "elf_fmt",
    "xrd_sf",
    "phonon",
    "phonon_dos",
    "magres",
    "efield",
    "tddft",
    "err",
    "pes",
    "epme",
    ("pp-md", "castep"),
    ("si8-md", "castep"),
)


def gen_data(
    types: Sequence[tuple[str | tuple[str, str]]] = ALL_SETS,
    fmts: tuple[str] = ("json", "pyyaml", "ruamel"),
) -> None:
    """Generate benchmark data."""
    for type_ in types:
        for fmt in fmts:
            print(type_, fmt)
            if isinstance(type_, tuple):
                name, typ = type_
                in_name = name
            else:
                name = typ = type_
                in_name = "test"

            # Delete existing
            pth = pathlib.Path(f"{name}.{fmt}")
            pth.unlink(missing_ok=True)
            parse_all(output=str(pth), out_format=fmt, **{typ: [f"{in_name}.{typ}"]})


if __name__ == "__main__":
    argp = ArgumentParser(prog="gen_data", description="Generate test data.")

    argp.add_argument("datasets", nargs=REMAINDER, help="Sets to generate.", default=ALL_SETS)
    argp.add_argument(
        "--formats",
        nargs="+",
        help="Formats to generate.",
        default=("json", "pyyaml", "ruamel"),
    )
    args = argp.parse_args()

    gen_data(args.datasets, args.formats)
