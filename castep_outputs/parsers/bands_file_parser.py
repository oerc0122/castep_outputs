"""
Parse the following castep outputs:
.bands
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, TextIO

from ..utilities import castep_res as REs
from ..utilities.filewrapper import Block
from ..utilities.utility import fix_data_types
from .parse_utilities import parse_regular_header


def parse_bands_file(bands_file: TextIO) -> dict[str, Any]:
    """ Parse castep .bonds file """

    bands_info = defaultdict(list)
    qdata = {}

    block = Block.from_re("", bands_file, "", REs.THREEVEC_RE, n_end=3)
    data = parse_regular_header(block, ("Fermi energy",))
    bands_info.update(data)

    for line in bands_file:
        if line.startswith("K-point"):
            if qdata:
                fix_data_types(qdata, {'qpt': float,
                                       'weight': float,
                                       'spin_comp': int,
                                       'band': float,
                                       'band_up': float,
                                       'band_dn': float,
                                       })
                bands_info['bands'].append(qdata)
            _, _, *qpt, weight = line.split()
            qdata = {'qpt': qpt, 'weight': weight, 'spin_comp': None, 'band': []}

        elif line.startswith("Spin component"):
            qdata['spin_comp'] = line.split()[2]
            if qdata['spin_comp'] != "1":
                qdata['band_up'] = qdata.pop('band')
                if "band_dn" not in qdata:
                    qdata["band_dn"] = []

        elif re.match(rf"^\s*{REs.FNUMBER_RE}$", line.strip()):
            if qdata['spin_comp'] != "1":
                qdata['band_dn'].append(line)
            else:
                qdata['band'].append(line)

    if qdata:
        fix_data_types(qdata, {'qpt': float,
                               'weight': float,
                               'spin_comp': int,
                               'band': float,
                               'band_up': float,
                               'band_dn': float,
                               })
        bands_info['bands'].append(qdata)

    return bands_info
