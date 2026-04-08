"""Test reading binary files."""

from __future__ import annotations

from pathlib import Path

import pytest
from dump_fortran_unformatted import data_types, fake_file, raw_data, to_bytes

from castep_outputs.bin_parsers.fortran_bin_parser import FortranBinaryReader
from castep_outputs.utilities.utility import to_type

DATA_FILES = Path(__file__).parent / "data_files"
DEFAULT_SAMPLE = (1, 2, 3, 2, 3.1, "Hello", (1.0, 3.0, 6.0))


@pytest.mark.parametrize("fake_file", [(1,)], indirect=True)
def test_reader_get(fake_file):
    reader = FortranBinaryReader(fake_file)
    assert reader.get(int) == 1


@pytest.mark.parametrize("fake_file", [(1, 2, 3, 2)], indirect=True)
def test_reader_get_iter(fake_file):
    reader = FortranBinaryReader(fake_file)
    assert list(reader.get_dtype_iter((int, int, int, int))) == [1, 2, 3, 2]


@pytest.mark.parametrize("fake_file", [(2, 3.1, "Hello")], indirect=True)
def test_reader_get_dict(fake_file):
    reader = FortranBinaryReader(fake_file)
    assert reader.get_dtype_dict({"x": int, "y": float, "z": str}) == {
        "x": 2,
        "y": 3.1,
        "z": "Hello",
    }


@pytest.mark.parametrize("fake_file", [(1, 2, 3, 2)], indirect=True)
def test_reader_get_cycle(fake_file):
    reader = FortranBinaryReader(fake_file)
    x = reader.get_dtype_cycle((int, int))
    assert next(x) == (1, 2)
    assert next(x) == (3, 2)


@pytest.mark.parametrize(
    "fake_file, data_types, raw_data",
    [
        (DEFAULT_SAMPLE,) * 3,
    ],
    indirect=True,
)
def test_binary_file_reader(fake_file, data_types, raw_data):
    """Test reading a generic "file"."""
    reader = FortranBinaryReader(fake_file)

    for datum, typ, expected in zip(reader, data_types, raw_data):
        assert to_type(datum, typ) == expected


def test_actual_read():
    """Test reading a castep `.cst_esp` file elements."""
    dtypes = ((int, 1), (int, (16, 16, 16)))

    with (DATA_FILES / "test.cst_esp").open("rb") as file:
        reader = FortranBinaryReader(file)
        for (typ, expected) in dtypes:
            assert reader.get(typ) == expected

        for n, datum in enumerate(reader):
            x, y = divmod(n, 16)
            ind = to_type(datum[:8], int)
            print(ind, (x + 1, y + 1))
            assert ind == (x + 1, y + 1)  # 1 indexed
            res = to_type(datum[8:], complex)
            assert len(res) == dtypes[1][1][2]


@pytest.mark.parametrize(
    "fake_file, raw_data",
    [
        (DEFAULT_SAMPLE,) * 2,
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "forward, skip, index",
    [
        (1, 3, 4),
        (3, -2, 1),
        (2, -1, 1),
        (2, 0, 2),
    ],
)
def test_rewind(fake_file, raw_data, forward, skip, index):
    """Test rewind functionality of raw_file_reader."""
    reader = FortranBinaryReader(fake_file)

    for i, val in zip(range(forward), reader):
        assert to_bytes(raw_data[i]) == val

    reader.skip(skip)
    assert to_bytes(raw_data[index]) == next(reader)


if __name__ == "__main__":
    pytest.main()
