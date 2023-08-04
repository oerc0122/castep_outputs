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
try:
    from ruamel import yaml
    _YAML_TYPE = "ruamel"
except ImportError:
    try:
        import yaml
        _YAML_TYPE = "yaml"
    except ImportError:
        _YAML_TYPE = None


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


def normalise(obj: Any) -> Any:
    """
    Standardises data after processing
    """
    if isinstance(obj, (tuple, list)):
        obj = tuple(normalise(v) for v in obj)
    elif isinstance(obj, (dict, defaultdict)):
        obj = {key: normalise(val) for key, val in obj.items()}

    return obj


def json_safe(obj: Any) -> Any:
    """ Transform datatypes into JSON safe variants"""
    if isinstance(obj, (tuple, list)):
        obj = [json_safe(v) for v in obj]
    elif isinstance(obj, dict):
        obj = json_safe_dict(obj)
    elif isinstance(obj, complex):
        obj = (obj.real, obj.imag)
    return obj


def json_safe_dict(obj: Dict) -> Dict:
    """ Transform a castep_output dict into a JSON safe variant
    i.e. convert tuple keys to conjoined strings """
    obj_out = {}

    for key, val in obj.items():
        if isinstance(key, (tuple, list)):
            key = "_".join(map(str, key))
        obj_out[key] = json_safe(val)
    return obj_out


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


def fix_data_types(in_dict: Dict, type_dict: Dict[str, type]) -> Dict:
    """ Applies correct types to elements of in_dict by mapping given in type_dict"""
    for key, typ in type_dict.items():
        if key in in_dict:
            in_dict[key] = to_type(in_dict[key], typ)


def add_aliases(in_dict: Dict[str, Any],
                alias_dict: [str, str],
                replace: bool = False) -> Dict[str, Any]:
    """ Adds aliases of known names into dictionary, if replace is true, remove original """
    for frm, new in alias_dict.items():
        if frm in in_dict:
            in_dict[new] = in_dict[frm]
            if replace:
                in_dict.pop(frm)


def to_type(data_in: Union[str, List, Tuple], typ: type) -> Union[Tuple[type], type]:
    """ Convert types to `typ` regardless of if data_in is iterable or otherwise """
    if isinstance(data_in, (list, tuple)):
        data_in = tuple(map(typ, data_in))
    elif isinstance(data_in, str):
        data_in = typ(data_in)
    return data_in


def log_factory(file: TextIO) -> Callable:
    """ Return logging function to add file info to logs """
    if isinstance(file, fileinput.FileInput):
        def log_file(message, *args, level="info"):
            getattr(logging, level)(f"[{file.filename()}:{file.lineno()}]"
                                    f" {message}", *args)
    elif hasattr(file, 'name'):
        def log_file(message, *args, level="info"):
            getattr(logging, level)(f"[{file.name}] {message}", *args)
    else:
        def log_file(message, *args, level="info"):
            getattr(logging, level)(message, *args)

    return log_file
