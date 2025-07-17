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
from fractions import Fraction
from functools import partial, singledispatch, wraps
from itertools import filterfalse
from pathlib import Path
from struct import unpack
from typing import Any, Literal, TextIO, TypeVar

import castep_outputs.utilities.castep_res as REs

from ..utilities.filewrapper import Block
from .filewrapper import FileWrapper

T = TypeVar("T")
NORMALISE_RE = re.compile(r"[_\W]+")
LoggingLevels = Literal["debug", "info", "warning", "error", "critical"]
Logger = Callable[[str, tuple[Any, ...], LoggingLevels], None]


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
    return NORMALISE_RE.sub("_", string).strip("_").lower()


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


def normalise(obj: T, mapping: dict[type, type | Callable]) -> T:
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


def json_safe(obj: dict | complex | T) -> dict | T:
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
        elif isinstance(value, (list, tuple)):
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
def log_factory(file: TextIO | fileinput.FileInput | FileWrapper) -> Logger:
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
        def log_file(message: str, *args: Any, level: LoggingLevels = "info") -> None:
            getattr(logging, level)(f"[{file.name}] {message}", *args)
    else:
        def log_file(message: str, *args: Any, level: LoggingLevels = "info") -> None:
            getattr(logging, level)(message, *args)

    return log_file


@log_factory.register
def _(file: fileinput.FileInput) -> Logger:
    def log_file(message: str, *args: Any, level: LoggingLevels = "info") -> None:
        getattr(logging, level)(f"[{file.filename()}:{file.lineno()}]"
                                f" {message}", *args)

    return log_file


@log_factory.register
def _(file: FileWrapper) -> Logger:
    def log_file(message: str, *args: Any, level: LoggingLevels = "info") -> None:
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
    if data.title() in {"T", "True", "F", "False"}:
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
    return float(Fraction(val))


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
    return val.title() in {"T", "True", "1"}


def _parse_float_bytes(val: bytes) -> float | Sequence[float]:
    r"""Parse (big-endian) bytes to float.

    Parameters
    ----------
    val : bytes
        Values to parse.

    Returns
    -------
    float | Sequence[float]
        Parsed value or list of values.

    Examples
    --------
    >>> one = b"?\xf0\x00\x00\x00\x00\x00\x00"
    >>> zero = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    >>> _parse_float_bytes(zero)
    0.0
    >>> _parse_float_bytes(one)
    1.0
    >>> _parse_float_bytes(one*3)
    (1.0, 1.0, 1.0)
    """
    result = unpack(f">{len(val) // 8}d", val)
    return result if len(result) != 1 else result[0]


def _parse_int_bytes(val: bytes) -> int | Sequence[int]:
    r"""Parse (big-endian) bytes to int.

    Parameters
    ----------
    val : bytes
        Values to parse.

    Returns
    -------
    int | Sequence[int]
        Parsed value or list of values.

    Examples
    --------
    >>> one = b"\x00\x00\x00\x01"
    >>> zero = b"\x00\x00\x00\x00"
    >>> _parse_int_bytes(zero)
    0
    >>> _parse_int_bytes(one)
    1
    >>> _parse_int_bytes(one*3)
    (1, 1, 1)
    """
    result = unpack(f">{len(val) // 4}i", val)
    return result if len(result) != 1 else result[0]


def _parse_bool_bytes(val: bytes) -> bool | Sequence[bool]:
    r"""Parse (big-endian) bytes to bool.

    Parameters
    ----------
    val : bytes
        Values to parse.

    Returns
    -------
    bool | Sequence[bool]
        Parsed value or list of values.

    Examples
    --------
    >>> one = b"\x00\x00\x00\x01"
    >>> zero = b"\x00\x00\x00\x00"
    >>> _parse_bool_bytes(zero)
    False
    >>> _parse_bool_bytes(one)
    True
    >>> _parse_bool_bytes(one*3)
    (True, True, True)
    """
    result = tuple(map(bool, unpack(f">{len(val) // 4}i", val)))
    return result if len(result) != 1 else result[0]


def _parse_complex_bytes(val: bytes) -> complex | Sequence[complex]:
    r"""Parse (big-endian) bytes to complex.

    Parameters
    ----------
    val : bytes
        Values to parse.

    Returns
    -------
    complex | Sequence[complex]
        Parsed value or list of values.

    Examples
    --------
    >>> one = b"?\xf0\x00\x00\x00\x00\x00\x00"
    >>> zero = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    >>> _parse_complex_bytes(zero + one)
    1j
    >>> _parse_complex_bytes(one + zero)
    (1+0j)
    >>> _parse_complex_bytes((one+one)*3)
    ((1+1j), (1+1j), (1+1j))
    """
    tmp = unpack(f">{len(val) // 8}d", val)
    result = tuple(map(complex, tmp[::2], tmp[1::2]))
    return result if len(result) != 1 else result[0]


_TYPE_PARSERS: dict[type, Callable] = {float: _parse_float_or_rational,
                                       bool: _parse_logical}
_BYTE_PARSERS: dict[type, Callable] = {complex: _parse_complex_bytes,
                                       float: _parse_float_bytes,
                                       bool: _parse_bool_bytes,
                                       int: _parse_int_bytes,
                                       str: partial(str, encoding="ascii")}


@functools.singledispatch
def to_type(data_in: T, _typ: type) -> T:
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
def _(data_in: Any, typ: type[T]) -> tuple[T, ...]:
    parse_dict = _BYTE_PARSERS if data_in and isinstance(data_in[0], bytes) else _TYPE_PARSERS
    parser: Callable[[str], T] = parse_dict.get(typ, typ)
    return tuple(parser(x) for x in data_in)


@to_type.register(bytes)
def _(data_in: Any, typ: type[T]) -> T | tuple[T, ...]:
    parser: Callable[[bytes], T] = _BYTE_PARSERS.get(typ, typ)
    return parser(data_in)


def fix_data_types(in_dict: MutableMapping[str, Any], type_dict: dict[str, type]) -> None:
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


def file_or_path(*, mode: Literal["r", "rb"], **open_kwargs: Any) -> Callable:  # paramspec 3.10+
    """Decorate to allow a parser to accept either a path or open file.

    Parameters
    ----------
    mode : Literal["r", "rb"]
        Open mode if passed a :class:`~pathlib.Path` or :class:`str`.

    Returns
    -------
    Callable
        Wrapped function able to handle open files or paths invisibly.
    """
    def inner(func: Callable) -> Callable:
        @wraps(func)
        def wrapped(file: str | Path, *args: Any, **kwargs: Any) -> Callable:
            file = Path(file)
            with file.open(mode, **open_kwargs) as in_file:
                return func(in_file, *args, **kwargs)

        func = singledispatch(func)
        func.register(str, wrapped)
        func.register(Path, wrapped)
        return func

    return inner
