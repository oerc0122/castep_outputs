"""
Convenient filewrapper class.
"""
from io import StringIO
from typing import List, TextIO, Union, NoReturn


class FileWrapper:
    """
    Convenience file wrapper to add rewind and line number capabilities.

    Parameters
    ----------
    file : ~typing.TextIO
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
            raise StopIteration()
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
        return self.file.name if hasattr(self.file, 'name') else 'unknown'


class Block:
    """
    Data block class returned from :func:`get_block`.

    Emulates the properties of both a file, and sequence.
    """
    def __init__(self, parent: Union[TextIO, FileWrapper, "Block"]):
        if isinstance(parent, (FileWrapper, Block)):
            self._lineno = parent.lineno

        self._name = parent.name if hasattr(parent, 'name') else 'unknown'
        self._i = -1
        self._data = []

    def remove_bounds(self, fore: int = 1, back: int = 2):
        """
        Remove the bounding lines of the block.

        These are often region delimiters and not
        relevant to the processed data.

        Parameters
        ----------
        fore : bool
            Whether to strip leading line from data.
        back : bool
            Whether to strip trailing line from data.
        """
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

    def aslist(self) -> List[str]:
        """
        Return block as a list of lines.

        Returns
        -------
        list[str]
            Block as list of lines.
        """
        return self._data

    def rewind(self):
        """
        Rewind file to previous line.

        Useful for blocks not terminated by a clear
        statement, where we can only check if next line
        does *NOT* match.
        """
        self._i -= 1

    def __bool__(self):
        return bool(self._data)

    def __add__(self, other: str):
        self._data.append(other.strip("\n"))
        return self

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

    def __getitem__(self, key: Union[int, slice]):
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
