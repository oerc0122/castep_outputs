"""
Parse the following castep outputs:
.bands

"""
# pylint: disable=unused-argument

import re
from collections import defaultdict

from .utility import (fix_data_types, stack_dict, get_block, to_type, get_numbers,
                      labelled_floats, SPECIES_RE, INTNUMBER_RE, FNUMBER_RE,
                      SND_D)


# Regexp to identify block in .phonon or .phonon_dos file
FRACCOORDS_RE = re.compile(rf"\s*(?P<index>{INTNUMBER_RE}){labelled_floats(('u', 'v', 'w'))}"
                           rf"\s*(?P<spec>{SPECIES_RE}){labelled_floats(('mass',))}")

PHONON_PHONON_RE = re.compile(rf"""
    \s+q-pt=\s*{INTNUMBER_RE}\s*
    {labelled_floats(('qpt', 'pth'), counts=(3, 1))}
    """, re.VERBOSE)

PROCESS_PHONON_PHONON_RE = re.compile(labelled_floats(('n', 'f', 'Grad_qf')))


# Regexp to identify Fermi energies in .bands file
CASTEP_BANDS_FERMI_RE = re.compile(r"Fermi energ(ies|y) \(in atomic units\)\s*" +
                                   labelled_floats(('a', 'b')))

# Regexp to identify eigenvalue block in .bands file
# CASTEP_BANDS_EIGENS_RE =
# rf"K-point\s+(\d+)\s*(\s*{FNUMBER_RE})\s*({FNUMBER_RE})\s*({FNUMBER_RE})\s*({FNUMBER_RE})"


def parse_regular_header(block, extra_opts=tuple()):
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

        elif match := FRACCOORDS_RE.match(line):
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


def parse_hug_file(hug_file, verbose=False):
    """ Parse castep .hug file """

    cols = ('compression', 'temperature', 'pressure', 'energy')
    data = defaultdict(list)
    for line in hug_file:
        if match := re.search(labelled_floats(cols), line):
            stack_dict(data, match.groupdict())

    fix_data_types(data, {dt: float for dt in cols})
    return data


def parse_bands_file(bands_file, verbose=False):
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

        elif re.match(rf"^\s*{FNUMBER_RE}$", line.strip()):
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


def parse_phonon_dos_file(phonon_dos_file, verbose=False):
    """ Parse castep .phonon_dos file """
    # pylint: disable=too-many-branches,redefined-outer-name
    phonon_dos_info = defaultdict(list)
    for line in phonon_dos_file:
        if block := get_block(line, phonon_dos_file, "BEGIN header", "END header"):
            data = parse_regular_header(block)
            phonon_dos_info.update(data)

        elif block := get_block(line, phonon_dos_file, "BEGIN GRADIENTS", "END GRADIENTS"):
            if verbose:
                print("Found gradient block")
            qdata = defaultdict(list)

            def fix(qdat):
                fix_data_types(qdat, {'qpt': float,
                                      'pth': float,
                                      'n': int,
                                      'f': float,
                                      'Grad_qf': float})

            for line in block:
                if match := PHONON_PHONON_RE.match(line):
                    if qdata:
                        fix(qdata)
                        phonon_dos_info['gradients'].append(qdata)
                    qdata = defaultdict(list)

                    for key, val in match.groupdict().items():
                        qdata[key] = val.split()

                elif match := PROCESS_PHONON_PHONON_RE.match(line):
                    stack_dict(qdata, match.groupdict())

            if qdata:
                fix(qdata)
                phonon_dos_info['gradients'].append(qdata)

        elif block := get_block(line, phonon_dos_file, "BEGIN DOS", "END DOS", out_fmt=list):
            if verbose:
                print("Found DOS block")

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


def parse_efield_file(efield_file, verbose=False):
    """ Parse castep .efield file """
    # pylint: disable=too-many-branches,redefined-outer-name

    efield_info = defaultdict(list)

    for line in efield_file:
        if block := get_block(line, efield_file, "BEGIN header", "END header"):
            data = parse_regular_header(block, ('Oscillator Q',))
            efield_info.update(data)

        elif block := get_block(line, efield_file, "BEGIN Oscillator Strengths",
                                "END Oscillator Strengths",
                                out_fmt=list):
            if verbose:
                print("Found Oscillator Strengths")

            osc = defaultdict(list)
            for line in block[1:-2]:
                match = re.match(rf"\s*(?P<freq>{INTNUMBER_RE})" +
                                 labelled_floats([*(f'S{d}' for d in SND_D)]), line)
                stack_dict(osc, match.groupdict())

            if osc:
                fix_data_types(osc, {'freq': float,
                                     **{f'S{d}': float for d in SND_D}})
                efield_info['oscillator_strengths'].append(osc)

        elif block := get_block(line, efield_file, "BEGIN permittivity", "END permittivity",
                                out_fmt=list):
            if verbose:
                print("Found permittivity")

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


def parse_xrd_sf_file(xrd_sf_file, verbose=False):
    """ Parse castep .xrd_sf file """

    # Get headers from first line
    headers = xrd_sf_file.readline().split()[3:]
    # Turn Re(x) into x_re
    headers = [(head[3:-1]+"_"+head[0:2]).lower() for head in headers]

    xrd_re = re.compile(rf"(?P<qvec>(?:\s*{INTNUMBER_RE}){{3}})" +
                        labelled_floats(headers))

    xrd = defaultdict(list)
    for line in xrd_sf_file:
        match = xrd_re.match(line)
        stack_dict(xrd, match.groupdict())

    if xrd:
        xrd["qvec"] = [[*map(int, qvec)] for x in xrd["qvec"] if (qvec := x.split())]
        fix_data_types(xrd, {head: float for head in headers})

    return xrd


def parse_kpt_info(inp, prop):
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


def parse_elf_fmt_file(elf_file, verbose=True):
    """ Parse castep .elf_fmt files """
    return parse_kpt_info(elf_file, 'chi')


def parse_chdiff_fmt_file(chdiff_file, verbose=True):
    """ Parse castep .chdiff_fmt files """
    return parse_kpt_info(chdiff_file, 'chdiff')


def parse_pot_fmt_file(pot_file, verbose=True):
    """ Parse castep .pot_fmt files """
    return parse_kpt_info(pot_file, 'pot')


def parse_den_fmt_file(den_file, verbose=True):
    """ Parse castep .den_fmt files """
    return parse_kpt_info(den_file, 'density')
