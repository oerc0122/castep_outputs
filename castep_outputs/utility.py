"""
Utility functions for parsing castep outputs
"""
import collections.abc
from collections import defaultdict
import itertools
import re
import json
import pprint
try:
    from ruamel import yaml
    _YAML_TYPE = "ruamel"
except ImportError:
    try:
        import yaml
        _YAML_TYPE = "yaml"
    except ImportError:
        _YAML_TYPE = None



def normalise_string(string):
    """
    Normalise a string removing leading/trailing space
    and making all spacing single-space
    """
    return " ".join(string.strip().split())


def atreg_to_index(dict_in, clear=True):
    """
    Transform a matched atreg value to species index tuple
    Also clear value from dictionary for easier processing
    """
    spec, ind = dict_in["spec"], dict_in["index"]

    if isinstance(dict_in, dict) and clear:
        del dict_in["spec"]
        del dict_in["index"]

    return (spec, int(ind))


def de_default_dict(obj):
    """
    Turns defaultdicts into regular dicts
    """
    obj_out = {}

    for key, val in obj.items():
        if isinstance(val, defaultdict):
            val = dict(val)
        if isinstance(val, dict):
            val = de_default_dict(val)
        elif isinstance(val, (tuple, list)):
            val = [de_default_dict(v) if isinstance(v, dict) else v for v in val]

        obj_out[key] = val

    return obj_out


def json_safe_dict(obj):
    """ Transform a castep_output dict into a JSON safe variant
    i.e. convert tuple keys to conjoined strings """
    obj_out = {}

    for key, val in obj.items():
        if isinstance(key, (tuple, list)):
            key = "_".join(map(str, key))
        if isinstance(val, dict):
            val = json_safe_dict(val)
        elif isinstance(val, (tuple, list)):
            val = [json_safe_dict(v) if isinstance(v, dict) else v for v in val]
        obj_out[key] = val
    return obj_out


def flatten_dict(dictionary, parent_key=False, separator='_'):
    """
    Turn a nested dictionary into a flattened dictionary

    Taken from:
    https://stackoverflow.com/a/62186053

    :param dictionary: The dictionary to flatten
    :param parent_key: The string to prepend to dictionary's keys
    :param separator: The string used to separate flattened keys
    :return: A flattened dictionary
    """

    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        if isinstance(value, collections.abc.MutableMapping):
            items.extend(flatten_dict(value, new_key, separator).items())
        elif isinstance(value, list):
            for keyx, val in enumerate(value):
                items.extend(flatten_dict({str(keyx): val}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


def json_dumper(data, file):
    """ Basic JSON format dumper """
    json.dump(data, file, indent=2)


def ruamel_dumper(data, file):
    """ Basic ruamel.yaml format dumper """
    yaml_eng = yaml.YAML(typ='unsafe')
    yaml_eng.dump(data, file)


def yaml_dumper(data, file):
    """ Basic yaml format dumper """
    yaml.dump(data, file)


def pprint_dumper(data, file):
    """ PPrint dumper """
    print(pprint.pformat(data), file=file)


def print_dumper(data, file):
    """ Print dumper """
    print(data, file=file)


SUPPORTED_FORMATS = {"json": json_dumper,
                     "ruamel": ruamel_dumper,
                     "yaml": yaml_dumper,
                     "pprint": pprint_dumper,
                     "print": print_dumper}

def get_dumpers(dump_fmt: str):
    """
    Get appropriate dump for unified interface
    """
    if dump_fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Cannot output in {dump_fmt} format.")

    if dump_fmt == "yaml":
        if _YAML_TYPE is None:
            raise ImportError("Couldn't find valid yaml dumper (ruamel.yaml / yaml)"
                              "please install and try again.")
        dump_fmt = _YAML_TYPE

    return SUPPORTED_FORMATS[dump_fmt]


def get_numbers(line: str):
    """ Get all numbers in a string as a list """
    return NUMBER_RE.findall(line)


def get_block(line: str, in_file, start, end, cnt=1):
    """ Check if line is the start of a block and return
    the block if it is, moving in_file forward as it does so """

    block = ""

    if not re.search(start, line):
        return block

    block = line
    fnd = cnt
    for line in in_file:
        block += line
        if re.search(end, line):
            fnd -= 1
            if fnd == 0:
                break
    else:
        raise IOError(f"Unexpected end of file in {in_file.name}")

    return block


def labelled_floats(labels, counts=(None,), sep=r"\s+?", suff=""):
    """ Constructs a regex for extracting floats with assigned labels
    :param labels:iterable of labels to label each group
    :param counts:iterable of counts to group into each label (count must not exceed that of labels)
    :param sep:separator between floats
    """
    if suff and any(cnt for cnt in counts):
        raise NotImplementedError("Suffix and counts not currently supported")

    outstr = ""
    for label, cnt in itertools.zip_longest(labels, counts):
        if cnt:
            outstr += f"(?:(?P<{label}>(?:{sep}{EXPNUMBER_RE}{suff}){{{cnt}}}))"
        else:
            outstr += f"(?:{sep}(?P<{label}>{EXPNUMBER_RE}){suff})"

    return outstr


def stack_dict(out_dict, in_dict):
    """ Append items in `in_dict` to the keys in `out_dict` """
    for key, val in in_dict.items():
        out_dict[key].append(val)


def fix_data_types(in_dict, type_dict):
    """ Applies correct types to elements of in_dict by mapping given in type_dict"""
    for key, typ in type_dict.items():
        if key in in_dict:
            in_dict[key] = to_type(in_dict[key], typ)


def add_aliases(in_dict, alias_dict, replace=False):
    """ Adds aliases of known names into dictionary, if replace is true, remove original """
    for frm, new in alias_dict.items():
        if frm in in_dict:
            in_dict[new] = in_dict[frm]
            if replace:
                in_dict.pop(frm)


def to_type(data_in, typ):
    """ Convert types to `typ` regardless of if data_in is iterable or otherwise """
    if isinstance(data_in, (list, tuple)):
        data_in = tuple(map(typ, data_in))
    elif isinstance(data_in, str):
        data_in = typ(data_in)
    return data_in


# --- Constants
SHELLS = ('s', 'p', 'd', 'f')
FST_D = ('x', 'y', 'z')
SND_D = ('xx', 'yy', 'zz', 'yz', 'zx', 'xy')

CASTEP_OUTPUT_NAMES = (
    "castep",
    "param",
    "cell",
    "geom",
    "md",
    "bands",
    "hug",
    "phonon_dos",
    "efield",
    "xrd_sf",
    "elf_fmt",
    "chdiff_fmt",
    "pot_fmt",
    "den_fmt"
)


# --- RegExes
# Regexps to recognise numbers
FNUMBER_RE = r"(?:[+-]?(?:\d*\.?\d+|\d+\.?\d*))"
EXPNUMBER_RE = rf"(?:{FNUMBER_RE}(?:[Ee][+-]?\d{{1,3}})?)"
INTNUMBER_RE = r"(?:\d+)"
NUMBER_RE = re.compile(rf"(?:{EXPNUMBER_RE}|{FNUMBER_RE}|{INTNUMBER_RE})")

# Regexp to identify extended chemical species
SPECIES_RE = r"[A-Z][a-z]{0,2}"
ATOM_NAME_RE = rf"{SPECIES_RE}(?::\w+)?"

# Unless we have *VERY* exotic electron shells
SHELL_RE = rf"\d[{''.join(SHELLS)}]\d{{1,2}}"

# Atom regexp
ATREG = rf"(?P<spec>{ATOM_NAME_RE})\s+(?P<index>\d+)"

# Atom reference with 3-vector

ATDAT3VEC = re.compile(ATREG + labelled_floats(FST_D))

TAG_RE = re.compile(r"<--\s*(?P<tag>\w+)")
