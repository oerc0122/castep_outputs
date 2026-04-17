import os
import sys
from difflib import unified_diff
from pathlib import Path
from textwrap import fill, indent

from castep_outputs import __version__
from castep_outputs.cli.args import ALL_NAMES, get_parser
from castep_outputs.cli.castep_outputs_main import ALL_PARSERS
from castep_outputs.utilities.dumpers import SUPPORTED_FORMATS

os.environ["COLUMNS"] = "77"

template_path = Path(__file__).parent / "README_template.rst"
out_path = Path(__file__).parent.parent / "README.rst"

template = template_path.read_text(encoding="utf-8")

parser = get_parser()

file_formats = fill(", ".join(f"``.{ft}``" for ft in sorted(ALL_NAMES)), width=80)

parse_functions = "\n".join(
    f" - {fmt}: ``{parser.__name__}``"
    for fmt, parser in sorted(ALL_PARSERS.items(), key=lambda x: x[1].__name__)
)

usage = indent(parser.format_help(), "   ")

parsers = "\n".join(f"- ``.{ft}``" for ft in sorted(ALL_NAMES))
dumpers = "\n".join(f"- ``{dumper}``" for dumper in sorted(SUPPORTED_FORMATS))

to_write = template.format(
    version=__version__,
    file_formats=file_formats,
    parse_functions=parse_functions,
    usage=usage,
    parsers=parsers,
    dumpers=dumpers,
)


match sys.argv[1:]:
    case ["--lint"]:
        current = out_path.read_text(encoding="utf-8").splitlines()
        issue = False
        for diff in unified_diff(current, to_write.splitlines(), str(out_path), "after"):
            print(diff)
            issue = True

        if issue:
            sys.exit(1)
        print("Good to go")

    case _:
        out_path.write_text(to_write, encoding="utf-8")
