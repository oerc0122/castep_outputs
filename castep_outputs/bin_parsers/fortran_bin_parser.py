"""General parser for the Fortran Unformatted file format."""

from collections.abc import Iterable, Iterator, Mapping
from functools import singledispatchmethod
from itertools import count
from os import SEEK_CUR
from typing import BinaryIO, TypeVar, overload

from castep_outputs.utilities.type_conv import ToTypeTuple, parse_bytes

T = TypeVar("T")
K = TypeVar("K")


class FortranBinaryReader:
    """Yield the elements of a Fortran unformatted file.

    Parameters
    ----------
    file
        Open file to get binary data from.

    Yields
    ------
    bytes
        Binary data record from Fortran file.

    Notes
    -----
    Each "record" is:

    ``(pre_nbytes: 4; data: nbytes; post_nbytes: 4)``

    Where ``pre_nbytes == post_nbytes`` (this is used in Fortran for rewinding).

    So when we rewind, we rewind the current size + ``post_nbytes``
    (current) + ``pre_nbytes`` (current) + ``post_nbytes`` (previous) [cursor
    now before post_nbytes (previous)] which is then read putting the
    cursor after post_nbytes (previous).

    When we do the final rewind, we put the cursor before ``pre_nbytes``
    ready to read the record.
    """

    def __init__(self, file: BinaryIO) -> None:
        self.file = file

    def __iter__(self) -> Iterator[bytes]:
        return self

    def __next__(self) -> bytes:
        bin_size = self.file.read(4)

        if not bin_size:
            raise StopIteration

        size = int.from_bytes(bin_size, "big")
        data = self.file.read(size)
        self.file.read(4)
        return data

    def rewind(self, n: int = 1, /) -> None:
        """Rewind ``n`` elements.

        Parameters
        ----------
        n
            How many elements to rewind.
        """
        self.skip(-n)

    def skip(self, n: int, /) -> None:
        """Ignore the next ``n`` elements.

        Parameters
        ----------
        n
            Number of elements to skip.
        """
        if n == 0:
            return

        if n < 0:
            self.file.seek(-4, SEEK_CUR)
            for _ in range(abs(n) - 1):
                # Rewind to record size before last read
                size = int.from_bytes(self.file.read(4), "big")
                self.file.seek(-size - 12, SEEK_CUR)

            # Rewind one extra
            size = int.from_bytes(self.file.read(4), "big")
            self.file.seek(-size - 8, SEEK_CUR)
        else:
            for _ in range(n):
                size = int.from_bytes(self.file.read(4), "big")
                self.file.seek(size + 4, SEEK_CUR)

    @overload
    def get(self, typ: type[T]) -> T: ...
    @overload
    def get(self, typ: ToTypeTuple) -> tuple[T, ...]: ...
    def get(self, typ):
        """Get next value as ``typ``.

        Parameters
        ----------
        typ
            Type to retrieve.

        Returns
        -------
        :
            Value as type.
        """
        return parse_bytes(next(self), typ)

    @overload
    def get_dtype_cycle(
        self,
        dtypes: tuple[type[T], ...],
        *,
        n: int | None,
    ) -> Iterator[tuple[T, ...]]: ...
    @overload
    def get_dtype_cycle(
        self,
        dtypes: tuple[ToTypeTuple, ...],
        *,
        n: int | None,
    ) -> Iterator[tuple[tuple[T, ...], ...]]: ...
    @overload
    def get_dtype_cycle(
        self,
        dtypes: tuple[type[T] | ToTypeTuple, ...],
        *,
        n: int | None,
    ) -> Iterator[tuple[T | tuple[T, ...], ...]]: ...
    @overload
    def get_dtype_cycle(
        self,
        dtypes: Mapping[K, type[T]],
        *,
        n: int | None,
    ) -> Iterator[dict[K, T]]: ...
    @overload
    def get_dtype_cycle(
        self,
        dtypes: Mapping[K, ToTypeTuple],
        *,
        n: int | None,
    ) -> Iterator[dict[K, tuple[T, ...]]]: ...
    @overload
    def get_dtype_cycle(
        self,
        dtypes: Mapping[K, type[T] | ToTypeTuple],
        *,
        n: int | None,
    ) -> Iterator[dict[K, T | tuple[T, ...]]]: ...
    def get_dtype_cycle(self, dtypes, *, n=None):
        """Get iterator over values reading dtypes each cycle.

        Parameters
        ----------
        dtypes
            Dtypes to load simultaneously.
        n
            Number of iterations to load or infinite if ``None``.

        Yields
        ------
        :
            Loaded data.
        """
        ind = count() if n is None else range(n)

        if isinstance(dtypes, dict):
            for _ in ind:
                yield self.get_dtype_dict(dtypes)
        else:
            for _ in ind:
                yield tuple(self.get_dtype_iter(dtypes))

    @overload
    def get_dtype_iter(self, dtypes: Iterable[type[T]]) -> Iterator[T]: ...
    @overload
    def get_dtype_iter(self, dtypes: Iterable[ToTypeTuple]) -> Iterator[tuple[T, ...]]: ...
    @overload
    def get_dtype_iter(
        self,
        dtypes: Iterable[type[T] | ToTypeTuple],
    ) -> Iterator[T | tuple[T, ...]]: ...
    def get_dtype_iter(self, dtypes):
        """Get next values as types in ``dtypes``.

        Parameters
        ----------
        dtypes
            Types of data to read.

        Yields
        ------
        :
            Loaded data.
        """
        for dtype in dtypes:
            yield self.get(dtype)

    @overload
    def get_dtype_dict(self, dtypes: Mapping[K, type[T]]) -> dict[K, T]: ...
    @overload
    def get_dtype_dict(self, dtypes: Mapping[K, ToTypeTuple]) -> dict[K, tuple[T, ...]]: ...
    @overload
    def get_dtype_dict(
        self,
        dtypes: Mapping[K, type[T] | ToTypeTuple],
    ) -> dict[K, T | tuple[T, ...]]: ...
    def get_dtype_dict(self, dtypes: Mapping[K, type[T] | ToTypeTuple]):
        """Get from a dictionary of dtypes to read.

        Parameters
        ----------
        dtypes
            Dictionary mapping key names to dtype to read.

        Returns
        -------
        :
            Loaded data.
        """
        return {
            key: parse_bytes(datum, typ)
            for (key, typ), datum in zip(dtypes.items(), self, strict=False)
        }
