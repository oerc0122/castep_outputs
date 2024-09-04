# pylint: disable=missing-class-docstring
"""
Types produced by castep_outputs
"""

from typing import Dict, List, Literal, Optional, Tuple, TypedDict, Union

# General types

AtomIndex = Tuple[str, int]
ThreeVector = Tuple[float, float, float]
SixVector = Tuple[float, float, float, float, float, float]
ThreeByThreeMatrix = Tuple[ThreeVector, ThreeVector, ThreeVector]
AtomPropBlock = Dict[AtomIndex, ThreeVector]


class CellInfo(TypedDict):
    lattice_parameters: ThreeVector
    cell_angles: ThreeVector
    real_lattice: ThreeByThreeMatrix
    recip_lattice: ThreeByThreeMatrix
    density_amu: float
    density_g: float
    volume: float


# Initial Spins

class InitialSpin(TypedDict):
    spin: float
    magmom: float
    fix: bool


# Elastic

class ElasticProperties(TypedDict):
    young_s_modulus: ThreeVector
    poisson_ratios: SixVector
    bulk_modulus: ThreeVector
    shear_modulus: ThreeVector
    speed_of_sound: ThreeByThreeMatrix
    longitudinal_waves: float
    transverse_waves: float


# Geometry

class FinalConfig(TypedDict):
    cell: CellInfo
    atoms: AtomPropBlock
    final_bulk_modulus: float
    final_enthalpy: float


class GeomTableElem(TypedDict):
    converged: bool
    tolerance: float
    value: float


class GeomTable(TypedDict):
    smax: GeomTableElem
    de_ion: GeomTableElem
    f_max: GeomTableElem
    dr_max: GeomTableElem


# Dipole

class DipoleTable(TypedDict):
    centre_electronic: ThreeVector
    centre_positive: ThreeVector
    dipole_direction: ThreeVector
    dipole_magnitude: float
    total_ionic: float
    total_valence: float


# Phonon

class CharTable(TypedDict):
    chars: Tuple[Tuple[str, int], ...]
    mul: int
    rep: str
    name: str


class QData(TypedDict, total=False):
    char_table: CharTable
    qpt: ThreeVector
    n: Tuple[int, ...]
    frequency: Tuple[float, ...]
    intensity: Tuple[float, ...]
    irrep: Tuple[str, ...]
    active: Tuple[Literal["Y", "N"], ...]
    raman_active: Tuple[Literal["Y", "N"], ...]
    raman_intensity: Tuple[float, ...]


class PhononSymmetryReport(TypedDict):
    title: str
    mat: Tuple[Tuple[Union[int, float], ...], ...]


class RamanReport(TypedDict, total=False):
    tensor: ThreeByThreeMatrix
    trace: float
    ii: float
    depolarisation: Optional[float]


# Occupancies

class Occupancies(TypedDict):
    band: int
    eigenvalue: float
    occupancy: float


# SCF

class WvfnLineMin(TypedDict):
    init_energy: float
    init_de_dstep: float
    steps: Tuple[float, ...]
    gain: Tuple[float, ...]


class SCFSection(TypedDict):
    initial: float
    final: float
    change: float


class SCFReport(TypedDict, total=False):
    energy: float
    energy_gain: float
    fermi_energy: float
    time: float
    density_residual: Optional[float]
    constraint_energy: float
    dipole_corr_energy: float
    no_bands: int
    kinetic_eigenvalue: float
    eigenvalue: List[SCFSection]


# Bonds

class BondInfo(TypedDict):
    population: float
    spin: Optional[float]
    length: float


BondData = Dict[Tuple[AtomIndex, AtomIndex], BondInfo]


class MullikenInfo(TypedDict, total=False):
    spin_sep: bool
    charge: float
    spin: float
    total: float
    s: float
    p: float
    d: float
    f: float
    up_total: float
    up_s: float
    up_p: float
    up_d: float
    up_f: float
    down_total: float
    down_s: float
    down_p: float
    down_d: float
    down_f: float


# PSPot

class PSPotProj(TypedDict):
    orbital: int
    shell: Literal["s", "p", "d", "f"]
    type: Literal["N", "U", "UU", "L", "LL", "G", "GG", "LGG", None]


class PSPotStrInfo(TypedDict, total=False):
    local_channel: int
    beta_radius: float
    core_radius: float
    r_inner: float
    coarse: float
    medium: float
    fine: float
    proj: str
    projectors: Tuple[PSPotProj, ...]
    opt: List[str]
    shell_swp: str
    shell_swp_end: str
    print: bool
    string: str


class PSPotElecStruct(TypedDict):
    energy: float
    occupation: float
    orb: str


class PSPotDebugInfo(TypedDict):
    eigenvalue: float
    nl: int
    type: Literal["AE", "PS"]


class PSPotTableInfo(TypedDict, total=False):
    rc: float
    beta: Union[float, str]
    e: float
    j: int
    l: int  # noqa: E741
    norm: int
    scheme: Literal["2b", "es", "ev", "fh", "pn", "pv", "qb", "qc", "tm"]


class PSPotReport(TypedDict, total=False):
    element: str
    detail: PSPotStrInfo
    ionic_charge: float
    level_of_theory: Literal["LDA"]
    augmentation_charge_rinner: Tuple[float, ...]
    partial_core_correction: Tuple[float, ...]
    pseudopotential_definition: PSPotTableInfo
    reference_electronic_structure: List[PSPotElecStruct]
    solver: Literal["Koelling-Harmon", "Schroedinger", "ZORA", "Unknown"]


class PSPotEnergy(TypedDict):
    pseudo_atomic_energy: float
    charge_spilling: Tuple[float, ...]


# Symmetry & Constraints

class Symop(TypedDict):
    displacement: ThreeVector
    rotation: ThreeByThreeMatrix
    symmetry_related: List[AtomIndex]


class ConstraintsReport(TypedDict, total=False):
    number_of_cell_constraints: int
    number_of_ionic_constraints: int
    cell_constraints: Tuple[int, int, int, int, int, int]
    com_constrained: bool
    ionic_constraints: Dict[AtomIndex, ThreeByThreeMatrix]


class SymmetryReport(TypedDict, total=False):
    maximum_deviation_from_symmetry: str
    number_of_symmetry_operations: int
    point_group_of_crystal: str
    space_group_of_crystal: str
    symop: List[Symop]
    n_primitives: int


# KPoints

class KPoint(TypedDict):
    qpt: ThreeVector
    weight: float


class KPointsList(TypedDict):
    points: List[KPoint]
    num_kpoints: int


class KPointsSpec(TypedDict, total=False):
    kpoint_mp_grid: Tuple[int, int, int]
    kpoint_mp_offset: Tuple[float, float, float]
    num_kpoints: int


# Memory Report

class MemoryEst(TypedDict):
    memory: float
    disk: float


# Band Structure

class BandStructure(TypedDict):
    spin: int
    kx: float
    ky: float
    kz: float
    kpgrp: int
    band: Tuple[int, ...]
    energy: Tuple[float, ...]


# Thermodynamics

class Thermodynamics(TypedDict):
    t: Tuple[float, ...]
    e: Tuple[float, ...]
    f: Tuple[float, ...]
    s: Tuple[float, ...]
    cv: Tuple[float, ...]
    zero_point_energy: float


# MD

class MDInfo(TypedDict, total=False):
    time: float
    hamilt_energy: float
    kinetic_energy: float
    potential_energy: float
    temperature: float
    total_energy: float


# TDDFT

class TDDFTData(TypedDict):
    energy: float
    error: float
    type: str
