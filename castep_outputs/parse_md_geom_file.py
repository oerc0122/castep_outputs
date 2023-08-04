"""
Parse castep .md or .geom files
"""

from typing import TextIO, List, Dict
from collections import defaultdict

from .castep_res import ATDATTAG, TAG_RE, get_numbers
from .constants import FST_D
from .utility import to_type, add_aliases

ALIASES = {'E': 'energy',
           'T': 'temperature',
           'P': 'pressure',
           'h': 'lattice_vectors',
           'hv': 'lattice_velocity',
           'R': 'position',
           'V': 'velocity',
           'F': 'force'}


def parse_md_geom_file(md_geom_file: TextIO) -> List[Dict[str, float]]:
    """ Parse standard MD and GEOM file formats """

    while "END header" not in md_geom_file.readline():
        pass

    steps = []
    curr = defaultdict(list)
    for line in md_geom_file:
        if not line.strip():  # Next step
            if curr:
                add_aliases(curr, ALIASES)
                for ion in filter(lambda x: isinstance(x, tuple), curr):
                    add_aliases(curr[ion], ALIASES)
                steps.append(curr)
            curr = defaultdict(list)
        elif not TAG_RE.search(line):  # Timestep
            curr['time'] = to_type(get_numbers(line)[0], float)

        elif match := ATDATTAG.match(line):
            ion = (match.group('spec'), match.group('index'))
            if ion not in curr:
                curr[ion] = {}
            curr[ion][match.group('tag')] = to_type([*(match.group(d) for d in FST_D)], float)

        elif match := TAG_RE.search(line):
            curr[match.group('tag')].append([*to_type(get_numbers(line), float)])

    return steps


# Aliases
parse_md_file = parse_md_geom_file
parse_geom_file = parse_md_geom_file
