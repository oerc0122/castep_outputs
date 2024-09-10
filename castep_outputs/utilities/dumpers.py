"""
Module containing dumpers for formats
"""

import json
import pprint
from typing import Any, Callable, TextIO

try:
    from ruamel import yaml
    _YAML_TYPE = "ruamel"
except ImportError:
    try:
        import yaml
        _YAML_TYPE = "yaml"
    except ImportError:
        _YAML_TYPE = None


def json_dumper(data: Any, file: TextIO):
    """ Basic JSON format dumper """
    json.dump(data, file, indent=2)


def ruamel_dumper(data: Any, file: TextIO):
    """ Basic ruamel.yaml format dumper """
    yaml_eng = yaml.YAML(typ="unsafe")
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


SUPPORTED_FORMATS = {"json": json_dumper,
                     "ruamel": ruamel_dumper,
                     "yaml": yaml_dumper,
                     "pprint": pprint_dumper,
                     "print": print_dumper}
