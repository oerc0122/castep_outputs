"""
Parse the following castep outputs:
.elastic
"""
from collections import defaultdict
from typing import Dict, List, TextIO

from ..utilities.castep_res import get_block, get_numbers
from ..utilities.utility import to_type


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
