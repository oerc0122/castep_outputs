"""Module containing all regexes."""
from __future__ import annotations

import itertools
import re
from collections.abc import Sequence
from typing import Union

from .constants import FST_D, MINIMISERS, SHELLS

#: Valid input where patterns are wanted.
Pattern = Union[str, re.Pattern]


def get_numbers(line: str) -> list[str]:
    """
    Get all numbers in a string as a list.

    Parameters
    ----------
    line
        String to search for valid numbers.

    Returns
    -------
    list[str]
        All numbers found in `line`.

    Examples
    --------
    >>> get_numbers("Hello 13, my name is 3.142")
    ['13', '3.142']

    See Also
    --------
    NUMBER_RE : RegEx matching numbers.
    """
    return NUMBER_RE.findall(line)


def labelled_floats(labels: Sequence[str], counts: Sequence[int | str | None] = (None,),
                    sep: str = r"\s+?", suffix: str = "") -> str:
    """
    Construct a regex for extracting floats with assigned labels.

    Parameters
    ----------
    labels
        Iterable of labels to label each group.
    counts
        Iterable of counts to group into each label (count must not exceed that of labels).
    sep
        Separator between floats.
    suffix
        Suffix following each float.

    Returns
    -------
    str
        Regular expression to match floats with given labels.

    Raises
    ------
    NotImplementedError
        If `suffix` and `counts` provided.

    Examples
    --------
    .. code-block:: python

       # Capture 3 space-separated floats with labels "x", "y", "z"
       labelled_floats(("x", "y", "z"))
       # Capture 2 colon-separated floats with labels "u", "v"
       labelled_floats(("u", "v"), sep=":")
       # Capture 3 space-separated floats under the label "val"
       labelled_floats(("val",), counts=(3,))
    """
    if suffix and any(cnt for cnt in counts):
        raise NotImplementedError("Suffix and counts not currently supported")

    outstr = ""
    for label, cnt in itertools.zip_longest(labels, counts):
        if cnt:
            outstr += f"(?:(?P<{label}>(?:{sep}{NUMBER_RE.pattern}{suffix}){{{cnt}}}))"
        else:
            outstr += f"(?:{sep}(?P<{label}>{NUMBER_RE.pattern}){suffix})"

    return outstr


def gen_table_re(content: str, border: str = r"\s*",
                 *, pre: str = "", post: str = "", whole_line: bool = True) -> str:
    r"""
    Construct a regex for matching table headers with given borders.

    Parameters
    ----------
    content
        RegEx capturing the content of the table.
    border
        RegEx capturing the characters the make up the border.
    pre
        RegEx matching content outside and before the table.
    post
        RegEx matching content outside and after the table.
    whole_line
        Whether the RegExes are an exact match for the whole line.

    Returns
    -------
    str
        RegEx pattern to match line(s).

    Examples
    --------
    RegEx for a line of "?"s

    .. code-block:: python

       # No content, with any number of questionmarks.
       gen_table_re("", r"\?+")

    RegEx for a separator line in a table which resembles:

    .. code-block::

       +-----------------------------------+

    .. code-block:: python

       gen_table_re("-+", "\+")

    """
    tab_re = (rf"\s*{border}\s*{content}\s*{border}\s*"
              if content else
              rf"\s*{border}\s*")

    tab_re = rf"\s*{pre}{tab_re}{post}\s*"

    if whole_line:
        tab_re = f"^{tab_re}$"

    return tab_re


def get_atom_parts(spec: str) -> dict[str, str]:
    """
    Get components of an atom name (species, tag, label) from a spec string.

    Parameters
    ----------
    spec
        String to split up.

    Returns
    -------
    dict[str, str]
        Dictionary detailing separate parts of atom name.

    Examples
    --------
    >>> get_atom_parts("Ar")
    {'species': 'Ar'}
    >>> get_atom_parts("Ar:tag")
    {'species': 'Ar', 'tag': 'tag'}
    >>> get_atom_parts("Ar [label]")
    {'species': 'Ar', 'label': 'label'}
    >>> get_atom_parts("Ar:tag[label]")
    {'species': 'Ar', 'tag': 'tag', 'label': 'label'}
    """
    return {key: val.strip()
            for key, val in ATOM_NAME_GRP_RE.match(spec).groupdict().items()
            if val}


# --- RegExes
# Regexps to recognise numbers

#: Floating point number.
#:
#: :meta hide-value:
FNUMBER_RE = r"(?:[+-]?(?:\d*\.\d+|\d+\.\d*))"

#: Integer number.
#:
#: :meta hide-value:
INTNUMBER_RE = r"(?:[+-]?(?<!\.)\d+(?!\.))"

#: Float or int with exponent.
#:
#: :meta hide-value:
EXPNUMBER_RE = rf"(?:(?:{FNUMBER_RE}|{INTNUMBER_RE})[Ee][+-]?\d{{1,3}})"

#: Exponent or bare floating point.
#:
#: :meta hide-value:
EXPFNUMBER_RE = f"(?:{EXPNUMBER_RE}|{FNUMBER_RE})"

#: Integer ratio.
#:
#: :meta hide-value:
RATIONAL_RE = rf"\b{INTNUMBER_RE}/{INTNUMBER_RE}\b"

#: Generalised number.
#:
#: :meta hide-value:
NUMBER_RE = re.compile(rf"(?:{EXPNUMBER_RE}|{FNUMBER_RE}|{INTNUMBER_RE})")

#: Floating point, integer or ratio.
#:
#: :meta hide-value:
FLOAT_RAT_RE = re.compile(rf"(?:{RATIONAL_RE}|{EXPFNUMBER_RE}|{INTNUMBER_RE})")

#: Three vector.
#:
#: :meta hide-value:
THREEVEC_RE = labelled_floats(("val",), counts=(3,))

# Regexp to identify extended chemical species
#: Element name.
#:
#: :meta hide-value:
SPECIES_RE = r"[A-Z][a-z]{0,2}"
#: CASTEP atom name with optional tag and label.
#:
#: :meta hide-value:
ATOM_NAME_RE = rf"\b{SPECIES_RE}(?::\w+)?\b(?:\s*\[[^\]]+\])?"
#: Labelled CASTEP atom name.
#:
#: :meta hide-value:
ATOM_NAME_GRP_RE = re.compile(
    rf"(?P<species>{SPECIES_RE})(?::(?P<tag>\w+))?\b(?:\s*\[(?P<label>[^\]]*)\])?",
    )


# Unless we have *VERY* exotic electron shells

#: RegEx for atomic shell labels. E.g. 4d4.
#:
#: :meta hide-value:
SHELL_RE = rf"\d[{''.join(SHELLS)}]\d{{0,2}}"

#: RegEx for CASTEP table tags as in e.g. .md/.geom.
#:
#: :meta hide-value:
TAG_RE = re.compile(r"<--\s*(?P<tag>\w+)")

#: Empty line RegEx
#:
#: :meta hide-value:
EMPTY = r"^\s*$"

#: CASTEP Atom RegEx with optional index.
#:
#: :meta hide-value:
ATOM_RE = rf"(?P<spec>{ATOM_NAME_RE})\s+(?P<index>\d+)"


# Atom reference with 3-vector
#: CASTEP atom followed by 3D vector.
#:
#: :meta hide-value:
ATOMIC_DATA_3VEC = re.compile(ATOM_RE + labelled_floats(FST_D))
ATOMIC_DATA_FORCE = re.compile(ATOM_RE + labelled_floats(FST_D, suffix=r"(?:\s*\([^)]+\))?"))
ATOMIC_DATA_TAG = re.compile(rf"\s*{ATOMIC_DATA_3VEC.pattern}\s*{TAG_RE.pattern}")

# Labelled positions
LABELLED_POS_RE = re.compile(ATOMIC_DATA_3VEC.pattern + r"\s{5}(?P<label>\S{0,8})")

# Colon separated key-val
COLON_SEP_RE = re.compile(r"\b(?P<key>\S+)\s*:\s*(?P<val>\S+)\b")

# VCA atoms
MIXTURE_LINE_1_RE = re.compile(rf"""
(?P<index>\d+)\s+
{labelled_floats(FST_D)}\s+
(?P<spec>{ATOM_NAME_RE})\s+
{labelled_floats(('weight',))}""", re.VERBOSE)
MIXTURE_LINE_2_RE = re.compile(rf"(?P<spec>{ATOM_NAME_RE})\s+{labelled_floats(('weight',))}")


# SCF Loop
SCF_LOOP_RE = re.compile(r"\s*(?:Initial|\d+)\s*"
                         rf"{labelled_floats(('energy', 'fermi_energy', 'energy_gain'))}?\s*"
                         f"{labelled_floats(('time',))}")

# Spin density
INTEGRATED_SPIN_DENSITY_RE = re.compile(r"(?P<vec>2\*)?Integrated \|?Spin Density\|?[^=]+=\s*"
                                        rf"(?P<val>{EXPFNUMBER_RE}\s*"
                                        rf"(?(vec)(?:{EXPFNUMBER_RE}\s*){{2}}))")

# PS Energy
PS_SHELL_RE = re.compile(
    rf"\s*Pseudo atomic calculation performed for (?P<spec>{SPECIES_RE})(\s+{SHELL_RE})+")

# PS Projector
PROJ_TYPES = "[UNGHLP]"
PSPOT_SHELL_RE = rf"(?:{SHELL_RE}{FNUMBER_RE}?)"
PSPOT_PROJ_GROUPS = ("orbital", "shell", "type", "de", "beta_delta")
PSPOT_PROJ_RE = re.compile(rf"""
    (\d)                            # Orbital
    (\d)                            # Shell type
    ({PROJ_TYPES}*)                 # Proj type
    ((?:[\+-=]{FNUMBER_RE})?)       # DE_use
    ((?:@{FNUMBER_RE})?)            # beta_delta
""", re.VERBOSE)

PSPOT_REFERENCE_STRUC_RE = re.compile(
    rf"""
    ^\s*\|\s*
    (?P<orb>{SHELL_RE}(?:/\d+)?)\s*
    {labelled_floats(('occupation', 'energy'))}
    \s*\|\s*$
    """, re.VERBOSE)

PSPOT_DEF_RE = re.compile(
    rf"""
    ^\s*\|\s*
    (?P<beta>\d+|loc)\s*
    (?P<l>\d+)\s*
    (?P<j>\d+)?\s*
    {labelled_floats(('e', 'Rc'))}\s*
    (?P<scheme>\w+)\s*
    (?P<norm>\d+)
    \s*\|\s*$
    """, re.VERBOSE)

# PSPot String
PSPOT_RE = re.compile(
    rf"""^
    (?:{labelled_floats(("local_energy",), sep="")}=)?
    (?P<local_channel>\d+)
    (?P<poly_fit>-)?\|
    {labelled_floats(("core_radius",), sep="")}\|
    (?:{labelled_floats(("beta_radius",), sep="")}\|)?
    (?(beta_radius){labelled_floats(("r_inner",), sep="")}\| |)
    (?:{labelled_floats(("coarse",), sep="")}\|)
    (?:{labelled_floats(("medium",), sep="")}\|)
    (?:{labelled_floats(("fine",), sep="")}\|)
    (?P<proj>{PSPOT_PROJ_RE.pattern}(?::{PSPOT_PROJ_RE.pattern})*)
    (?:\{{(?P<shell_swp>{SHELL_RE}(?:,{SHELL_RE})*)\}})?
    (?:\((?P<opt>[^)]+)\))?
    (?P<debug>\#)?
    (?P<print>\[(?P<shell_swp_end> {PSPOT_SHELL_RE}(?:,{PSPOT_SHELL_RE})* )?\])?
    $
""", re.VERBOSE)

# Forces block
FORCES_BLOCK_RE = re.compile(gen_table_re("([a-zA-Z ]*)Forces", r"\*+"), re.IGNORECASE)
# Stresses block
STRESSES_BLOCK_RE = re.compile(gen_table_re("([a-zA-Z ]*)Stress Tensor", r"\*+"), re.IGNORECASE)

# Bonds
BOND_RE = re.compile(rf"""\s*
                       (?P<spec1>{ATOM_NAME_RE})\s*(?P<ind1>\d+)\s*
                       --\s*
                       (?P<spec2>{ATOM_NAME_RE})\s*(?P<ind2>\d+)\s*
                       {labelled_floats(("population", "spin", "length"), counts=(None,"0,1",None))}
                       """, re.VERBOSE)

# Pair pot
PAIR_POT_RES = {
    "two_body_one_spec": re.compile(
        rf"^(?P<tag>\w+)?\s*\*\s*(?P<spec>{ATOM_NAME_RE})\s*\*\s*$",
    ),
    "two_body_spec":  re.compile(
        rf"(?P<spec1>{ATOM_NAME_RE})\s*-\s*"
        rf"(?P<spec2>{ATOM_NAME_RE})",
    ),
    "two_body_val": re.compile(
        rf"""
            (?P<tag>\w+)?\s*\*\s*
            (?P<label>\w+)\s*
            {labelled_floats(('params',), counts=('1,4',))}\s*
            [\w^/*]+\s* \* \s*
            <--\s*(?P<type>\w+)
            """, re.ASCII | re.VERBOSE,
    ),
    "three_body_spec": re.compile(
        rf"""
        ^(?P<tag>\w+)?\s*\*\s*
        (?P<spec>(?:{ATOM_NAME_RE}\s*){{3}})
        \s*\*\s*$""", re.VERBOSE,
    ),
    "three_body_val": re.compile(
        rf"""
        ^(?P<tag>\w+)?\s*\*\s*
        (?P<label>\w+)\s*
        {labelled_floats(('params',))}\s*
        [\w^/*]+\s* \* \s*
        <--\s*(?P<type>\w+)
        """, re.VERBOSE,
    ),
}

# Orbital population
ORBITAL_POPN_RE = re.compile(rf"\s*{ATOM_RE}\s*(?P<orb>[SPDF][xyz]?)"
                             rf"\s*{labelled_floats(('charge',))}")

# Regexp to identify phonon block in .castep file
PHONON_RE = re.compile(
    rf"""
    \s+\+\s+
    q-pt=\s*{INTNUMBER_RE}\s+
    \({labelled_floats(("qpt",), counts=(3,))}\)
    \s+
    ({FNUMBER_RE})\s+\+
    """, re.VERBOSE)

PROCESS_PHONON_RE = re.compile(
    rf"""\s+\+\s+
    (?P<N>\d+)\s+
    (?P<frequency>{FNUMBER_RE})\s*
    (?P<irrep>[a-zA-V])?\s*
    (?P<ir_intensity>{FNUMBER_RE})?\s*
    (?P<ir_active>[YN])?\s*
    (?P<raman_intensity>{FNUMBER_RE})?\s*
    (?P<raman_active>[YN])?\s*\+""", re.VERBOSE)

TDDFT_RE = re.compile(
    rf"""\s*\+\s*
    {INTNUMBER_RE}
    {labelled_floats(("energy", "error"))}
    \s*(?P<type>\w+)
    \s*\+TDDFT""", re.VERBOSE)

TDDFT_STATE_RE = re.compile(
    rf"""
    \s*(?P<state>\d+)
    \s*(?P<occ>\d+)\s*-->
    \s*(?P<unocc>\d+)
    \s*{labelled_floats(('overlap',))}
    """, re.VERBOSE)

BS_RE = re.compile(
    rf"""
    Spin=\s*(?P<spin>{INTNUMBER_RE})\s*
    kpt=\s*{INTNUMBER_RE}\s*
    \({labelled_floats(("kx","ky","kz"))}\)\s*
    kpt-group=\s*(?P<kpgrp>{INTNUMBER_RE})
    """, re.VERBOSE)

THERMODYNAMICS_DATA_RE = re.compile(labelled_floats(("t", "e", "f", "s", "cv")))
ATOMIC_DISP_RE = re.compile(labelled_floats(("temperature",)) + r"\s*" +
                            ATOM_RE + r"\s*" +
                            labelled_floats(("displacement",), counts=(6,)))

MINIMISERS_RE = f"(?:{'|'.join(x.upper() for x in MINIMISERS)})"
GEOMOPT_MIN_TABLE_RE = re.compile(
    r"\s*\|\s* (?P<step>[^|]+)" +
    labelled_floats(("lambda", "fdelta", "enthalpy"), sep=r"\s*\|\s*") +
    r"\s* \|", re.VERBOSE)

GEOMOPT_TABLE_RE = re.compile(
    r"\s*\|\s* (?P<parameter>\S+)" +
    labelled_floats(("value", "tolerance"), sep=r"\s*\|\s*") +
    r"\s*\|\s* \S+ (?#Units) \s*\|\s* (?P<converged>No|Yes) \s*\|", re.VERBOSE)


# Regexp to identify Mulliken ppoulation analysis line
POPN_RE = re.compile(rf"\s*{ATOM_RE}\s*(?P<spin_sep>up:)?" +
                     labelled_floats((*SHELLS, "total", "charge", "spin")) +
                     "?",   # Spin is optional
                     )

POPN_RE_DN = re.compile(r"\s+\d+\s*dn:" +
                        labelled_floats((*SHELLS, "total")),
                        )

# Regexp for born charges
BORN_RE = re.compile(rf"\s+{ATOM_RE}(?P<charges>(?:\s*{FNUMBER_RE}){{3}})(?:\s*ID=(?P<label>\S+))?")

# MagRes REs
MAGRES_RE = (
    # "Chemical Shielding Tensor" 0
    re.compile(rf"\s*\|\s*{ATOM_RE}{labelled_floats(('iso','aniso'))}\s*"
               rf"(?P<asym>{FNUMBER_RE}|N/A)\s*\|\s*"),
    # "Chemical Shielding and Electric Field Gradient Tensor" 1
    re.compile(rf"\s*\|\s*{ATOM_RE}{labelled_floats(('iso','aniso'))}\s*"
               rf"(?P<asym>{FNUMBER_RE}|N/A)"
               rf"{labelled_floats(('cq', 'eta'))}\s*\|\s*"),
    # "Electric Field Gradient Tensor" 2
    re.compile(rf"\s*\|\s*{ATOM_RE}{labelled_floats(('cq',))}\s*"
               rf"(?P<asym>{FNUMBER_RE}|N/A)\s*\|\s*"),
    # "(?:I|Ani)sotropic J-coupling" 3
    re.compile(rf"\s*\|\**\s*{ATOM_RE}{labelled_floats(('fc','sd','para','dia','tot'))}\s*\|\s*"),
    # "Hyperfine Tensor" 4
    re.compile(rf"\s*\|\s*{ATOM_RE}{labelled_floats(('iso',))}\s*\|\s*"),
)

# MagRes Tasks
MAGRES_TASK = (
    "Chemical Shielding",
    "Chemical Shielding and Electric Field Gradient",
    "Electric Field Gradient",
    "(An)Isotropic J-coupling",
    "Hyperfine",
)

TENSOR_RE = (rf"{labelled_floats(('xx', 'xy', 'xz'))}[\n\r]+"
             rf"{labelled_floats(('yx', 'yy', 'yz'))}[\n\r]+"
             rf"{labelled_floats(('zx', 'zy', 'zz'))}")

MAGRES_OLD_RE = {
    # Atom lines
    "atom": re.compile(
        r"=+\s+"
        rf"( Perturbing Atom|Atom): {ATOM_RE}[\r\n]+"
        r"=+[\r\n]+"
        r"([^=]+)\s+",
        re.MULTILINE | re.DOTALL,
    ),
    # Coordinates
    "coords": re.compile(
        rf"{ATOM_RE}\s+Coordinates\s+{THREEVEC_RE}\s+A",
    ),
    # Magnetic shielding tensor
    "ms_tensor": re.compile(
        rf"\s*(.*?) Shielding Tensor[\r\n]+{TENSOR_RE}",
    ),
    # Spin-Spin coupling tensor
    "isc_tensor": re.compile(
        r"\s{0,}J-coupling (.*?)[\r\n]+"
        rf"{TENSOR_RE}",
    ),
    # Electric field gradient tensor
    "efg_tensor": re.compile(
        r"\s{0,}(.*?) tensor[\r\n]+"
        rf"{TENSOR_RE}"
        r"\s+[A-Za-z]+\s+\d+\s+Eigenvalue\s+V_xx\s+[-0-9\.]+",
    ),
    # Hyperfine tensor
    "hf_tensor": re.compile(
        r"\s{0,}(.*?) tensor[\r\n]+"
        rf"{TENSOR_RE}"
        r"\s+[A-Za-z]+\s+\d+\s+Eigenvalue\s+A_xx\s+[-0-9\.]+",
    ),
}

# Regexp to identify block in .phonon or .phonon_dos file
FRACCOORDS_RE = re.compile(rf"\s*(?P<index>{INTNUMBER_RE}){labelled_floats(('u', 'v', 'w'))}"
                           rf"\s*(?P<spec>{SPECIES_RE}){labelled_floats(('mass',))}")

PHONON_PHONON_RE = re.compile(rf"""
    \s+q-pt=\s*{INTNUMBER_RE}\s*
    {labelled_floats(('qpt', 'pth'), counts=(3, 1))}
    """, re.VERBOSE)

PROCESS_PHONON_PHONON_RE = re.compile(labelled_floats(("n", "f", "Grad_qf")))


# Regexp to identify Fermi energies in .bands file
BANDS_FERMI_RE = re.compile(r"Fermi energ(ies|y) \(in atomic units\)\s*" +
                            labelled_floats(("a", "b")))

# Regexp to identify eigenvalue block in .bands file
# BANDS_EIGENS_RE =
# rf"K-point\s+(\d+)\s*(\s*{FNUMBER_RE})\s*({FNUMBER_RE})\s*({FNUMBER_RE})\s*({FNUMBER_RE})"

DEVEL_CODE_VAL_RE = r"[A-Za-z0-9_]+[:=]\S+"
DEVEL_CODE_BLOCK_RE = rf"([A-Za-z0-9_]+):(?:\s*{DEVEL_CODE_VAL_RE}\s*)*:end\1"
DEVEL_CODE_BLOCK_GENERIC_RE = r"([A-Za-z0-9_]+):(?:.*):end\1"

PARAM_VALUE_RE = re.compile(rf"""
^\s*(?P<key>[a-z_]+)
\s*[ \t:=]\s*
(?P<val>(?:\s*{NUMBER_RE.pattern})+|\S+)
(?P<unit>\s\S*\w\S*)?
\s*$
""", re.IGNORECASE | re.VERBOSE)

IONIC_CONSTRAINTS_RE = re.compile(rf"^\s*\d\s+{ATOM_RE}{THREEVEC_RE}")
POSITIONS_LINE_RE = re.compile(rf"^\s*(?P<spec>{SPECIES_RE})"
                               rf"(?P<pos>(?:\s+{FLOAT_RAT_RE.pattern}){{3}})")
POSITIONS_SPIN_RE = re.compile(rf"(?:spin|magmom)\s*[= :\t]\s*(?P<spin>{FLOAT_RAT_RE.pattern})",
                               re.IGNORECASE)
POSITIONS_MIXTURE_RE = re.compile(rf"mixture[= :\t]\(\s*{labelled_floats(('mix', 'ratio'))}\)",
                                  re.IGNORECASE)
SPEC_PROP_RE = re.compile(rf"\s*{ATOM_NAME_RE}\s+(?P<val>.*)")
