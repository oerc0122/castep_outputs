"""
Utility functions for parsing castep outputs.
"""

from __future__ import annotations

import collections.abc
import fileinput
import functools
import logging
import re
from collections import defaultdict
from collections.abc import Callable, Iterable, MutableMapping
from copy import copy
from typing import Any, TypeVar

import castep_outputs.utilities.castep_res as REs

from .filewrapper import FileWrapper

T = TypeVar("T")


def normalise_string(string: str) -> str:
    """
    Normalise a string.

    This includes:
    - Removing leading/trailing whitespace.
    - Making all spacing single-space.

    Parameters
    ----------
    string : str
        String to process.

    Returns
    -------
    str
        Normalised string.

    Examples
    --------
    >>> normalise_string(" Several   words  ")
    "Several words"
    """
    return " ".join(string.strip().split())


def normalise_key(string: str) -> str:
    """
    Normalise a dictionary key.

    This includes:
    - Removing all punctuation.
    - Lower-casing all.
    - Making all spacing single-underscore.

    Parameters
    ----------
    string : str
        String to process.

    Returns
    -------
    str
        Normalised string.

    Examples
    --------
    >>> normalise_key(" Several   words  ")
    "several_words"
    >>> normalise_key("A sentence.")
    "a_sentence"
    >>> normalise_key("I<3;;semi-colons;;!!!")
    "i_3_semi_colons"
    """
    return re.sub(r"[_\W]+", "_", string).strip("_").lower()


def atreg_to_index(dict_in: dict[str, str] | re.Match, *, clear: bool = True) -> tuple[str, int]:
    """
    Transform a matched atreg value to species index tuple.

    Optionally clear value from dictionary for easier processing.

    Parameters
    ----------
    dict_in : Union[Dict[str, str], re.Match]
        Atreg to process.
    clear : bool
        Whether to remove from incoming dictionary.

    Returns
    -------
    species : str
        Atomic species.
    ind : index
        Internal index.

    Examples
    --------
    >>> atreg_to_index({'x': 3.1, 'y': 2.1, 'z': 1.0, 'spec': "Ar", 'index': "1"})
    ("Ar", 1)
    """
    spec, ind = dict_in["spec"], dict_in["index"]

    if isinstance(dict_in, dict) and clear:
        del dict_in["spec"]
        del dict_in["index"]

    return (spec, int(ind))


def normalise(obj: Any, mapping: dict[type, type | Callable]) -> Any:
    """
    Standardise data after processing.

    Recursively converts:
    - lists to tuples
    - defaultdicts to dicts
    - types in `mapping` to their mapped type or apply mapped function.

    Parameters
    ----------
    obj : Any
        Object to normalise.
    mapping : Dict[type, Union[type, Callable]]
        Mapping of `type` to a callable transformation
        including class constructors.

    Returns
    -------
    Any
        Normmalised data.
    """
    if isinstance(obj, (tuple, list)):
        obj = tuple(normalise(v, mapping) for v in obj)
    elif isinstance(obj, (dict, defaultdict)):
        obj = {key: normalise(val, mapping) for key, val in obj.items()}

    if type(obj) in mapping:
        obj = mapping[type(obj)](obj)

    return obj


def json_safe(obj: Any) -> Any:
    """
    Recursively transform datatypes into JSON safe variants.

    Including:
    - Ensuring dict keys are strings without spaces.
    - Ensuring complex numbers are split into real/imag components.

    Parameters
    ----------
    obj : Any
        Incoming datatype.

    Returns
    -------
    Any
        Safe datatype.

    Examples
    --------
    >>> json_safe(3 + 4i)
    {"real": 3., "imag": 4.}
    >>> json_safe({("Ar", "Sr"): 3})
    {"Ar_Sr": 3}
    >>> json_safe({(("Ar", 1), ("Sr", 1)): 3})
    {"Ar_1_Sr_1": 3}
    """
    if isinstance(obj, dict):
        obj_out = {}

        for key, val in obj.items():
            if isinstance(key, (tuple, list)):
                # Key in bonds is tuple[tuple[AtomIndex]]
                if isinstance(key[0], tuple):
                    key = "_".join(str(y) for x in key for y in x)
                else:
                    key = "_".join(map(str, key))
            obj_out[key] = json_safe(val)

        obj = obj_out
    elif isinstance(obj, complex):
        obj = {"real": obj.real, "imag": obj.imag}
    return obj


def flatten_dict(dictionary: MutableMapping[Any, Any],
                 parent_key: str = "",
                 separator: str = "_") -> dict[str, Any]:
    """
    Turn a nested dictionary into a flattened dictionary.

    Parameters
    ----------

    dictionary : MutableMapping[Any, Any]
        The dictionary to flatten.
    parent_key : str
        The string to prepend to dictionary's keys.
    separator : str
        The string used to separate flattened keys.

    Returns
    -------
    dict[str, Any]
        A flattened dictionary.

    Notes
    -----
    Taken from:
    https://stackoverflow.com/a/62186053
    """

    items: list[tuple[Any, Any]] = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        if isinstance(value, collections.abc.MutableMapping):
            items.extend(flatten_dict(value, new_key, separator).items())
        elif isinstance(value, list):
            for keyx, val in enumerate(value):
                items.extend(flatten_dict({str(keyx): val}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


def stack_dict(out_dict: dict[Any, list], in_dict: dict[Any, list]):
    """
    Append items in `in_dict` to the keys in `out_dict`.

    Parameters
    ----------
    out_dict : dict[Any, list]
        Dict to append to.
    in_dict : dict[Any, list]
        Dict to append from.
    """
    for key, val in in_dict.items():
        out_dict[key].append(val)


def add_aliases(in_dict: dict[str, Any],
                alias_dict: dict[str, str], *,
                replace: bool = False,
                inplace: bool = True) -> dict[str, Any]:
    """
    Add aliases of known names into dictionary, if replace is true, remove original.

    Parameters
    ----------
    in_dict : Dict[str, Any]
        FIXME: Add docs.
    alias_dict : Dict[str, str]
        FIXME: Add docs.
    replace : bool
        FIXME: Add docs.
    inplace : bool
        FIXME: Add docs.

    Returns
    -------
    Dict[str, Any]
        FIXME: Add docs.

    Examples
    --------
    FIXME: Add docs.
    """
    out_dict = in_dict if inplace else copy(in_dict)

    for frm, new in alias_dict.items():
        if frm in in_dict:
            out_dict[new] = in_dict[frm]
            if replace:
                out_dict.pop(frm)
    return out_dict


@functools.singledispatch
def log_factory(file) -> Callable:
    """
    Return logging function to add file info to logs.

    Parameters
    ----------
    file : TextIO or ~fileinput.FileInput or FileWrapper
        File to apply logging for.

    Returns
    -------
    Callable
        Function for logging data.
    """
    if hasattr(file, "name"):
        def log_file(message, *args, level="info"):
            getattr(logging, level)(f"[{file.name}] {message}", *args)
    else:
        def log_file(message, *args, level="info"):
            getattr(logging, level)(message, *args)

    return log_file


@log_factory.register
def _(file: fileinput.FileInput):
    def log_file(message, *args, level="info"):
        getattr(logging, level)(f"[{file.filename()}:{file.lineno()}]"
                                f" {message}", *args)

    return log_file


@log_factory.register
def _(file: FileWrapper) -> Callable:
    def log_file(message, *args, level="info"):
        getattr(logging, level)(f"[{file.name}:{file.lineno}]"
                                f" {message}", *args)

    return log_file


def determine_type(data: str) -> type:
    """
    Determine the datatype and return the appropriate type.

    For dealing with miscellaneous data read from input files.

    Parameters
    ----------
    data : str
        String to process.

    Returns
    -------
    type
        Best type to attempt.

    Examples
    --------
    >>> determine_type('T')
    bool
    >>> determine_type('False')
    bool
    >>> determine_type('3.1415')
    float
    >>> determine_type('123')
    int
    >>> determine_type('1/3')
    float
    >>> determine_type('BEEF')
    str
    """

    """  """
    if data.title() in ("T", "True", "F", "False"):
        return bool

    if re.match(rf"(?:\s*{REs.EXPFNUMBER_RE})+", data):
        return float

    if re.match(rf"(?:\s*{REs.INTNUMBER_RE})+", data):
        return int

    if re.match(rf"(?:\s*{REs.FLOAT_RAT_RE.pattern})+", data):
        return float

    return str


def parse_int_or_float(numbers: Iterable[str]) -> int | float:
    """
    Parse numbers to `int` if all elements ints or `float` otherwise.

    Parameters
    ----------
    numbers : Iterable[str]
        Sequence of numbers to parse.

    Returns
    -------
    int or float
        Parsed numerical value.

    Examples
    --------
    >>> parse_int_or_float("3.141")
    3.141
    >>> parse_int_or_float("7")
    7
    """
    if all(x.isdigit() for x in numbers):
        return to_type(numbers, int)

    return to_type(numbers, float)


def _parse_float_or_rational(val: str) -> float:
    """ Parse a float or a rational to float """
    if "/" in val:
        numerator, denominator = val.split("/")
        return float(numerator) / float(denominator)

    return float(val)


def _parse_logical(val: str) -> bool:
    """ Parse a logical to a bool """
    return val.title() in ("T", "True", "1")


_TYPE_PARSERS: dict[type, Callable] = {float: _parse_float_or_rational,
                                       bool: _parse_logical}


@functools.singledispatch
def to_type(data_in, _: type):
    """ Convert types to `typ` regardless of if data_in is iterable or otherwise """
    return data_in


@to_type.register(str)
def _(data_in: str, typ: type[T]) -> T:
    parser: Callable[[str], T] = _TYPE_PARSERS.get(typ, typ)
    return parser(data_in)


@to_type.register(tuple)
@to_type.register(list)
def _(data_in, typ: type[T]) -> tuple[T, ...]:
    parser: Callable[[str], T] = _TYPE_PARSERS.get(typ, typ)
    return tuple(parser(x) for x in data_in)


def fix_data_types(in_dict: MutableMapping, type_dict: dict[str, type]):
    """ Applies correct types to elements of in_dict by mapping given in type_dict"""
    for key, typ in type_dict.items():
        if key in in_dict:
            in_dict[key] = to_type(in_dict[key], typ)
