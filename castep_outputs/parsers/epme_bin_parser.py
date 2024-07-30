from pathlib import Path

from binary_file_parser import FortranUnformattedReader

def parse_epme_bin_file(epme_file_path: Path):
    data = FortranUnformattedReader(epme_file_path)

    labels = [record if record.isprintable() else "" for size, record in data.reader()]
    data.label(labels)
    print(data._labelled_indices)


if __name__ == "__main__":
    TEST_FILE = Path('~/CASTEP/castep/Test/Phonon/Si2-ep/Si2-ep.epme_bin').expanduser()
    parse_epme_bin_file(TEST_FILE)
