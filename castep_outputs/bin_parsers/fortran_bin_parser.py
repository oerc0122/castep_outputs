"""General parser for the Fortran Unformatted file format."""
from os import SEEK_CUR
from typing import BinaryIO, Generator

FortranBinaryReader = Generator[bytes, int, None]

def binary_file_reader(file: BinaryIO) -> FortranBinaryReader:
    """Yield the elements of a Fortran unformatted file."""
    while bin_size := file.read(4):
        size = int.from_bytes(bin_size, "big")
        data = file.read(size)
        skip = yield data
        file.read(4)
        if skip:  # NB. Send proceeds to yield.
            # `True` implies rewind 1
            if skip < 0 or skip is True:
                for _ in range(abs(skip)):
                    # Rewind to record size before last read
                    file.seek(-size-12, SEEK_CUR)
                    size = int.from_bytes(file.read(4), "big")

                # Rewind one extra (which will be yielded)
                file.seek(-size-8, SEEK_CUR)
            else:
                for _ in range(skip):
                    size = int.from_bytes(file.read(4), "big")
                    file.seek(size+4, SEEK_CUR)
