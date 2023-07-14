#!/usr/bin/env python3
"""
Parse castep .md or .geom files
"""

import re
from collections import defaultdict

from .utility import (ATDAT3VEC, TAG_RE, FST_D, to_type, get_numbers)

ATDATTAG = re.compile(rf"\s*{ATDAT3VEC.pattern}\s*{TAG_RE.pattern}")


def parse_md_geom_file(md_geom_file, verbose=False):
    """ Parse standard MD and GEOM file formats """

    while "END header" not in md_geom_file.readline():
        pass

    steps = []
    curr = defaultdict(list)
    for line in md_geom_file:
        if not line.strip():  # Next step
            if curr:
                steps.append(curr)
            curr = defaultdict(list)
        elif not TAG_RE.search(line):  # Timestep
            curr['time'] = to_type(get_numbers(line)[0], float)

        elif match := ATDATTAG.match(line):
            ion = f"{match.group('spec')}_{match.group('index')}"
            if ion not in curr:
                curr[ion] = {}
            curr[ion][match.group('tag')] = to_type([*(match.group(d) for d in FST_D)], float)

        elif match := TAG_RE.search(line):
            curr[match.group('tag')].append([*to_type(get_numbers(line), float)])

    return steps


# Aliases
parse_md_file = parse_md_geom_file
parse_geom_file = parse_md_geom_file
