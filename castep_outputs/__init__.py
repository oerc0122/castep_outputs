"""Module to parse miscellaneous castep files."""

__author__ = "Jacob Wilkins"
__version__ = "0.2.0"

# pylint: disable=unused-import

from .cli.castep_outputs_main import parse_single  # noqa: F401
from .parsers import *  # noqa: F403
