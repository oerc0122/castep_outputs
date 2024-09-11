"""Parse castep .elf_fmt, .chdiff_fmt, .pot_fmt, and .den_fmt files."""
from __future__ import annotations

from typing import TextIO

from .parse_utilities import parse_kpt_info


def parse_elf_fmt_file(elf_file: TextIO) -> dict[str, list[int | float]]:
    """Parse castep .elf_fmt files."""
    return parse_kpt_info(elf_file, ("chi_alpha", "chi_beta"))


def parse_chdiff_fmt_file(chdiff_file: TextIO) -> dict[str, list[int | float]]:
    """Parse castep .chdiff_fmt files."""
    return parse_kpt_info(chdiff_file, "chdiff")


def parse_pot_fmt_file(pot_file: TextIO) -> dict[str, list[int | float]]:
    """Parse castep .pot_fmt files."""
    return parse_kpt_info(pot_file, "pot")


def parse_den_fmt_file(den_file: TextIO) -> dict[str, list[int | float]]:
    """Parse castep .den_fmt files."""
    return parse_kpt_info(den_file, "density")
