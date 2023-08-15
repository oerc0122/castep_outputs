"""
Argument parser
"""
from typing import Sequence, Dict, List
from pathlib import Path
import argparse
# pylint: disable=line-too-long

from .utility import SUPPORTED_FORMATS
from .parsers import CASTEP_OUTPUT_NAMES, CASTEP_FILE_FORMATS

AP = argparse.ArgumentParser(
    prog="castep_outputs",
    description=f"""Attempts to find all files for seedname, filtered by `inc` args (default: all).
    Explicit files can be passed using longname arguments.
    castep_outputs can parse most human-readable castep outputs including: {', '.join(CASTEP_FILE_FORMATS)}"""
)

AP.add_argument("seedname", nargs=argparse.REMAINDER, help="Seed name for data")
AP.add_argument("-V", "--version", action="version", version="%(prog)s v0.1")
AP.add_argument("-L", "--log", help="Verbose output",
                choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'), default="WARNING")
AP.add_argument("-o", "--output", help="File to write output, default: screen", default=None)
AP.add_argument("-f", "--out-format", help="Output format", choices=SUPPORTED_FORMATS, default="json")

AP.add_argument("-t", "--testing", action="store_true", help="Set testing mode to produce flat outputs")

AP.add_argument("-A", "--inc-all", action="store_true", help="Extract all available information")

for output_name in CASTEP_OUTPUT_NAMES:
    AP.add_argument(f"--inc-{output_name}", action="store_true", help=f"Extract .{output_name} information")

for output_name in CASTEP_OUTPUT_NAMES:
    AP.add_argument(f"--{output_name}", nargs="*",
                    help=f"Extract from {output_name.upper()} as .{output_name} type", default=[])


def parse_args(to_parse: Sequence[str] = ()) -> argparse.Namespace:
    """ Parse all arguments and add those caught by flags """
    args = AP.parse_args()

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


def args_to_dict(args: argparse.Namespace) -> Dict[str, List[str]]:
    """ Convert args namespace to dictionary """
    out_dict = {typ: getattr(args, typ) for typ in CASTEP_OUTPUT_NAMES}
    return out_dict
