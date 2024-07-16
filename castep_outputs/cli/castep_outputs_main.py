"""
Run main castep parser
"""
import io
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TextIO, Union

from .args import args_to_dict, parse_args
from ..parsers import PARSERS
from ..utilities.constants import OutFormats
from ..utilities.dumpers import get_dumpers
from ..utilities.utility import flatten_dict, json_safe, normalise


def parse_single(in_file: Union[str, Path, TextIO],
                 parser: Optional[Callable[[TextIO], List[Dict[str, Any]]]] = None,
                 out_format: OutFormats = "print",
                 *, loglevel: int = logging.WARNING, testing: bool = False):
    """
    Parse a file using the given parser and post-process according to options
    """

    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    if isinstance(in_file, str):
        in_file = Path(in_file)

    if parser is None and isinstance(in_file, Path):
        ext = in_file.suffix.strip(".")

        if ext not in PARSERS:
            raise KeyError(f"Parser for file {in_file} (assumed type: {ext}) not found")

        parser = PARSERS[ext]

    assert parser is not None

    if isinstance(in_file, io.TextIOBase):
        data = parser(in_file)
    elif isinstance(in_file, Path):
        with in_file.open(mode='r', encoding="utf-8") as file:
            data = parser(file)

    if out_format == "json" or testing:
        data = normalise(data, {dict: json_safe, complex: json_safe})
    elif out_format in ("yaml", "ruamel"):
        data = normalise(data, {tuple: list})

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

    data = {}
    for typ, paths in files.items():
        parser = PARSERS[typ]
        for path in paths:
            data[path] = parse_single(path, parser, out_format, loglevel=loglevel, testing=testing)

    if len(data) == 1:
        data = data.popitem()[1]

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
