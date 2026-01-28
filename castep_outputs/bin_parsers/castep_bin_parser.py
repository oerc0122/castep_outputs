"""Parser for cst_esp files."""
from __future__ import annotations

from typing import BinaryIO, TypedDict

from ..utilities.utility import file_or_path, to_type
from .fortran_bin_parser import binary_file_reader
