"""
Run main castep parser
"""
from typing import Callable, Optional, TextIO, Union
from pathlib import Path
import logging
import io
import sys

from .args import (parse_args, args_to_dict)
from .utility import (normalise, json_safe, flatten_dict, get_dumpers)
from .constants import OutFormats
from .parsers import PARSERS


def parse_single(in_file: Union[Path, TextIO], parser: Callable = None,
                 out_format: OutFormats = "print",
                 *, loglevel: int = logging.WARNING, testing: bool = False):
    """
    Parse a file using the given parser and post-process according to options
    """

    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    if not isinstance(in_file, (io.TextIOBase, Path)):
        in_file = Path(in_file)

    if parser is None:
        ext = in_file.suffix.strip(".")

        if ext not in PARSERS:
            raise KeyError(f"Parser for file {in_file} (assumed type: {ext}) not found")

        parser = PARSERS[ext]

    if isinstance(in_file, io.TextIOBase):
        data = parser(in_file)
    else:
        with open(in_file, mode='r', encoding="utf-8") as file:
            data = parser(file)

    if out_format == "json" or testing:
        data = normalise(data, {dict: json_safe, complex: json_safe})
    elif out_format in ("yaml", "ruamel"):
        data = normalise(data, {tuple: list})
    else:
        data = normalise(data)

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
