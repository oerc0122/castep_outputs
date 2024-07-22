"""
Parse the following castep outputs:
.phonon
"""
import re
from collections import defaultdict
from typing import Any, Dict, TextIO

from ..utilities import castep_res as REs
from ..utilities.castep_res import get_block, labelled_floats
from ..utilities.utility import fix_data_types, log_factory, stack_dict
from .parse_utilities import parse_regular_header


def parse_phonon_file(phonon_file: TextIO) -> Dict[str, Any]:
    """ Parse castep .phonon file """

    logger = log_factory(phonon_file)
    phonon_info = defaultdict(list)
    phonon_info["qpt_pos"] = []
    phonon_info["evals"] = []
    phonon_info["evecs"] = []
    evals = []
    evecs = []

    for line in phonon_file:
        if block := get_block(line, phonon_file, "BEGIN header", "END header"):

            data = parse_regular_header(block)
            phonon_info.update(data)
            eigenvectors_endblock = ""
            eigenvectors_endblock += " "*(4-len(str(phonon_info["branches"])))+str(phonon_info["branches"])
            eigenvectors_endblock += " "*(4-len(str(phonon_info["ions"])))+str(phonon_info["ions"])

        elif block := get_block(line, phonon_file, "q-pt", "Phonon Eigenvectors", out_fmt=list):

            logger("Found eigenvalue block")
            b = []
            for line in block:
                if "q-pt" in line:
                    _, _, posx,posy,posz, *weight = line.split()
                    qdata = {'pos':[posx,posy,posz], 'weight':weight}
                    fix_data_types(qdata, {'pos': float,
                                           'weight': float})
                    phonon_info["qpt_pos"].append(qdata['pos'])

                elif "Eigenvectors" not in line:
                    _, e_val, *_ = line.split()
                    qdata = {'eval':e_val}
                    fix_data_types(qdata, {'eval': float})
                    evals.append(qdata['eval'])
                    if len(evals) == phonon_info["branches"]:
                        phonon_info["evals"].append(evals)
                        evals = []
        
        elif block := get_block(line, phonon_file, "Mode Ion", eigenvectors_endblock, out_fmt=list):
            
            logger("Found eigenvector block")
            for line in block:
                if "Mode" not in line:
                    _, _, *vectors = line.split()
                    
                    qdata = {'evec':vectors}
                    fix_data_types(qdata, {'evec': float})
                    e_vec = []
                    for i in range(0,len(vectors), 2):
                        e_vec.append([qdata['evec'][i],qdata['evec'][i+1]])
                    qdata['evec'] = e_vec
                    evecs.append(qdata['evec'])

                    if len(evecs) == phonon_info["branches"]*phonon_info["ions"]:
                        phonon_info["evecs"].append(evecs)
    
    return phonon_info