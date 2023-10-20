"""
Module to parse miscellaneous castep files
"""

__AUTHOR__ = "Jacob Wilkins"
__VERSION__ = "0.1.6"

# pylint: disable=unused-import

from .castep_outputs_main import parse_single
from .castep_file_parser import parse_castep_file
from .cell_param_file_parser import parse_cell_param_file, parse_cell_file, parse_param_file
from .md_geom_file_parser import parse_md_geom_file, parse_md_file, parse_geom_file
from .extra_files_parser import (parse_bands_file, parse_hug_file, parse_phonon_dos_file,
                                 parse_efield_file, parse_xrd_sf_file, parse_elf_fmt_file,
                                 parse_chdiff_fmt_file, parse_pot_fmt_file, parse_den_fmt_file,
                                 parse_elastic_file, parse_ts_file)
