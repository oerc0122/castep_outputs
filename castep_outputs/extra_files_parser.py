"""
Parse the following castep outputs:
.bands

"""
from typing import TextIO, Sequence, Dict, Union, List, Any
import re
from collections import defaultdict

from . import castep_res as REs
from .castep_res import get_block, get_numbers, labelled_floats, ATDATTAG, TAG_RE
from .constants import FST_D, SND_D, TAG_ALIASES, TS_TYPES
from .utility import (fix_data_types, stack_dict, to_type, log_factory, atreg_to_index,
                      add_aliases)


def parse_regular_header(block: TextIO,
                         extra_opts: Sequence[str] = tuple()) -> Dict[str, Union[float, int]]:
    """ Parse (semi-)standard castep file header block (given as iterable over lines) """

    data = {}
    coords = defaultdict(list)
    for line in block:

        if line.strip().startswith("Number of"):
            _, _, *key, val = line.split()
            data[" ".join(key)] = int(float(val))
        elif "Unit cell vectors" in line:
            data['unit_cell'] = [to_type(next(line).split(), float)
                                 for _ in range(3)]

        elif match := REs.FRACCOORDS_RE.match(line):
            stack_dict(coords, match.groupdict())

        elif match := re.search(f"({'|'.join(extra_opts)})", line):
            data[match.group(0)] = to_type(get_numbers(line), float)

    fix_data_types(coords, {'index': int,
                            'u': float,
                            'v': float,
                            'w': float,
                            'mass': float})
    data['coords'] = coords
    return data


def parse_hug_file(hug_file: TextIO) -> Dict[str, List[float]]:
    """ Parse castep .hug file """

    cols = ('compression', 'temperature', 'pressure', 'energy')
    data = defaultdict(list)
    for line in hug_file:
        if match := re.search(labelled_floats(cols), line):
            stack_dict(data, match.groupdict())

    fix_data_types(data, {dt: float for dt in cols})
    return data


def parse_bands_file(bands_file: TextIO) -> Dict[str, Any]:
    """ Parse castep .bonds file """

    bands_info = defaultdict(list)
    qdata = {}
    for line in bands_file:
        if block := get_block(line, bands_file, "BEGIN header", "END header"):

            data = parse_regular_header(block)
            bands_info.update(data)

        elif line.startswith("K-point"):
            if qdata:
                fix_data_types(qdata, {'qpt': float,
                                       'weight': float,
                                       'spin_comp': int,
                                       'band': float
                                       })
                bands_info['bands'].append(qdata)
            _, _, *qpt, weight = line.split()
            qdata = {'qpt': qpt, 'weight': weight, 'spin_comp': None, 'band': []}

        elif line.startswith("Spin component"):
            qdata['spin_comp'] = line.split()[2]
            if qdata['spin_comp'] != "1":
                qdata['band_up'] = qdata.pop('band')

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
                               'band_dn': float
                               })
        bands_info['bands'].append(qdata)

    return bands_info


def parse_phonon_dos_file(phonon_dos_file: TextIO) -> Dict[str, Any]:
    """ Parse castep .phonon_dos file """
    # pylint: disable=too-many-branches,redefined-outer-name
    logger = log_factory(phonon_dos_file)
    phonon_dos_info = defaultdict(list)

    for line in phonon_dos_file:
        if block := get_block(line, phonon_dos_file, "BEGIN header", "END header"):
            data = parse_regular_header(block)
            phonon_dos_info.update(data)

        elif block := get_block(line, phonon_dos_file, "BEGIN GRADIENTS", "END GRADIENTS"):

            logger("Found gradient block")
            qdata = defaultdict(list)

            def fix(qdat):
                fix_data_types(qdat, {'qpt': float,
                                      'pth': float,
                                      'n': int,
                                      'f': float,
                                      'Grad_qf': float})

            for line in block:
                if match := REs.PHONON_PHONON_RE.match(line):
                    if qdata:
                        fix(qdata)
                        phonon_dos_info['gradients'].append(qdata)
                    qdata = defaultdict(list)

                    for key, val in match.groupdict().items():
                        qdata[key] = val.split()

                elif match := REs.PROCESS_PHONON_PHONON_RE.match(line):
                    stack_dict(qdata, match.groupdict())

            if qdata:
                fix(qdata)
                phonon_dos_info['gradients'].append(qdata)

        elif block := get_block(line, phonon_dos_file, "BEGIN DOS", "END DOS", out_fmt=list):

            logger("Found DOS block")

            dos = defaultdict(list)
            for line in block[1:-2]:
                match = re.match(labelled_floats(('freq', 'g', 'si')), line)
                stack_dict(dos, match.groupdict())

            if dos:
                fix_data_types(dos, {'freq': float,
                                     'g': float,
                                     'si': float})
                phonon_dos_info['dos'].append(dos)

    return phonon_dos_info


def parse_efield_file(efield_file: TextIO) -> Dict[str, Union[float, int]]:
    """ Parse castep .efield file """
    # pylint: disable=too-many-branches,redefined-outer-name

    efield_info = defaultdict(list)
    logger = log_factory(efield_file)

    for line in efield_file:
        if block := get_block(line, efield_file, "BEGIN header", "END header"):
            data = parse_regular_header(block, ('Oscillator Q',))
            efield_info.update(data)

        elif block := get_block(line, efield_file, "BEGIN Oscillator Strengths",
                                "END Oscillator Strengths",
                                out_fmt=list):

            logger("Found Oscillator Strengths")

            osc = defaultdict(list)
            for line in block[1:-2]:
                match = re.match(rf"\s*(?P<freq>{REs.INTNUMBER_RE})" +
                                 labelled_floats([*(f'S{d}' for d in SND_D)]), line)
                stack_dict(osc, match.groupdict())

            if osc:
                fix_data_types(osc, {'freq': float,
                                     **{f'S{d}': float for d in SND_D}})
                efield_info['oscillator_strengths'].append(osc)

        elif block := get_block(line, efield_file, "BEGIN permittivity", "END permittivity",
                                out_fmt=list):

            logger("Found permittivity")

            perm = defaultdict(list)
            for line in block[1:-2]:
                match = re.match(labelled_floats(['freq',
                                                  *(f'e_r_{d}' for d in SND_D)]), line)
                stack_dict(perm, match.groupdict())

            if perm:
                fix_data_types(perm, {'freq': float,
                                      **{f'e_r_{d}': float for d in SND_D}})
                efield_info['permittivity'].append(perm)

    return efield_info


def parse_xrd_sf_file(xrd_sf_file: TextIO) -> Dict[str, Union[int, float]]:
    """ Parse castep .xrd_sf file """

    # Get headers from first line
    headers = xrd_sf_file.readline().split()[3:]
    # Turn Re(x) into x_re
    headers = [(head[3:-1]+"_"+head[0:2]).lower() for head in headers]

    xrd_re = re.compile(rf"(?P<qvec>(?:\s*{REs.INTNUMBER_RE}){{3}})" +
                        labelled_floats(headers))

    xrd = defaultdict(list)
    for line in xrd_sf_file:
        match = xrd_re.match(line)
        stack_dict(xrd, match.groupdict())

    if xrd:
        xrd["qvec"] = [[*map(int, qvec)] for x in xrd["qvec"] if (qvec := x.split())]
        fix_data_types(xrd, {head: float for head in headers})

    return xrd


def parse_elastic_file(elastic_file: TextIO) -> Dict[str, List[List[float]]]:
    """ Parse castep .elastic files """
    accum = defaultdict(list)

    for line in elastic_file:
        if block := get_block(line, elastic_file,
                              "^BEGIN Elastic Constants",
                              "^END Elastic Constants"):

            accum["elastic_constants"] = [to_type(numbers, float)
                                          for blk_line in block
                                          if (numbers := get_numbers(blk_line))]

        elif block := get_block(line, elastic_file,
                                "^BEGIN Compliance Matrix",
                                "^END Compliance Matrix"):
            next(block)  # Skip Begin line w/units

            accum["compliance_matrix"] = [to_type(numbers, float)
                                          for blk_line in block
                                          if (numbers := get_numbers(blk_line))]

    return accum


def parse_ts_file(ts_file: TextIO) -> Dict[str, Any]:
    """ Parse castep .ts files """

    accum = defaultdict(list)

    for line in ts_file:
        if "TSConfirmation" in line:
            accum["confirmation"] = True

        elif block := get_block(line, ts_file, "(REA|PRO|TST)", r"^\s*$", eof_possible=True):
            curr = defaultdict(list)
            match = re.match(r"\s*(?P<type>REA|PRO|TST)\s*\d+\s*" +
                             labelled_floats(('reaction_coordinate',)), line)
            key = TS_TYPES[match["type"]]
            curr["reaction_coordinate"] = to_type(match["reaction_coordinate"], float)

            for blk_line in block:
                if match := ATDATTAG.search(blk_line):
                    ion = atreg_to_index(match)
                    if ion not in curr:
                        curr[ion] = {}
                    curr[ion][match.group('tag')] = to_type([*(match.group(d)
                                                               for d in FST_D)], float)
                    add_aliases(curr[ion], TAG_ALIASES)

                elif match := TAG_RE.search(blk_line):
                    curr[match.group('tag')].append([*to_type(get_numbers(blk_line), float)])

            add_aliases(curr, TAG_ALIASES)
            accum[key].append(curr)

    return accum


def parse_kpt_info(inp: TextIO, prop: str) -> Dict[str, List[Union[int, float]]]:
    """ Parse standard form of kpt related .*_fmt files """

    # Skip header
    while "END header" not in inp.readline():
        pass

    qdata = defaultdict(list)
    for line in inp:
        if not line.strip():
            continue
        *qpt, val = line.split()
        qpt = to_type(qpt, int)
        val = to_type(val, float)
        stack_dict(qdata, {'q': qpt, prop: val})

    return qdata


def parse_elf_fmt_file(elf_file: TextIO) -> Dict[str, List[Union[int, float]]]:
    """ Parse castep .elf_fmt files """
    return parse_kpt_info(elf_file, 'chi')


def parse_chdiff_fmt_file(chdiff_file: TextIO) -> Dict[str, List[Union[int, float]]]:
    """ Parse castep .chdiff_fmt files """
    return parse_kpt_info(chdiff_file, 'chdiff')


def parse_pot_fmt_file(pot_file: TextIO) -> Dict[str, List[Union[int, float]]]:
    """ Parse castep .pot_fmt files """
    return parse_kpt_info(pot_file, 'pot')


def parse_den_fmt_file(den_file: TextIO) -> Dict[str, List[Union[int, float]]]:
    """ Parse castep .den_fmt files """
    return parse_kpt_info(den_file, 'density')
