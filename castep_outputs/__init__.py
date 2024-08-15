"""
Module to parse miscellaneous castep files
"""

__author__ = "Jacob Wilkins"
__version__ = "0.1.7"

# pylint: disable=unused-import

from .parsers import *  # noqa: F403
from .cli.castep_outputs_main import parse_single  # noqa: F401
