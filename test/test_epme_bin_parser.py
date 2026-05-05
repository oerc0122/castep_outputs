from castep_outputs.bin_parsers.fortran_bin_parser import FortranBinaryReader
import pytest
from dump_fortran_unformatted import fake_file
from castep_outputs.bin_parsers.epme_bin_parser import _parse_phonons


@pytest.mark.parametrize("fake_file", [("EPCOUPLING", 3, 4)], indirect=True)
@pytest.mark.parametrize(
    "accum, expected",
    [
        ({"n_kpoint_pairs": -1, "n_bands": 2}, "Number of kpoint pairs"),
        ({"n_kpoint_pairs": 3, "n_bands": -1}, "Number of bands"),
    ],
)
def test_epme_abort(fake_file, accum, expected):
    reader = FortranBinaryReader(fake_file)

    with pytest.raises(ValueError, match=expected):
        _parse_phonons(reader, accum)
