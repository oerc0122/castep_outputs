from contextlib import closing
from functools import singledispatchmethod
from pathlib import Path
from typing import Sequence
from os import SEEK_SET, SEEK_CUR


class FortranUnformattedReader():
    def __init__(self, file: str | Path, labels: Sequence[str] = None):
        self.file = Path(file)
        self._indices = None

        if labels is not None:
            self.label(labels)
        else:
            self._labelled_indices = None

    def __del__(self):
        if hasattr(self, "_file_handle"):
            self._file_handle.close()

    def __enter__(self):
        self._file_handle = open(self.file, 'rb')
        return self._file_handle

    def __exit__(self, exception_type, exception_value, traceback):
        self._file_handle.close()
        self._file_handle = None

    def index(self):
        indices = []
        with self.file.open('rb') as file:
            while to_read_b := file.read(4):
                to_read = int.from_bytes(to_read_b, "big")
                indices.append((file.tell(), to_read))
                file.seek(to_read + 4, SEEK_CUR)
        self._indices = tuple(indices)

    def reader(self):
        with self.file.open('rb') as file:
            while to_read_b := file.read(4):
                to_read = int.from_bytes(to_read_b, "big")
                data = file.read(to_read)
                file.seek(4, SEEK_CUR)  # Skip terminal record
                yield to_read, data

    def label(self, labels: Sequence[str]):
        if self._indices is None:
            self.index()

        self._labelled_indices = dict(zip(labels, self._indices))

    @singledispatchmethod
    def __getitem__(self, ind: int):
        if not self._indices:
            self.index()

        if self._file_handle is None:
            file = closing(self.file.open('rb'))
        else:
            file = self._file_handle

        to_read, to_seek = self._indices[ind]

        file.seek(to_seek, SEEK_SET)
        return file.read(to_read)

    @__getitem__.register
    def _(self, ind: str):
        if not self._labelled_indices:
            raise KeyError("No labels supplied")

        if self._file_handle is None:
            file = closing(self.file.open('rb'))
        else:
            file = self._file_handle

        to_read, to_seek = self._labelled_indices[ind]

        file.seek(to_seek, SEEK_SET)
        return file.read(to_read)


if __name__ == "__main__":
    TEST_FILE = Path('~/CASTEP/castep/Test/Phonon/Si2-ep/Si2-ep.epme_bin').expanduser()
    data = FortranUnformattedReader(TEST_FILE)

    for record in data.reader():
        print(record)
