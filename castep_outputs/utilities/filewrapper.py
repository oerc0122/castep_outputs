"""Convenient filewrapper class."""
from __future__ import annotations

import re
from collections.abc import Sequence
from io import StringIO
from typing import NoReturn, TextIO

from .castep_res import Pattern


class FileWrapper:
    """
    Convenience file wrapper to add rewind and line number capabilities.

    Parameters
    ----------
    file
        File to wrap and control.
    """

    def __init__(self, file: TextIO):
        self._file = file
        self._pos = 0
        self._lineno = 0

    def __iter__(self):
        return self

    def __next__(self):
        self._lineno += 1
        self._pos = self.file.tell()
        nextline = self.file.readline()
        if not nextline:
            raise StopIteration
        return nextline

    def rewind(self):
        """
        Rewind file to previous line.

        If iterated by `next` (or `for`) can rewind
        one line.

        Useful for blocks not terminated by a clear
        statement, where we can only check if next line
        does *NOT* match.
        """
        if self.file.tell() == self._pos:
            return
        self._lineno -= 1
        self.file.seek(self._pos)

    @property
    def file(self) -> TextIO:
        """
        File handle wrapped by the filewrapper.

        Returns
        -------
        ~typing.TextIO
            Underlying file.
        """
        return self._file

    @property
    def lineno(self) -> int:
        """
        Current line number.

        Returns
        -------
        int
            Current line number in file.
        """
        return self._lineno

    @property
    def name(self):
        """
        Name of underlying file.

        Returns
        -------
        str
            Name if name is known otherwise "unknown".
        """
        return self.file.name if hasattr(self.file, "name") else "unknown"


class Block:
    """
    Data block class returned from :func:`get_block`.

    Emulates the properties of both a file, and sequence.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, parent: TextIO | FileWrapper | Block | None):
        if isinstance(parent, (FileWrapper, Block)):
            self._lineno = parent.lineno
        else:
            self._lineno = 0

        self._name = parent.name if hasattr(parent, "name") else "unknown"
        self._i = -1
        self._data: tuple[str, ...] = ()

    @classmethod
    def get_lines(
            cls,
            in_file: TextIO | FileWrapper | Block,
            n_lines: int,
            *,
            eof_possible: bool = False,
    ) -> Block:
        r"""
        Read the next `n_lines` from `in_file` and return the block.

        Parameters
        ----------
        in_file
            File to read data from.
        n_lines
            Number of lines to read.

        Returns
        -------
        Block
            Read data.

        Raises
        ------
        IOError
            If EOF reached and ``not eof_possible``.

        Examples
        --------
        >>> from io import StringIO
        >>> x = StringIO('Hello\nThere\nFriend')
        >>> block = Block.get_lines(x, 2)
        >>> type(block).__name__
        'Block'
        >>> block.aslist()
        ['Hello\n', 'There\n']
        """
        block = cls(in_file)

        data: list[str] = []
        for i, line in enumerate(in_file, 1):
            if i > n_lines:
                break
            data.append(line)
        else:
            if not eof_possible:
                if hasattr(in_file, "name"):
                    raise OSError(f"Unexpected end of file in {in_file.name}.")
                raise OSError("Unexpected end of file.")

        block._data = tuple(data)
        return block

    @classmethod
    def from_re(
            cls,
            init_line: str,
            in_file: TextIO | FileWrapper | Block,
            start: Pattern,
            end: Pattern,
            *,
            n_end: int = 1,
            eof_possible: bool = False,
    ) -> Block:
        """
        Check if line is the start of a block and return the block if it is.

        Parameters
        ----------
        init_line
            Initial line which may start the block.
        in_file
            File handle to read data from.
        start
            RegEx matched against `init_line` to see if is start of block.
        end
            RegEx to verify if block has ended.
        n_end
            Number of times `end` must match before block is returned.
        eof_possible
            Whether it is possible block is ended by EOF.

        Returns
        -------
        Block
            Recovered block of data matching prereqs.

        Notes
        -----
        Advances `in_file` as it does so.

        Raises
        ------
        IOError
            If EOF reached and ``not eof_possible``.
        """
        block = cls(in_file)

        if not re.search(start, init_line):
            # Return empty block. (bool -> False)
            return block

        data: list[str] = []
        data.append(init_line)

        found = 0
        for line in in_file:
            data.append(line)
            if re.search(end, line):
                found += 1
                if found == n_end:
                    break
        else:
            if not eof_possible:
                if hasattr(in_file, "name"):
                    raise OSError(f"Unexpected end of file in {in_file.name}.")
                raise OSError("Unexpected end of file.")

        block._data = tuple(data)
        return block

    @classmethod
    def from_iterable(
            cls,
            data: Sequence[str],
            parent: TextIO | FileWrapper | Block | None = None):
        r"""
        Construct a Block from an iterable containing strings.

        Parameters
        ----------
        data
            Data to read into block.

        Examples
        --------
        >>> x = Block.from_iterable(("Hello", "There"))
        >>> type(x).__name__
        'Block'
        >>> str(x)
        'Hello\nThere'
        """
        block = cls(parent)
        block._data = tuple(data)
        return block

    def remove_bounds(self, /, fore: int = 1, back: int = 2):
        """
        Remove the bounding lines of the block.

        These are often region delimiters and not
        relevant to the processed data.

        Parameters
        ----------
        fore
            Whether to strip leading line from data.
        back
            Whether to strip trailing line from data.
        """
        self._lineno += fore
        self._data = self._data[fore:
                                -back if back else None]

    def asstringio(self) -> StringIO:
        """
        Return block as a simulated file.

        Returns
        -------
        ~io.StringIO
            Block data as StringIO
        """
        return StringIO(str(self))

    def aslist(self) -> list[str]:
        """
        Return block as a list of lines.

        Returns
        -------
        list[str]
            Block as list of lines.
        """
        return list(self._data)

    def rewind(self):
        """
        Rewind to previous line.

        Useful for blocks not terminated by a clear
        statement, where we can only check if next line
        does *NOT* match.
        """
        if self._i < 0:
            self._i = -1
            raise ValueError("Block already at beginning.")

        self._i -= 1

    def __bool__(self):
        return any(map(str.strip, self._data))

    def __str__(self):
        return "\n".join(self._data)

    def __iter__(self):
        return self

    def __next__(self):
        self._i += 1
        if self._i >= len(self):
            raise StopIteration
        return self._data[self._i]

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, key: int | slice):
        return self._data[key]

    @property
    def name(self) -> str:
        """
        Name of underlying file.

        Returns
        -------
        str
            Name if name is known otherwise "unknown".
        """
        return self._name

    @property
    def lineno(self) -> int:
        """
        Current line number.

        Returns
        -------
        int
            Current line number in file.
        """
        return self._lineno + self._i

    @property
    def file(self) -> NoReturn:
        """
        Block has no internal file.

        Raises
        ------
        NotImplementedError
            Block has no internal file holder.
        """
        raise NotImplementedError("Block has no internal file holder.")
