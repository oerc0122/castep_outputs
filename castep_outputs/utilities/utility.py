"""
Utility functions for parsing castep outputs
"""

import collections.abc
import fileinput
import functools
import logging
import re
from collections import defaultdict
from copy import copy
from typing import (Any, Callable, Dict, Iterable, List, MutableMapping, Tuple,
                    Type, TypeVar, Union)

import castep_outputs.utilities.castep_res as REs

from .filewrapper import FileWrapper

T = TypeVar('T')


def normalise_string(string: str) -> str:
    """
    Normalise a string removing leading/trailing space
    and making all spacing single-space
    """
    return " ".join(string.strip().split())


def normalise_key(string: str) -> str:
    """
    Normalise a key removing punctuation
    and making all spacing single-underscore
    """
    return re.sub(r"[_\W]+", "_", string).strip("_").lower()


def atreg_to_index(dict_in: Union[Dict[str, str], re.Match], clear: bool = True) -> Tuple[str, int]:
    """
    Transform a matched atreg value to species index tuple
    Also clear value from dictionary for easier processing
    """
    spec, ind = dict_in["spec"], dict_in["index"]

    if isinstance(dict_in, dict) and clear:
        del dict_in["spec"]
        del dict_in["index"]

    return (spec, int(ind))


def normalise(obj: Any, mapping: Dict[type, Union[type, Callable]]) -> Any:
    """
    Standardises data after processing
    """
    if isinstance(obj, (tuple, list)):
        obj = tuple(normalise(v, mapping) for v in obj)
    elif isinstance(obj, (dict, defaultdict)):
        obj = {key: normalise(val, mapping) for key, val in obj.items()}

    if type(obj) in mapping:
        obj = mapping[type(obj)](obj)

    return obj


def json_safe(obj: Any) -> Any:
    """ Transform datatypes into JSON safe variants"""
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
                 parent_key: bool = False,
                 separator: str = '_') -> Dict[str, Any]:
    """
    Turn a nested dictionary into a flattened dictionary

    Taken from:
    https://stackoverflow.com/a/62186053

    :param dictionary: The dictionary to flatten
    :param parent_key: The string to prepend to dictionary's keys
    :param separator: The string used to separate flattened keys
    :return: A flattened dictionary
    """

    items: List[Tuple[Any, Any]] = []
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


def stack_dict(out_dict: Dict[Any, List], in_dict: Dict[Any, List]) -> Dict[Any, List]:
    """ Append items in `in_dict` to the keys in `out_dict` """
    for key, val in in_dict.items():
        out_dict[key].append(val)


def add_aliases(in_dict: Dict[str, Any],
                alias_dict: Dict[str, str],
                replace: bool = False,
                inplace: bool = True) -> Dict[str, Any]:
    """ Adds aliases of known names into dictionary, if replace is true, remove original """
    out_dict = in_dict if inplace else copy(in_dict)

    for frm, new in alias_dict.items():
        if frm in in_dict:
            out_dict[new] = in_dict[frm]
            if replace:
                out_dict.pop(frm)
    return out_dict


@functools.singledispatch
def log_factory(file) -> Callable:
    """ Return logging function to add file info to logs """

    if hasattr(file, 'name'):
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
    """ Deterimine the datatype rand return the appropriate types """
    if data.title() in ("T", "True", "F", "False"):
        return bool

    if re.match(rf"(?:\s*{REs.EXPFNUMBER_RE})+", data):
        return float

    if re.match(rf"(?:\s*{REs.INTNUMBER_RE})+", data):
        return int

    if re.match(rf"(?:\s*{REs.FLOAT_RAT_RE.pattern})+", data):
        return float

    return str


def parse_int_or_float(numbers: Iterable[str]) -> Union[int, float]:
    """ Parses numbers to `int` if all elements ints or `float` otherwise """
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


_TYPE_PARSERS: Dict[type, Callable] = {float: _parse_float_or_rational,
                                       bool: _parse_logical}


@functools.singledispatch
def to_type(data_in, _: type):
    """ Convert types to `typ` regardless of if data_in is iterable or otherwise """
    return data_in


@to_type.register(str)
def _(data_in: str, typ: Type[T]) -> T:
    parser: Callable[[str], T] = _TYPE_PARSERS.get(typ, typ)
    return parser(data_in)


@to_type.register(tuple)
@to_type.register(list)
def _(data_in, typ: Type[T]) -> Tuple[T, ...]:
    parser: Callable[[str], T] = _TYPE_PARSERS.get(typ, typ)
    return tuple(parser(x) for x in data_in)


def fix_data_types(in_dict: MutableMapping, type_dict: Dict[str, type]):
    """ Applies correct types to elements of in_dict by mapping given in type_dict"""
    for key, typ in type_dict.items():
        if key in in_dict:
            in_dict[key] = to_type(in_dict[key], typ)
