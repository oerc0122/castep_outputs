"""Module containing dumpers for formats."""
from __future__ import annotations

import json
import pprint
from contextlib import suppress
from typing import Any, Callable, TextIO

_YAML_TYPE = None

with suppress(ImportError):
    import yaml
    _YAML_TYPE = "pyyaml"

with suppress(ImportError):
    from ruamel import yaml as ruamel
    _YAML_TYPE = "ruamel"


#: Dumping function protocol.
Dumper = Callable[[Any, TextIO], None]


def json_dumper(data: Any, file: TextIO) -> None:
    """
    JSON format dumper.

    Parameters
    ----------
    data
        Data to dump.
    file
        File to dump to.
    """
    json.dump(data, file, indent=2)


def ruamel_dumper(data: Any, file: TextIO) -> None:
    """
    YAML (ruamel.yaml) format dumper.

    Parameters
    ----------
    data
        Data to dump.
    file
        File to dump to.
    """
    yaml_eng = ruamel.YAML(typ="unsafe")
    yaml_eng.dump(data, file)


def pyyaml_dumper(data: Any, file: TextIO) -> None:
    """
    YAML (pyyaml) format dumper.

    Parameters
    ----------
    data
        Data to dump.
    file
        File to dump to.
    """
    yaml.dump(data, file)


def pprint_dumper(data: Any, file: TextIO) -> None:
    """
    Pretty print dumper.

    Parameters
    ----------
    data
        Data to dump.
    file
        File to dump to.
    """
    print(pprint.pformat(data), file=file)


def print_dumper(data: Any, file: TextIO) -> None:
    """
    Python print dumper.

    Parameters
    ----------
    data
        Data to dump.
    file
        File to dump to.
    """
    print(data, file=file)


def get_dumpers(dump_fmt: str) -> Dumper:
    """
    Get appropriate dump for unified interface.

    Parameters
    ----------
    dump_fmt
        Formats to dump to.

    Returns
    -------
    Dumper
        Dumping function.

    Raises
    ------
    ValueError
        Invalid `dump_fmt` provided.
    ImportError
        No valid YAML dumper and `yaml` requested.

    See Also
    --------
    SUPPORTED_FORMATS
        Acceptable values for `dump_fmt`.
    """
    if dump_fmt == "yaml":
        if _YAML_TYPE is None:
            raise ImportError("Couldn't find valid yaml dumper (ruamel.yaml / yaml)"
                              "please install and try again.")
        dump_fmt = _YAML_TYPE

    if dump_fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Cannot output in {dump_fmt} format. "
                         f"Valid keys are: {', '.join(SUPPORTED_FORMATS.keys())}")

    return SUPPORTED_FORMATS[dump_fmt]


#: Currently supported dumpers.
SUPPORTED_FORMATS: dict[str, Dumper] = {"json": json_dumper,
                                        "ruamel": ruamel_dumper,
                                        "pyyaml": pyyaml_dumper,
                                        "pprint": pprint_dumper,
                                        "print": print_dumper}
