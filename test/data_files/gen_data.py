#!/usr/bin/env python3

"""Generate testing benchmark files for dumpers."""

from __future__ import annotations

from pathlib import Path
from argparse import REMAINDER, ArgumentParser
from typing import TYPE_CHECKING, Literal

from castep_outputs.cli.castep_outputs_main import parse_all

if TYPE_CHECKING:
    from collections.abc import Iterable

    from castep_outputs.utilities.constants import OutFormats

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
    "epme",
    "epme_bin",
    "elnes_bin",
    ("pp-md", "castep"),
    ("si8-md", "castep"),
)

def gen_data(
    types: Iterable[str | tuple[str, str]] = ALL_SETS,
    fmts: tuple[OutFormats, ...] = ("json", "pyyaml", "ruamel"),
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
            pth = Path(f"{name}.{fmt}")
            pth.unlink(missing_ok=True)
            parse_all(output=str(pth), out_format=fmt, **{typ: [Path(f"{in_name}.{typ}")]})


if __name__ == "__main__":
    argp = ArgumentParser(prog="gen_data", description="Generate test data.")

    argp.add_argument("datasets", nargs=REMAINDER, help="Sets to generate.")
    argp.add_argument(
        "--formats",
        nargs="+",
        help="Formats to generate.",
        default=("json", "pyyaml", "ruamel"),
    )
    args = argp.parse_args()

    gen_data(args.datasets or ALL_SETS, args.formats)
