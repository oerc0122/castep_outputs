"""
Convenient filewrapper class
"""

from typing import TextIO


class FileWrapper:
    """
    Convenience file wrapper to add rewind and line number capabilities
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
        """Rewinds file to previous line"""
        if self.file.tell() == self._pos:
            return
        self._lineno -= 1
        self.file.seek(self._pos)

    @property
    def file(self):
        """File wrapped by the filewrapper"""
        return self._file

    @property
    def lineno(self):
        """Current line number"""
        return self._lineno

    @property
    def name(self):
        """Name of underlying file"""
        return self.file.name if hasattr(self.file, 'name') else 'unknown'
