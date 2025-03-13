"""Tools for dumping Fortran unformatted file."""
from __future__ import annotations

import struct
from collections.abc import Sequence
from functools import singledispatch
from io import BytesIO
from typing import Any, TypeVar

import pytest

T = TypeVar("T")

def _get_type(elem: T | Sequence[T]) -> type[T]:
    if isinstance(elem, Sequence):
        val = next(iter(elem), None)
        return int if val is None else type(val)
    return type(elem)

@pytest.fixture
def fake_file(request):
    return to_unformat_file(*request.param)

@pytest.fixture
def data_types(request):
    return tuple(map(_get_type, request.param))

@pytest.fixture
def raw_data(request):
    return request.param

@singledispatch
def fort_unformat(inp) -> bytes:
    """Convert data ready for dumping in Fortan unformatted."""
    raise NotImplementedError(f"Cannot convert {type(inp).__name__}.")


@fort_unformat.register(list)
@fort_unformat.register(tuple)
def _(inp) -> bytes:
    return add_size(b"".join(map(to_bytes, inp)))


@fort_unformat.register(float)
@fort_unformat.register(int)
@fort_unformat.register(str)
def _(inp) -> bytes:
    return add_size(to_bytes(inp))


@singledispatch
def to_bytes(inp) -> bytes:
    """Convert python data to big-endian bytes."""
    raise NotImplementedError(f"Cannot convert {type(inp).__name__}.")


@to_bytes.register
def _(inp: float) -> bytes:
    return struct.pack(">d", inp)


@to_bytes.register
def _(inp: int) -> bytes:
    return struct.pack(">i", inp)


@to_bytes.register
def _(inp: str) -> bytes:
    return struct.pack(f">{len(inp)}s", bytes(inp, encoding="utf-8"))


def add_size(inp: bytes) -> bytes:
    """Add byte size to either end (Fortran record format)."""
    size = to_bytes(len(inp))
    return b"".join((size, inp, size))


def to_unformat_file(*inp: Any) -> BytesIO:
    """Convert sequence of data to an unformatted file."""
    return BytesIO(b"".join(map(fort_unformat, inp)))
