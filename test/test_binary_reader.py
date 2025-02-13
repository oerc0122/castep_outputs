"""Test reading binary files."""
from pathlib import Path

import pytest
from dump_fortran_unformatted import to_unformat_file

from castep_outputs.bin_parsers.fortran_bin_parser import binary_file_reader
from castep_outputs.utilities.utility import to_type

DATA_FILES = Path(__file__).parent / "data_files"


def test_binary_file_reader():
    """Test reading a generic "file"."""
    sample = (1, 2, 3, 2, 3.1, "Hello", (1., 3., 6.))

    data, types = to_unformat_file(*sample), (*map(type, sample[:-1]), float)
    reader = binary_file_reader(data)

    for datum, typ, expected in zip(reader, types, sample):
        assert to_type(datum, typ) == expected


def test_actual_read():
    """Test reading a castep `.cst_esp` file elements."""
    dtypes = ((int, 1), (int, (16, 16, 16)))

    with (DATA_FILES / "test.cst_esp").open("rb") as file:
        reader = binary_file_reader(file)
        for (typ, expected), datum in zip(dtypes, reader):
            assert to_type(datum, typ) == expected

        for (n, datum) in enumerate(reader):
            x, y = divmod(n, 16)
            ind = to_type(datum[:8], int)
            assert ind == (x + 1, y + 1)  # 1 indexed
            res = to_type(datum[8:], complex)
            assert len(res) == dtypes[1][1][2]


if __name__ == "__main__":
    pytest.main()
