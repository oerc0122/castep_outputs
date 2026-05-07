"""Functions for parsing raw data into python types."""

import re
from collections.abc import Callable, Iterable, Mapping, MutableMapping
from fractions import Fraction
from struct import unpack
from types import EllipsisType
from typing import (
    Any,
    TypeAlias,
    TypeVar,
    overload,
)

import castep_outputs.utilities.castep_res as REs
from castep_outputs.utilities.utility import get_only

T = TypeVar("T")
U = TypeVar("U")
K = TypeVar("K")


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


@overload
def parse_int_or_float(numbers: str) -> int | float: ...
@overload
def parse_int_or_float(numbers: Iterable[str]) -> tuple[int | float, ...]: ...
def parse_int_or_float(numbers):
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


def _parse_float_bytes(val: bytes) -> tuple[float, ...]:
    r"""Parse (big-endian) bytes to float.

    Parameters
    ----------
    val : bytes
        Values to parse.

    Returns
    -------
    tuple[float, ...]
        Parsed value or list of values.

    Examples
    --------
    >>> one = b"?\xf0\x00\x00\x00\x00\x00\x00"
    >>> zero = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    >>> _parse_float_bytes(zero)
    (0.0,)
    >>> _parse_float_bytes(one)
    (1.0,)
    >>> _parse_float_bytes(one*3)
    (1.0, 1.0, 1.0)
    """
    return unpack(f">{len(val) // 8}d", val)


def _parse_int_bytes(val: bytes) -> tuple[int, ...]:
    r"""Parse (big-endian) bytes to int.

    Parameters
    ----------
    val : bytes
        Values to parse.

    Returns
    -------
    tuple[int, ...]
        Parsed value or list of values.

    Examples
    --------
    >>> one = b"\x00\x00\x00\x01"
    >>> zero = b"\x00\x00\x00\x00"
    >>> _parse_int_bytes(zero)
    (0,)
    >>> _parse_int_bytes(one)
    (1,)
    >>> _parse_int_bytes(one*3)
    (1, 1, 1)
    """
    return unpack(f">{len(val) // 4}i", val)


def _parse_bool_bytes(val: bytes) -> tuple[bool, ...]:
    r"""Parse (big-endian) bytes to bool.

    Parameters
    ----------
    val : bytes
        Values to parse.

    Returns
    -------
    tuple[bool, ...]
        Parsed value or list of values.

    Examples
    --------
    >>> one = b"\x00\x00\x00\x01"
    >>> zero = b"\x00\x00\x00\x00"
    >>> _parse_bool_bytes(zero)
    (False,)
    >>> _parse_bool_bytes(one)
    (True,)
    >>> _parse_bool_bytes(one*3)
    (True, True, True)
    """
    return tuple(map(bool, unpack(f">{len(val) // 4}i", val)))


def _parse_complex_bytes(val: bytes) -> tuple[complex, ...]:
    r"""Parse (big-endian) bytes to complex.

    Parameters
    ----------
    val : bytes
        Values to parse.

    Returns
    -------
    tuple[complex, ...]
        Parsed value or list of values.

    Examples
    --------
    >>> one = b"?\xf0\x00\x00\x00\x00\x00\x00"
    >>> zero = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    >>> _parse_complex_bytes(zero + one)
    (1j,)
    >>> _parse_complex_bytes(one + zero)
    ((1+0j),)
    >>> _parse_complex_bytes((one+one)*3)
    ((1+1j), (1+1j), (1+1j))
    """
    tmp = unpack(f">{len(val) // 8}d", val)
    return tuple(map(complex, tmp[::2], tmp[1::2]))


def _parse_str_bytes(val: bytes) -> tuple[str, ...]:
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
    >>> a = b"Hello"
    >>> _parse_str_bytes(a)
    ('Hello',)
    """
    return (str(val, encoding="ascii"),)


_TYPE_PARSERS: dict[type, Callable[[str], Any]] = {
    complex: complex,
    float: _parse_float_or_rational,
    int: int,
    bool: _parse_logical,
    str: str,
}
_BYTE_PARSERS: dict[type, Callable[[bytes], tuple]] = {
    complex: _parse_complex_bytes,
    float: _parse_float_bytes,
    bool: _parse_bool_bytes,
    int: _parse_int_bytes,
    str: _parse_str_bytes,
}
ToTypeTuple: TypeAlias = tuple[type[T], EllipsisType]


@overload
def parse_bytes(data_in: bytes, typ: type[T]) -> T: ...
@overload
def parse_bytes(data_in: bytes, typ: ToTypeTuple) -> tuple[T, ...]: ...
def parse_bytes(data_in, typ):
    r"""Convert from (Fortran) bytes to a Python type.

    Parameters
    ----------
    data_in : bytes
        Data to convert.
    typ : type | tuple[type, "..."]
        Type to convert to.

    Returns
    -------
    T or tuple[T, ...]
        Processed value.

    Raises
    ------
    TypeError
        Invalid type form passed.

    Examples
    --------
    >>> b_rep = (3).to_bytes(4, byteorder="big")
    >>> parse_bytes(b_rep, int)
    3
    >>> parse_bytes(b_rep, (int, ...))
    (3,)
    >>> parse_bytes(b_rep * 3, (int, ...))
    (3, 3, 3)
    >>> parse_bytes(b_rep * 3, int)
    Traceback (most recent call last):
    ValueError: Multiple elements in sequence (remainder=3, 3).
    """
    match typ:
        case (type() as type_, EllipsisType()):
            parser = _BYTE_PARSERS[type_]
            out = parser(data_in)
        case type() as type_:
            parser = _BYTE_PARSERS[type_]
            out = get_only(parser(data_in))
        case _:
            raise TypeError(f"Cannot handle converting to {typ!r}.")

    return out


@overload
def to_type(data_in: str, typ: type[T]) -> T: ...
@overload
def to_type(data_in: Iterable[str | U], typ: type[T]) -> tuple[T | U, ...]: ...
@overload
def to_type(data_in: Mapping[K, str | U], typ: type[T]) -> dict[K, T | U]: ...
@overload
def to_type(data_in: U, typ: Any) -> U: ...
def to_type(data_in, typ):
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
    match data_in:
        case str():
            return _TYPE_PARSERS[typ](data_in)
        case Mapping():
            return {key: to_type(val, typ) for key, val in data_in.items()}
        case Iterable():
            return tuple(to_type(x, typ) for x in data_in)
        case _:
            return data_in
