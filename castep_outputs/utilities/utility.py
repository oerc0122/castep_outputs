"""Utility functions for parsing castep outputs."""

from __future__ import annotations

import collections.abc
import fileinput
import functools
import logging
import re
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, MutableMapping, Sequence
from copy import copy
from itertools import filterfalse
from typing import Any, TextIO, TypeVar

import castep_outputs.utilities.castep_res as REs

from ..utilities.filewrapper import Block
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
    string
        String to process.

    Returns
    -------
    str
        Normalised string.

    Examples
    --------
    >>> normalise_string(" Several   words  ")
    'Several words'
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
    string
        String to process.

    Returns
    -------
    str
        Normalised string.

    Examples
    --------
    >>> normalise_key(" Several   words  ")
    'several_words'
    >>> normalise_key("A sentence.")
    'a_sentence'
    >>> normalise_key("I<3;;semi-colons;;!!!")
    'i_3_semi_colons'
    """
    return re.sub(r"[_\W]+", "_", string).strip("_").lower()


def atreg_to_index(dict_in: dict[str, str] | re.Match, *, clear: bool = True) -> tuple[str, int]:
    """
    Transform a matched atreg value to species index tuple.

    Optionally clear value from dictionary for easier processing.

    Parameters
    ----------
    dict_in
        Atreg to process.
    clear
        Whether to remove from incoming dictionary.

    Returns
    -------
    species : str
        Atomic species.
    ind : int
        Internal index.

    Examples
    --------
    >>> parsed_line = {'x': 3.1, 'y': 2.1, 'z': 1.0, 'spec': 'Ar', 'index': '1'}
    >>> atreg_to_index(parsed_line, clear=False)
    ('Ar', 1)
    >>> parsed_line
    {'x': 3.1, 'y': 2.1, 'z': 1.0, 'spec': 'Ar', 'index': '1'}
    >>> atreg_to_index(parsed_line)
    ('Ar', 1)
    >>> parsed_line
    {'x': 3.1, 'y': 2.1, 'z': 1.0}
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

    - ``list`` s to ``tuple`` s
    - ``defaultdict`` s to ``dict`` s
    - types in `mapping` to their mapped type or apply mapped function.

    Parameters
    ----------
    obj
        Object to normalise.
    mapping
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
    obj
        Incoming datatype.

    Returns
    -------
    Any
        Safe datatype.

    Examples
    --------
    >>> json_safe(3 + 4j)
    {'real': 3.0, 'imag': 4.0}
    >>> json_safe({('Ar', 'Sr'): 3})
    {'Ar_Sr': 3}
    >>> json_safe({(('Ar', 1), ('Sr', 1)): 3})
    {'Ar_1_Sr_1': 3}
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
    dictionary
        The dictionary to flatten.
    parent_key
        The string to prepend to dictionary's keys.
    separator
        The string used to separate flattened keys.

    Returns
    -------
    dict[str, Any]
        A flattened dictionary.

    Notes
    -----
    Taken from:
    https://stackoverflow.com/a/62186053

    Examples
    --------
    >>> flatten_dict({'hello': ['is', 'me'],
    ...               "goodbye": {"nest": "birds", "child": "moon"}})
    {'hello_0': 'is', 'hello_1': 'me', 'goodbye_nest': 'birds', 'goodbye_child': 'moon'}
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


def stack_dict(out_dict: dict[Any, list], in_dict: dict[Any, list]) -> None:
    """
    Append items in `in_dict` to the keys in `out_dict`.

    Parameters
    ----------
    out_dict
        Dict to append to.
    in_dict
        Dict to append from.
    """
    for key, val in in_dict.items():
        out_dict[key].append(val)


def add_aliases(in_dict: dict[str, Any],
                alias_dict: dict[str, str], *,
                replace: bool = False,
                inplace: bool = True) -> dict[str, Any]:
    """
    Add aliases of known names into dictionary.

    If replace is `True`, this will remove the original.

    Parameters
    ----------
    in_dict
        Dictionary of data to alias.
    alias_dict
        Mapping of from->to for keys in `in_dict`.
    replace
        Whether to remove the `from` key from `in_dict`.
    inplace
        Whether to return a copy or overwrite `in_dict`.

    Returns
    -------
    dict[str, Any]
        `in_dict` with keys substituted.

    Examples
    --------
    >>> add_aliases({'hi': 1, 'bye': 2}, {'hi': 'frog'})
    {'hi': 1, 'bye': 2, 'frog': 1}
    >>> add_aliases({'hi': 1, 'bye': 2}, {'hi': 'frog'}, replace=True)
    {'bye': 2, 'frog': 1}
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
    file : ~typing.TextIO or ~fileinput.FileInput or FileWrapper
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
def _(file: fileinput.FileInput) -> Callable:
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
    data
        String to process.

    Returns
    -------
    type
        Best type to attempt.

    Examples
    --------
    >>> determine_type('T')
    <class 'bool'>
    >>> determine_type('False')
    <class 'bool'>
    >>> determine_type('3.1415')
    <class 'float'>
    >>> determine_type('123')
    <class 'int'>
    >>> determine_type('1/3')
    <class 'float'>
    >>> determine_type('BEEF')
    <class 'str'>
    """
    if data.title() in ("T", "True", "F", "False"):
        return bool

    if re.match(rf"(?:\s*{REs.EXPFNUMBER_RE})+", data):
        return float

    if re.match(rf"(?:\s*{REs.RATIONAL_RE})+", data):
        return float

    if re.match(rf"(?:\s*{REs.INTNUMBER_RE})+", data):
        return int

    return str


def parse_int_or_float(numbers: Iterable[str]) -> int | float:
    """
    Parse numbers to `int` if all elements ints or `float` otherwise.

    Parameters
    ----------
    numbers
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
    """
    Parse a float or rational to float.

    Parameters
    ----------
    val
        Value to parse.

    Returns
    -------
    float
        Parsed value.

    Examples
    --------
    >>> _parse_float_or_rational("0.5")
    0.5
    >>> _parse_float_or_rational("1/2")
    0.5
    """
    if "/" in val:
        numerator, denominator = val.split("/")
        return float(numerator) / float(denominator)

    return float(val)


def _parse_logical(val: str) -> bool:
    """
    Parse a logical to a bool.

    Parameters
    ----------
    val
        String to parse.

    Returns
    -------
    bool
        Parsed value.

    Notes
    -----
    Case-insensitive.

    Examples
    --------
    >>> _parse_logical("T")
    True
    >>> _parse_logical("TrUe")
    True
    >>> _parse_logical("1")
    True
    >>> _parse_logical("F")
    False
    """
    return val.title() in ("T", "True", "1")


_TYPE_PARSERS: dict[type, Callable] = {float: _parse_float_or_rational,
                                       bool: _parse_logical}


@functools.singledispatch
def to_type(data_in, _typ: type):
    """
    Convert types to `typ` regardless of if data_in is iterable or otherwise.

    Parameters
    ----------
    data_in : str or ~collections.abc.Sequence
        Data to convert.
    typ : type
        Type to convert to.

    Returns
    -------
    `typ` or tuple[`typ`, ...]
        Converted data.
    """
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


def fix_data_types(in_dict: MutableMapping[str, Any], type_dict: dict[str, type]):
    """
    Apply correct types to elements of `in_dict` by mapping given in `type_dict`.

    Parameters
    ----------
    in_dict
        Dictionary of {key: values} to convert.
    type_dict
        Mapping of keys to types the keys should be converted to.

    See Also
    --------
    to_type : Conversion function.

    Notes
    -----
    Modifies the dictionary in-place.

    Examples
    --------
    >>> my_dict = {"int": "7", "float": "3.141", "bool": "T",
    ...            "vector": ["3", "4", "5"], "blank": "Hello"}
    >>> type_map = {"int": int, "float": float, "bool": bool, "vector": float}
    >>> fix_data_types(my_dict, type_map)
    >>> print(my_dict)
    {'int': 7, 'float': 3.141, 'bool': True, 'vector': (3.0, 4.0, 5.0), 'blank': 'Hello'}
    """
    for key, typ in type_dict.items():
        if key in in_dict:
            in_dict[key] = to_type(in_dict[key], typ)


def _strip_inline_comments(
        data: TextIO | FileWrapper | Block,
        *,
        comment_char: set[str],
) -> Iterator[str]:
    r"""
    Strip all comments from provided data.

    Parameters
    ----------
    data
        Data to strip comments from.
    comment_char
        Characters to interpret as comments.

    Yields
    ------
    str
        Data with line-initial comments stripped.

    Notes
    -----
    Also strips trailing, but not leading whitespace to clean up comment blocks.

    Also strips empty lines.

    Examples
    --------
    >>> from io import StringIO
    >>> inp = StringIO('''
    ... Hello
    ... # Initial line comment
    ... End of line # comment
    ... ''')
    >>> '|'.join(_strip_inline_comments(inp, comment_char={"#",}))
    'Hello|End of line'
    """
    comment_re = re.compile(f"({'|'.join(comment_char)})")

    for line in data:
        line = comment_re.split(line)[0].rstrip()
        if not line:
            continue

        yield line

def _strip_initial_comments(
        data: TextIO | FileWrapper | Block,
        *,
        comment_char: set[str],
) -> Iterator[str]:
    r"""
    Strip line-initial comments from provided data.

    Parameters
    ----------
    data
        Data to strip comments from.
    comment_char
        Characters to interpret as comments.

    Yields
    ------
    str
        Data with line-initial comments stripped.

    Notes
    -----
    Also strips trailing, but not leading whitespace to clean up comment blocks.

    Also strips empty lines.

    Examples
    --------
    >>> from io import StringIO
    >>> inp = StringIO('''
    ... Hello
    ... # Initial line comment
    ... End of line # comment
    ... ''')
    >>> '|'.join(_strip_initial_comments(inp, comment_char={"#",}))
    'Hello|End of line # comment'
    """
    comment_re = re.compile(rf"^\s*({'|'.join(comment_char)})")
    data = filterfalse(comment_re.match, data)
    data = map(str.rstrip, data)
    data = filter(None, data)
    yield from data

def strip_comments(
        data: TextIO | FileWrapper | Block,
        *,
        comment_char: str | set[str] = "#!",
        remove_inline: bool = False) -> Block:
    r"""
    Strip comments from data.

    Parameters
    ----------
    data
        Data to strip comments from.
    remove_inline
        Whether to remove inline comments or just line initial.
    comment_char
        Character sets to read as comments and remove.

        .. note::

            If the chars are passed as a string, it is assumed that
            each character is a comment character.

            To match a multicharacter comment you **must** pass this
            as a set or sequence of strings.

    Returns
    -------
    Block
        Block of data without comments.

    Notes
    -----
    Also strips trailing, but not leading whitespace to clean up comment blocks.

    Also strips empty lines.

    Examples
    --------
    >>> from io import StringIO
    >>> inp = StringIO('''
    ... Hello
    ... # Initial line comment
    ... End of line # comment
    ... // C-style
    ... ''')
    >>> x = strip_comments(inp, remove_inline=False)
    >>> type(x).__name__
    'Block'
    >>> '|'.join(x)
    'Hello|End of line # comment|// C-style'
    >>> _ = inp.seek(0)
    >>> x = strip_comments(inp, remove_inline=True)
    >>> '|'.join(x)
    'Hello|End of line|// C-style'
    >>> _ = inp.seek(0)
    >>> x = strip_comments(inp, comment_char={"//", "#"})
    >>> '|'.join(x)
    'Hello|End of line # comment'
    """
    if not isinstance(comment_char, set):
        comment_char = set(comment_char)

    strip_function = _strip_inline_comments if remove_inline else _strip_initial_comments
    stripped_comments = strip_function(data, comment_char=comment_char)

    return Block.from_iterable(stripped_comments, parent=data)


def get_only(seq: Sequence[T]) -> T:
    """
    Get the only element of a Sequence ensuring uniqueness.

    Parameters
    ----------
    seq
        Sequence of one element.

    Returns
    -------
    Any
        The sole element of the sequence.

    Raises
    ------
    ValueError
        Value is not alone.
    """
    val, *rest = seq
    if rest:
        raise ValueError(f"Multiple elements in sequence (remainder={', '.join(rest)}).")

    return val
