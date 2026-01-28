"""List of parsers for binary file formats."""
from __future__ import annotations

from collections.abc import Callable

from .cst_esp_file_parser import parse_cst_esp_file
from .elnes_bin_parser import parse_elnes_bin_file
from .epme_bin_parser import parse_epme_bin_file

#: Dictionary of available parsers.
PARSERS: dict[str, Callable] = {
    "cst_esp": parse_cst_esp_file,
    "epme_bin": parse_epme_bin_file,
    "elnes_bin": parse_elnes_bin_file,
}

#: Names of parsers/parsable file extensions (without ``"."``).
CASTEP_OUTPUT_NAMES: tuple[str, ...] = tuple(PARSERS.keys())

#: Names of parsable file extensions.
CASTEP_FILE_FORMATS: tuple[str, ...] = tuple(f".{typ}" for typ in CASTEP_OUTPUT_NAMES)
