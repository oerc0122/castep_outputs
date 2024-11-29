"""List of parsers for file formats."""
from __future__ import annotations

from collections.abc import Callable

from .bands_file_parser import parse_bands_file
from .castep_file_parser import parse_castep_file
from .cell_param_file_parser import parse_cell_param_file
from .efield_file_parser import parse_efield_file
from .elastic_file_parser import parse_elastic_file
from .err_file_parser import parse_err_file
from .hug_file_parser import parse_hug_file
from .magres_file_parser import parse_magres_file
from .md_geom_file_parser import parse_md_geom_file
from .parse_fmt_files import (
                              parse_chdiff_fmt_file,
                              parse_den_fmt_file,
                              parse_elf_fmt_file,
                              parse_pot_fmt_file,
)
from .phonon_dos_file_parser import parse_phonon_dos_file
from .phonon_file_parser import parse_phonon_file
from .tddft_file_parser import parse_tddft_file
from .ts_file_parser import parse_ts_file
from .xrd_sf_file_parser import parse_xrd_sf_file

__all__ = [
    "parse_bands_file",
    "parse_castep_file",
    "parse_cell_param_file",
    "parse_cell_param_file",
    "parse_chdiff_fmt_file",
    "parse_den_fmt_file",
    "parse_efield_file",
    "parse_elastic_file",
    "parse_elf_fmt_file",
    "parse_err_file",
    "parse_hug_file",
    "parse_magres_file",
    "parse_md_geom_file",
    "parse_md_geom_file",
    "parse_phonon_dos_file",
    "parse_phonon_file",
    "parse_pot_fmt_file",
    "parse_tddft_file",
    "parse_ts_file",
    "parse_xrd_sf_file",
]


#: Dictionary of available parsers.
PARSERS: dict[str, Callable] = {
    "castep": parse_castep_file,
    "cell": parse_cell_param_file,
    "param": parse_cell_param_file,
    "geom": parse_md_geom_file,
    "md": parse_md_geom_file,
    "bands": parse_bands_file,
    "hug": parse_hug_file,
    "phonon_dos": parse_phonon_dos_file,
    "efield": parse_efield_file,
    "xrd_sf": parse_xrd_sf_file,
    "elf_fmt": parse_elf_fmt_file,
    "chdiff_fmt": parse_chdiff_fmt_file,
    "pot_fmt": parse_pot_fmt_file,
    "den_fmt": parse_den_fmt_file,
    "elastic": parse_elastic_file,
    "ts": parse_ts_file,
    "magres": parse_magres_file,
    "tddft": parse_tddft_file,
    "err": parse_err_file,
    "phonon": parse_phonon_file,
    }

#: Names of parsers/parsable file extensions (without ``"."``).
CASTEP_OUTPUT_NAMES: tuple[str, ...] = tuple(PARSERS.keys())

#: Names of parsable file extensions.
CASTEP_FILE_FORMATS: tuple[str, ...] = tuple(f".{typ}" for typ in CASTEP_OUTPUT_NAMES)
