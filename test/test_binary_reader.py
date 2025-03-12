"""Test reading binary files."""
from __future__ import annotations

from pathlib import Path

import pytest
from dump_fortran_unformatted import data_types, fake_file, raw_data, to_bytes

from castep_outputs.bin_parsers.fortran_bin_parser import binary_file_reader
from castep_outputs.utilities.utility import to_type

DATA_FILES = Path(__file__).parent / "data_files"
DEFAULT_SAMPLE = (1, 2, 3, 2, 3.1, "Hello", (1., 3., 6.))


@pytest.mark.parametrize("fake_file, data_types, raw_data", [
    (DEFAULT_SAMPLE,)*3,
], indirect=True)
def test_binary_file_reader(fake_file, data_types, raw_data):
    """Test reading a generic "file"."""
    reader = binary_file_reader(fake_file)

    for datum, typ, expected in zip(reader, data_types, raw_data):
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

@pytest.mark.parametrize("fake_file, raw_data", [
    (DEFAULT_SAMPLE,)*2,
], indirect=True)
@pytest.mark.parametrize("forward, skip, index", [
    (2, True, 1),
    (1, 3, 4),
    (3, -2, 1),
    (2, -1, 1),
    (2, 0, 2),
])
def test_rewind(fake_file, raw_data, forward, skip, index):
    """Test rewind functionality of raw_file_reader."""
    reader = binary_file_reader(fake_file)

    for i, val in zip(range(forward), reader):
        assert to_bytes(raw_data[i]) == val

    result = reader.send(skip)
    assert to_bytes(raw_data[index]) == result


if __name__ == "__main__":
    pytest.main()
