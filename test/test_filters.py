"""Test filters work as expected."""

from pathlib import Path

import pytest

from castep_outputs import parse_castep_file
from castep_outputs.parsers.castep_file_parser import Filters

_DATA_FOLDER = Path(__file__).parent / "data_files"
_TEST_FILE = _DATA_FOLDER / "test.castep"

@pytest.mark.parametrize("filters,keys", (
    (Filters.CELL, {"initial_cell"}),
    (Filters.PARAMETERS, {"title", "options", "initial_spins", "k-points", "target_stress"}),
    (Filters.POSITION, {"initial_positions"}),
    (Filters.PSPOT, {"pspot_detail"}),
    (Filters.SPECIES_PROPS, {"species_properties"}),
    (Filters.SYMMETRIES, {"symmetries", "constraints"}),
    (Filters.SYS_INFO, {"build_info", "time_started", "warning", "memory_estimate"}),
    (Filters.LOW, {"species_properties", "initial_cell", "initial_positions"}),
    (Filters.MEDIUM, {"species_properties", "title", "options", "initial_cell",
                      "initial_positions", "initial_spins", "k-points", "target_stress"}),
    (Filters.HIGH, {"build_info", "time_started", "warning", "pspot_detail",
                    "species_properties", "title", "options",
                    "initial_cell", "initial_positions", "initial_spins", "k-points",
                    "symmetries", "constraints", "target_stress", "memory_estimate"}),
    (Filters.FULL, {"build_info", "time_started", "warning", "pspot_detail",
                    "species_properties", "title", "options", "initial_cell",
                    "initial_positions", "initial_spins", "k-points", "symmetries",
                    "constraints", "target_stress", "memory_estimate"}),
    (Filters.TESTING, {"pspot_detail", "species_properties", "initial_cell", "initial_positions"}),
))
def test_filter_all(filters, keys):
    with _TEST_FILE.open("r", encoding="utf-8") as file:
        data = parse_castep_file(file, filters=filters)
    assert keys <= data[0].keys()

def test_filter_none():
    with _TEST_FILE.open("r", encoding="utf-8") as file:
        data = parse_castep_file(file, filters=Filters.NONE)
    assert not data


if __name__ == "__main__":
    pytest.main()
