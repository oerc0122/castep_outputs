"""
Argument parser
"""
from typing import Sequence, Dict, List
import os.path
import argparse
# pylint: disable=line-too-long

from .utility import SUPPORTED_FORMATS
from .constants import CASTEP_OUTPUT_NAMES, CASTEP_FILE_FORMATS

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
AP.add_argument("-c", "--inc-castep", action="store_true", help="Extract .castep information")
AP.add_argument("-g", "--inc-geom", action="store_true", help="Extract .geom information")
AP.add_argument("-m", "--inc-md", action="store_true", help="Extract .md information")
AP.add_argument("-b", "--inc-bands", action="store_true", help="Extract .bands information")
AP.add_argument("-p", "--inc-phonon_dos", action="store_true", help="Extract .phonon_dos information")
AP.add_argument("-e", "--inc-efield", action="store_true", help="Extract .efield information")
AP.add_argument("-x", "--inc-xrd_sf", action="store_true", help="Extract .xrd_sf information")
AP.add_argument("-H", "--inc-hug", action="store_true", help="Extract .hug information")
AP.add_argument("-E", "--inc-elf_fmt", action="store_true", help="Extract .elf_fmt information")
AP.add_argument("-C", "--inc-chdiff_fmt", action="store_true", help="Extract .chdiff_fmt information")
AP.add_argument("-P", "--inc-pot_fmt", action="store_true", help="Extract .pot_fmt information")
AP.add_argument("-D", "--inc-den_fmt", action="store_true", help="Extract .den_fmt information")
AP.add_argument("-X", "--inc-elastic", action="store_true", help="Extract .elastic information")
AP.add_argument("-T", "--inc-ts", action="store_true", help="Extract .ts information")

AP.add_argument('--inc-param', action="store_true", help="Extract .param information")
AP.add_argument('--inc-cell', action="store_true", help="Extract .cell information")

AP.add_argument("--castep", nargs="*", help="Extract from CASTEP as .castep type", default=[])
AP.add_argument("--geom", nargs="*", help="Extract from GEOM as .geom type", default=[])
AP.add_argument("--cell", nargs="*", help="Extract from CELL as .cell type", default=[])
AP.add_argument("--param", nargs="*", help="Extract from PARAM as .param type", default=[])
AP.add_argument("--md", nargs="*", help="Extract from MD as .md type", default=[])
AP.add_argument("--bands", nargs="*", help="Extract from BANDS as .bands type", default=[])
AP.add_argument("--hug", nargs="*", help="Extract from HUG as .hug type", default=[])
AP.add_argument("--phonon_dos", nargs="*", help="Extract from PHONON_DOS as .phonon_dos type", default=[])
AP.add_argument("--efield", nargs="*", help="Extract from EFIELD as .efield type", default=[])
AP.add_argument("--xrd_sf", nargs="*", help="Extract from XRD_SF as .xrd_sf type", default=[])
AP.add_argument("--elf_fmt", nargs="*", help="Extract from ELF_FMT as .elf_fmt type", default=[])
AP.add_argument("--chdiff_fmt", nargs="*", help="Extract from CHDIFF_FMT as .chdiff_fmt type", default=[])
AP.add_argument("--pot_fmt", nargs="*", help="Extract from POT_FMT as .pot_fmt type", default=[])
AP.add_argument("--den_fmt", nargs="*", help="Extract from DEN_FMT as .den_fmt type", default=[])
AP.add_argument("--elastic", nargs="*", help="Extract from ELASTIC as .elastic type", default=[])
AP.add_argument("--ts", nargs="*", help="Extract from TS as .ts type", default=[])


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
        if os.path.isfile(seed) and (ext := os.path.splitext(seed)[1][1:]) in CASTEP_OUTPUT_NAMES:
            getattr(args, ext).append(seed)
        else:
            for typ in CASTEP_OUTPUT_NAMES:
                if getattr(args, f"inc_{typ}") and os.path.isfile(seed+typ):
                    getattr(args, typ).append(seed+typ)

    return args


def args_to_dict(args: argparse.Namespace) -> Dict[str, List[str]]:
    """ Convert args namespace to dictionary """
    out_dict = {typ: getattr(args, typ) for typ in CASTEP_OUTPUT_NAMES}
    return out_dict
