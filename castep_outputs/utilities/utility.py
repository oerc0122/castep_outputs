"""Utility functions for parsing castep outputs."""

from __future__ import annotations

import collections.abc
import fileinput
import functools
import logging
import re
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping, Sequence
from copy import copy
from functools import singledispatch, wraps
from itertools import filterfalse
from pathlib import Path
from typing import (
    IO,
    Any,
    Concatenate,
    Literal,
    ParamSpec,
    Protocol,
    TextIO,
    TypeAlias,
    TypedDict,
    TypeVar,
    cast,
    overload,
)

from castep_outputs.utilities.filewrapper import Block, FileWrapper

T = TypeVar("T")
In = TypeVar("In")
Out = TypeVar("Out")
K = TypeVar("K")
P = ParamSpec("P")

NORMALISE_RE = re.compile(r"[_\W]+")
LoggingLevels = Literal["debug", "info", "warning", "error", "critical"]


class Logger(Protocol):
    """Protocol for logging classes."""

    def __call__(self, message: str, *args: Any, level: LoggingLevels = "info") -> None:
        """Call method for logging methods."""


class ComplexDict(TypedDict):
    """Dict of complex values."""

    real: float
    imag: float


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


def strip_nones(
    data: dict[K, Any],
    *,
    include: Iterable[K] | None = None,
    exclude: Iterable[K] = (),
) -> None:
    """Strip ``None`` from datasets.

    Parameters
    ----------
    data : dict[K, Any]
        Dataset to filter.
    include : Iterable[K] or None
        Values to include (or all if None)
    exclude : Iterable[K]
        Keys/indices to ignore.

    Examples
    --------
    >>> data = {"a": 1, "b": None, "c": None}
    >>> strip_nones(data, exclude=("c",))
    >>> data
    {'a': 1, 'c': None}
    """
    keys = data.keys() - set(exclude)
    if include is not None:
        keys = keys.intersection(include)

    for key in keys:
        if data[key] is None:
            del data[key]


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


NormDict: TypeAlias = dict[type[In], type[Out] | Callable[[In], Out]]


@overload
def normalise(obj: T, mapping: NormDict) -> T: ...
@overload
def normalise(obj: In, mapping: NormDict) -> Out: ...
@overload
def normalise(obj: Iterable[In | T], mapping: NormDict) -> tuple[Out | T, ...]: ...
@overload
def normalise(obj: Mapping[K, In | T], mapping: NormDict) -> dict[K, Out | T]: ...
def normalise(obj, mapping):
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
        Normalised data.
    """
    if isinstance(obj, (tuple, list)):
        obj = tuple(normalise(v, mapping) for v in obj)
    elif isinstance(obj, (dict, defaultdict)):
        obj = {key: normalise(val, mapping) for key, val in obj.items()}

    if type(obj) in mapping:
        obj = mapping[type(obj)](obj)

    return obj


@overload
def json_safe(obj: complex) -> ComplexDict: ...
@overload
def json_safe(obj: T) -> T: ...
@overload
def json_safe(obj: dict[Any, T]) -> dict[str, T]: ...
def json_safe(obj):
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
        obj: ComplexDict = {"real": obj.real, "imag": obj.imag}
    return obj


def flatten_dict(
    dictionary: MutableMapping[Any, Any],
    parent_key: str = "",
    separator: str = "_",
) -> dict[str, Any]:
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
        # Temporary hack because `None` used as key in species_pot
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, collections.abc.MutableMapping):
            items.extend(flatten_dict(value, new_key, separator).items())
        elif isinstance(value, (list, tuple)):
            for keyx, val in enumerate(value):
                items.extend(flatten_dict({str(keyx): val}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


def stack_dict(out_dict: Mapping[Any, list[T]], in_dict: Mapping[Any, T]) -> None:
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


def add_aliases(
    in_dict: dict[str, Any],
    alias_dict: dict[str, str],
    *,
    replace: bool = False,
    inplace: bool = True,
) -> dict[str, Any]:
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
        getattr(logging, level)(f"[{file.filename()}:{file.lineno()}] {message}", *args)

    return log_file


@log_factory.register
def _(file: FileWrapper) -> Logger:
    def log_file(message: str, *args: Any, level: LoggingLevels = "info") -> None:
        getattr(logging, level)(f"[{file.name}:{file.lineno}] {message}", *args)

    return log_file


@log_factory.register
def _(file: Block) -> Logger:
    def log_file(message: str, *args: Any, level: LoggingLevels = "info") -> None:
        getattr(logging, level)(f"[{file.name}:{file.lineno}] {message}", *args)

    return log_file


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
    data: Iterable[str],
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
    out = cast("Iterable[str]", filterfalse(comment_re.match, data))
    out = map(str.rstrip, out)
    out = filter(None, out)
    yield from out


def strip_comments(
    data: TextIO | FileWrapper | Block,
    *,
    comment_char: str | set[str] = "#!",
    remove_inline: bool = False,
) -> Block:
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
        raise ValueError(f"Multiple elements in sequence (remainder={', '.join(map(str, rest))}).")

    return val


def file_or_path(*, mode: Literal["r", "rb"], **open_kwargs: Any) -> Callable:
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

    def inner(
        func: Callable[Concatenate[IO, P], Out],
    ) -> Callable[Concatenate[str | Path | IO, P], Out]:
        @wraps(func)
        def wrapped(file: str | Path, *args: P.args, **kwargs: P.kwargs) -> Out:
            file = Path(file)
            with file.open(mode, **open_kwargs) as in_file:
                return func(in_file, *args, **kwargs)

        func = singledispatch(func)
        func.register(str, wrapped)
        func.register(Path, wrapped)
        return func

    return inner
