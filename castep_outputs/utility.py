"""
Utility functions for parsing castep outputs
"""
from typing import Tuple, Any, Dict, TextIO, List, Callable, Union
import fileinput
import logging
import collections.abc
from collections import defaultdict
import json
import pprint
import re

import castep_outputs.castep_res as REs

try:
    from ruamel import yaml
    _YAML_TYPE = "ruamel"
except ImportError:
    try:
        import yaml
        _YAML_TYPE = "yaml"
    except ImportError:
        _YAML_TYPE = None


class FileWrapper:
    """
    Convenience file wrapper to add rewind and line number capabilities
    """
    def __init__(self, file):
        self.file = file
        self.pos = 0
        self.lineno = 0
        self.name = self.file.name if hasattr(self.file, 'name') else 'unknown'

    def __iter__(self):
        return self

    def __next__(self):
        self.lineno += 1
        self.pos = self.file.tell()
        nextline = self.file.readline()
        if not nextline:
            raise StopIteration()
        return nextline

    def rewind(self):
        """Rewinds file to previous line"""
        if self.file.tell == self.pos:
            return
        self.lineno -= 1
        self.file.seek(self.pos)


def normalise_string(string: str) -> str:
    """
    Normalise a string removing leading/trailing space
    and making all spacing single-space
    """
    return " ".join(string.strip().split())


def atreg_to_index(dict_in: dict, clear: bool = True) -> Tuple[str, int]:
    """
    Transform a matched atreg value to species index tuple
    Also clear value from dictionary for easier processing
    """
    spec, ind = dict_in["spec"], dict_in["index"]

    if isinstance(dict_in, dict) and clear:
        del dict_in["spec"]
        del dict_in["index"]

    return (spec, int(ind))


def normalise(obj: Any, mapping: Dict[type, Union[type, Callable]] = ()) -> Any:
    """
    Standardises data after processing
    """
    if isinstance(obj, (tuple, list)):
        obj = tuple(normalise(v, mapping) for v in obj)
    elif isinstance(obj, (dict, defaultdict)):
        obj = {key: normalise(val, mapping) for key, val in obj.items()}

    if type(obj) in mapping:
        obj = mapping[type(obj)](obj)

    return obj


def json_safe(obj: Any) -> Any:
    """ Transform datatypes into JSON safe variants"""
    if isinstance(obj, dict):
        obj_out = {}

        for key, val in obj.items():
            if isinstance(key, (tuple, list)):
                # Key in bonds is tuple[tuple[AtomIndex]]
                if isinstance(key[0], tuple):
                    key = "_".join(str(y) for x in key for y in x)
                else:
                    key = "_".join(map(str, key))
            obj_out[key] = json_safe(val)

        obj = obj_out
    elif isinstance(obj, complex):
        obj = {"real": obj.real, "imag": obj.imag}
    return obj


def flatten_dict(dictionary: Dict,
                 parent_key: bool = False,
                 separator: str = '_') -> Dict[str, Any]:
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


def json_dumper(data: Any, file: TextIO):
    """ Basic JSON format dumper """
    json.dump(data, file, indent=2)


def ruamel_dumper(data: Any, file: TextIO):
    """ Basic ruamel.yaml format dumper """
    yaml_eng = yaml.YAML(typ='unsafe')
    yaml_eng.dump(data, file)


def yaml_dumper(data: Any, file: TextIO):
    """ Basic yaml format dumper """
    yaml.dump(data, file)


def pprint_dumper(data: Any, file: TextIO):
    """ PPrint dumper """
    print(pprint.pformat(data), file=file)


def print_dumper(data: Any, file: TextIO):
    """ Print dumper """
    print(data, file=file)


SUPPORTED_FORMATS = {"json": json_dumper,
                     "ruamel": ruamel_dumper,
                     "yaml": yaml_dumper,
                     "pprint": pprint_dumper,
                     "print": print_dumper}


def get_dumpers(dump_fmt: str) -> Callable:
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


def stack_dict(out_dict: Dict[Any, List], in_dict: Dict[Any, List]) -> Dict[Any, List]:
    """ Append items in `in_dict` to the keys in `out_dict` """
    for key, val in in_dict.items():
        out_dict[key].append(val)


def add_aliases(in_dict: Dict[str, Any],
                alias_dict: [str, str],
                replace: bool = False) -> Dict[str, Any]:
    """ Adds aliases of known names into dictionary, if replace is true, remove original """
    for frm, new in alias_dict.items():
        if frm in in_dict:
            in_dict[new] = in_dict[frm]
            if replace:
                in_dict.pop(frm)


def log_factory(file: TextIO) -> Callable:
    """ Return logging function to add file info to logs """
    if isinstance(file, fileinput.FileInput):
        def log_file(message, *args, level="info"):
            getattr(logging, level)(f"[{file.filename()}:{file.lineno()}]"
                                    f" {message}", *args)
    elif isinstance(file, FileWrapper):
        def log_file(message, *args, level="info"):
            getattr(logging, level)(f"[{file.name}:{file.lineno}]"
                                    f" {message}", *args)
    elif hasattr(file, 'name'):
        def log_file(message, *args, level="info"):
            getattr(logging, level)(f"[{file.name}] {message}", *args)
    else:
        def log_file(message, *args, level="info"):
            getattr(logging, level)(message, *args)

    return log_file


def determine_type(data: str) -> type:
    """ Deterimine the datatype rand return the appropriate types """
    if data.title() in ("T", "True", "F", "False"):
        return bool

    if re.match(rf"(?:\s*{REs.EXPFNUMBER_RE})+", data):
        return float

    if re.match(rf"(?:\s*{REs.INTNUMBER_RE})+", data):
        return int

    if re.match(rf"(?:\s*{REs.FLOAT_RAT_RE.pattern})+", data):
        return float

    return str


def _parse_float_or_rational(val: str) -> float:
    """ Parse a float or a rational to float """
    if "/" in val:
        val = val.split("/")
        return float(val[0]) / float(val[1])

    return float(val)


def _parse_logical(val: str) -> bool:
    """ Parse a logical to a bool """
    if val.title() in ("T", "True", "1"):
        return True

    return False


_TYPE_PARSERS = {float: _parse_float_or_rational,
                 bool: _parse_logical}


def to_type(data_in: Union[str, List, Tuple], typ: type) -> Union[Tuple[type], type]:
    """ Convert types to `typ` regardless of if data_in is iterable or otherwise """
    parser = _TYPE_PARSERS.get(typ, typ)

    if isinstance(data_in, (list, tuple)):
        data_in = tuple(map(parser, data_in))
    elif isinstance(data_in, str):
        data_in = parser(data_in)
    return data_in


def fix_data_types(in_dict: Dict, type_dict: Dict[str, type]) -> Dict:
    """ Applies correct types to elements of in_dict by mapping given in type_dict"""
    for key, typ in type_dict.items():
        if key in in_dict:
            in_dict[key] = to_type(in_dict[key], typ)
