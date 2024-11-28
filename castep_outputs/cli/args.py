"""Module containing argument parser and processing."""
from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from castep_outputs.parsers import CASTEP_FILE_FORMATS, CASTEP_OUTPUT_NAMES
from castep_outputs.utilities.dumpers import SUPPORTED_FORMATS

# pylint: disable=line-too-long


#: Main argument parser for castep outputs.
ARG_PARSER = argparse.ArgumentParser(
    prog="castep_outputs",
    description=f"""Attempts to find all files for seedname, filtered by `inc` args (default: all).
    Explicit files can be passed using longname arguments.
    castep_outputs can parse most castep outputs including: {', '.join(CASTEP_FILE_FORMATS)}""",
)

ARG_PARSER.add_argument("seedname", nargs=argparse.REMAINDER, help="Seed name for data")
ARG_PARSER.add_argument("-V", "--version", action="version", version="%(prog)s v0.1")
ARG_PARSER.add_argument("-L", "--log", help="Verbose output",
                        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
                        default="WARNING")
ARG_PARSER.add_argument("-o", "--output", help="File to write output, default: screen",
                        default=None)
ARG_PARSER.add_argument("-f", "--out-format", help="Output format", choices=SUPPORTED_FORMATS,
                        default="json")

ARG_PARSER.add_argument("-t", "--testing", action="store_true",
                        help="Set testing mode to produce flat outputs")

ARG_PARSER.add_argument("-A", "--inc-all", action="store_true",
                        help="Extract all available information")

for output_name in CASTEP_OUTPUT_NAMES:
    ARG_PARSER.add_argument(f"--inc-{output_name}", action="store_true",
                            help=f"Extract .{output_name} information")

for output_name in CASTEP_OUTPUT_NAMES:
    ARG_PARSER.add_argument(f"--{output_name}", nargs="*",
                            help=f"Extract from {output_name.upper()} as .{output_name} type",
                            default=[])


def parse_args(to_parse: Sequence[str] = ()) -> argparse.Namespace:
    """
    Parse all arguments and add those caught by flags.

    Parameters
    ----------
    to_parse
        Arguments to handle in this call.

    Returns
    -------
    argparse.Namespace
        Parsed args.

    Examples
    --------
    parse_args()
    """
    args = ARG_PARSER.parse_args()

    parse_all = args.inc_all or not any(getattr(args, f"inc_{typ}") for typ in CASTEP_OUTPUT_NAMES)

    # Set all flags
    if parse_all and not to_parse:
        for typ in CASTEP_OUTPUT_NAMES:
            setattr(args, f"inc_{typ}", True)

    # Only parse those which are requested
    for typ in to_parse:
        setattr(args, f"inc_{typ}", True)

    # Add seeded files into parse list if to be included
    for seed in args.seedname:
        seed = Path(seed)
        if seed.is_file() and (ext := seed.suffix[1:]) in CASTEP_OUTPUT_NAMES:
            getattr(args, ext).append(str(seed))
        else:
            for typ in CASTEP_OUTPUT_NAMES:
                trial = seed.with_suffix(f".{typ}")
                if getattr(args, f"inc_{typ}") and trial.is_file():
                    getattr(args, typ).append(str(trial))

            if args.inc_err and (err_files := seed.parent.glob(f"{seed}.*.err")):
                args.err.extend(map(str, err_files))

    return args


def extract_parsables(args: argparse.Namespace) -> dict[str, list[str]]:
    """
    Extract the files to parse from the ``Namespace``.

    Parameters
    ----------
    args
        Namespace to process.

    Returns
    -------
    dict[str, list[str]]
        Files to parse.
    """
    return {typ: getattr(args, typ) for typ in CASTEP_OUTPUT_NAMES}
