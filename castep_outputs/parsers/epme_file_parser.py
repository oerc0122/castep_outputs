"""Parse castep .epme files."""

from __future__ import annotations

from typing import TextIO, TypedDict

from ..utilities.castep_res import get_numbers
from ..utilities.datatypes import ThreeVector
from ..utilities.utility import file_or_path, log_factory, to_type


class EPMEData(TypedDict):
    """Single line of EPME data."""

    # Initial k-point
    kpt_i: ThreeVector
    # Final k-point
    kpt_f: ThreeVector
    # Branch index.
    ph_index: int
    # Initial band.
    band_i: int
    # Final band.
    band_f: int
    # Phonon frequency.
    freq: float
    # Initial energy.
    e_i: float
    # Final Energy.
    e_f: float
    # Velocities.
    velocity: tuple[ThreeVector, ThreeVector]
    # Matrix element.
    e_p_matrix: complex


class EPMEFileInfo(TypedDict):
    """Full EPME file data."""

    # File version.
    version: int
    # Unit cell volume.
    volume: float
    # Fermi energy.
    fermi_energy: float
    # Number of bands.
    n_bands: int
    # Number of phonon branches.
    n_branches: int
    # EPME data.
    data: list[EPMEData]


def _parse_epme_header(epme_file: TextIO) -> EPMEFileInfo:
    """Read header and prepare EPME output dictionary.

    Parameters
    ----------
    epme_file : TextIO
        File to parse.

    Returns
    -------
    EPMEFileInfo
        Prepared EPME data with header.
    """
    epme_data: EPMEFileInfo = {}
    next(epme_file)  # Title
    epme_data["version"] = int(next(epme_file).rsplit(maxsplit=1)[1])
    next(epme_file)  # Units
    epme_data["volume"] = float(next(epme_file).rsplit(maxsplit=1)[1])
    epme_data["fermi_energy"] = float(next(epme_file).rsplit(maxsplit=1)[1])
    epme_data["n_bands"] = int(next(epme_file).rsplit(maxsplit=1)[1])
    epme_data["n_branches"] = int(next(epme_file).rsplit(maxsplit=1)[1])
    epme_data["data"] = []

    return epme_data


@file_or_path(mode="r")
def parse_epme_file(epme_file: TextIO) -> EPMEFileInfo:
    """Parse castep .epme file.

    Parameters
    ----------
    epme_file
        A handle to a CASTEP .epme file.

    Returns
    -------
    EPMEFileInfo
        Parsed data.
    """
    logger = log_factory(epme_file)

    epme_data: EPMEFileInfo = _parse_epme_header(epme_file)
    kpt_i, kpt_f = None, None

    for line in epme_file:
        if line.startswith("Electron-Phonon coupling"):
            kpts = to_type(get_numbers(line), float)
            kpt_i, kpt_f = kpts[:3], kpts[3:]
            logger("Found k-point pair: %s -> %s", kpt_i, kpt_f)
            next(epme_file)  # Skip header
            continue
        data = line.split()
        curr = {"kpt_i": kpt_i, "kpt_f": kpt_f}
        curr["ph_index"], curr["band_i"], curr["band_f"] = to_type(data[:3], int)
        curr["e_i"], curr["e_f"] = to_type(data[3:5], float)
        curr["velocity"] = to_type(data[5:8], float), to_type(data[8:11], float)
        curr["e_p_matrix"] = complex(*to_type(data[11:13], float))
        epme_data["data"].append(curr)

    return epme_data
