"""
Parse the following castep outputs:
.elf_fmt
.chdiff_fmt
.pot_fmt
.den_fmt
"""
from typing import TextIO, Dict, Union, List

from .parse_utilities import parse_kpt_info


def parse_elf_fmt_file(elf_file: TextIO) -> Dict[str, List[Union[int, float]]]:
    """ Parse castep .elf_fmt files """
    return parse_kpt_info(elf_file, ('chi_alpha', 'chi_beta'))


def parse_chdiff_fmt_file(chdiff_file: TextIO) -> Dict[str, List[Union[int, float]]]:
    """ Parse castep .chdiff_fmt files """
    return parse_kpt_info(chdiff_file, 'chdiff')


def parse_pot_fmt_file(pot_file: TextIO) -> Dict[str, List[Union[int, float]]]:
    """ Parse castep .pot_fmt files """
    return parse_kpt_info(pot_file, 'pot')


def parse_den_fmt_file(den_file: TextIO) -> Dict[str, List[Union[int, float]]]:
    """ Parse castep .den_fmt files """
    return parse_kpt_info(den_file, 'density')
