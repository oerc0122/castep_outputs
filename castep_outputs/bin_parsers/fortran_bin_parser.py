"""General parser for the Fortran Unformatted file format."""

from collections.abc import Iterable, Iterator, Mapping
from os import SEEK_CUR
from typing import BinaryIO, TypeVar

from castep_outputs.utilities.type_conv import parse_bytes

T = TypeVar("T")
K = TypeVar("K")


class FortranBinaryReader:
    """Yield the elements of a Fortran unformatted file.

    Parameters
    ----------
    file : BinaryIO
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
        n : int
            How many elements to rewind.
        """
        self.skip(-n)

    def skip(self, n: int, /) -> None:
        """Ignore the next ``n`` elements.

        Parameters
        ----------
        n : int
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

    def get(self, typ: type[T]) -> T:
        """Get next value as ``typ``.

        Parameters
        ----------
        typ : type[T]
            Type to retrieve.

        Returns
        -------
        T
            Value as type.
        """
        return parse_bytes(next(self), typ)

    # TypeVarTuple 3.11+
    def get_dtype_cycle(self, dtypes: tuple[type[T], ...]) -> Iterator[tuple[T, ...]]:
        """Get iterator over values reading dtypes each cycle.

        Parameters
        ----------
        dtypes : tuple[type[T], ...]
            Dtypes to load simultaneously.

        Yields
        ------
        tuple[T, ...]
            Loaded data.
        """
        while True:
            yield tuple(self.get(dtype) for dtype in dtypes)

    def get_dtype_iter(self, dtypes: Iterable[type[T]]) -> Iterator[T]:
        """Get next values as types in ``dtypes``.

        Parameters
        ----------
        dtypes : Iterable[type[T]]
            Types of data to read.

        Yields
        ------
        T
            Loaded data.
        """
        for dtype in dtypes:
            yield self.get(dtype)

    def get_dtype_dict(self, dtypes: Mapping[K, type[T]]) -> dict[K, T]:
        """Get from a dictionary of dtypes to read.

        Parameters
        ----------
        dtypes : dict[K, type[T]]
            Dictionary mapping key names to dtype to read.

        Returns
        -------
        dict[K, T]
            Loaded data.
        """
        accum: dict[K, T] = {}
        for (key, typ), datum in zip(dtypes.items(), self, strict=False):
            accum[key] = parse_bytes(datum, typ)

        return accum
