"""
Types produced by castep_outputs.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any, Dict, Literal, TextIO, Tuple, TypedDict

# Parser protocol

ParserFunction = Callable[[TextIO], Dict[str, Any]]


# General types

AtomIndex = Tuple[str, int]
ThreeVector = Tuple[float, float, float]
SixVector = Tuple[float, float, float, float, float, float]
ThreeByThreeMatrix = Tuple[ThreeVector, ThreeVector, ThreeVector]
AtomPropBlock = Dict[AtomIndex, ThreeVector]


class CellInfo(TypedDict):
    """
    Information from cell block data.
    """
    #: Cell side lengths in Ang.
    lattice_parameters: ThreeVector
    #: Cell lattice angles in Degrees.
    cell_angles: ThreeVector
    #: Lattice parameters as 3x3 matrix.
    real_lattice: ThreeByThreeMatrix
    #: Reciprocal space lattice as 3x3 matrix.
    recip_lattice: ThreeByThreeMatrix
    #: Density of cell in atomic mass units / Ang^3.
    density_amu: float
    #: Density of cell in grams / Ang^3
    density_g: float
    #: Total volume of cell in Ang^3
    volume: float


# Initial Spins

class InitialSpin(TypedDict):
    """
    Initial spins as read from cell file.
    """
    #: Spin as spin quantum number.
    spin: float
    #: Magnetic moment in Bohr magnetons.
    magmom: float
    #: Whether spin can vary.
    fix: bool


# Elastic

class ElasticProperties(TypedDict):
    """
    Elastic properties as measured from elastic calculation.
    """
    #: Young's Modulus in GPa.
    young_s_modulus: ThreeVector
    #: Poisson Ratios.
    poisson_ratios: SixVector
    #: Bulk Modulus in GPa.
    bulk_modulus: ThreeVector
    #: Shear Modulus in GPa.
    shear_modulus: ThreeVector
    #: Speed of sound in Ang/ps.
    speed_of_sound: ThreeByThreeMatrix
    #: Average longitudinal speed of sound in Ang/ps.
    longitudinal_waves: float
    #: Average transverse speed of sound in Ang/ps.
    transverse_waves: float


# Geometry

class FinalConfig(TypedDict):
    """
    Final configuration following optimisation.
    """
    #: Cell info block denoting final state.
    cell: CellInfo
    #: Positions of atoms in cell in Ang.
    atoms: AtomPropBlock
    #: Estimated bulk modulus in GPa.
    final_bulk_modulus: float
    #: Estimated enthalpy in eV.
    final_enthalpy: float


class GeomTableElem(TypedDict):
    """
    Element of mid-run geom opt status.
    """
    #: Whether component has converted.
    converged: bool
    #: Current tolerance limit.
    tolerance: float
    #: Current measured value.
    value: float


class GeomTable(TypedDict):
    """
    Mid-run geom opt status table.
    """
    #: Strain on system in GPa.
    smax: GeomTableElem
    #: Energy/ion in eV.
    de_ion: GeomTableElem
    #: Maximum force in system in eV/Ang.
    f_max: GeomTableElem
    #: Maximum ion step between optimisation steps in Ang.
    dr_max: GeomTableElem


# Dipole

class DipoleTable(TypedDict):
    """
    Molecular dipole status.
    """
    #: Weighted average position of electronic charge in system in Ang.
    centre_electronic: ThreeVector
    #: Weighted average position of positive ionic charge in system in Ang.
    centre_positive: ThreeVector
    #: Direction vector of dipole.
    dipole_direction: ThreeVector
    #: Magnitude of dipole moment in Debye.
    dipole_magnitude: float
    #: Total charge in system in fundamental charge.
    total_ionic: float
    #: Total valence charge in system in fundamental charge.
    total_valence: float

# Phonon


class CharTable(TypedDict):
    """
    Character table from group theory analysis of eigenvectors.
    """
    #: List of symmetry operations for each point.
    chars: tuple[tuple[str, int], ...]
    #: Multiplolarity.
    mul: int
    #: Irreducible representation.
    rep: str
    #: Point group name.
    name: str


class QData(TypedDict, total=False):
    """
    Phonon Q-Point data.
    """
    #: Group theory analysis at Q-point.
    char_table: CharTable
    #: Q-Point in 1/Ang.
    qpt: ThreeVector
    #: IDs
    n: tuple[int, ...]
    #: Frequencies
    frequency: tuple[float, ...]
    #: IR Intensities.
    intensity: tuple[float, ...]
    #: Irreducible representation.
    irrep: tuple[str, ...]
    #: IR Active.
    active: tuple[Literal["Y", "N"], ...]
    #: Raman active.
    raman_active: tuple[Literal["Y", "N"], ...]
    #: Raman intensities.
    raman_intensity: tuple[float, ...]


class PhononSymmetryReport(TypedDict):
    """
    Symmetry analysis report for phonon calculations.
    """
    #: Class/type of analysis.
    title: str
    #: Matrix of symmetry operations.
    mat: tuple[tuple[int | float, ...], ...]


class RamanReport(TypedDict, total=False):
    """
    Raman susceptibility report.
    """
    #: Raman susceptibility.
    tensor: ThreeByThreeMatrix
    #: Trace of array
    trace: float
    #: Sum(diagonal**2) - sum(off-diagonal :math:`xy*yx`...)
    ii: float
    #: Depolarisation ratio in 0.5 A/amu
    depolarisation: float | None


# Occupancies

class Occupancies(TypedDict):
    """
    SCF Band occupancies report.
    """
    #: Band index.
    band: int
    #: Total eigenvalue.
    eigenvalue: float
    #: Calculated occupancy.
    occupancy: float


# SCF

class WvfnLineMin(TypedDict):
    """
    Wavefunction minimisation report.
    """
    #: Energy before minimisation.
    init_energy: float
    #: Estimated gradient.
    init_de_dstep: float
    #: Steps in units.
    steps: tuple[float, ...]
    #: Energy change in eV.
    gain: tuple[float, ...]


class SCFSection(TypedDict):
    """
    SCF step component.
    """
    #: Initial energy in eV.
    initial: float
    #: Final energy in eV.
    final: float
    #: Difference between initial and final in eV.
    change: float


class SCFReport(TypedDict, total=False):
    """
    Full SCF report summary.
    """
    #: System energy in eV.
    energy: float
    #: Energy difference in step.
    energy_gain: float
    #: Calculated Fermi energy.
    fermi_energy: float
    #: Wall time since start.
    time: float
    #: Density mixing residual.
    density_residual: float | None
    #: Energy in constraint (if constrained)
    constraint_energy: float
    #: Total energy difference due to dipole correction.
    dipole_corr_energy: float
    #: Number of bands to minimise.
    no_bands: int
    #: Kinetic eigenvalue at each band.
    kinetic_eigenvalue: float
    #: Eigenvalue breakdown of minimisation.
    eigenvalue: list[SCFSection]


# Bonds

class BondInfo(TypedDict):
    """
    Single-bond information from final bonding report.
    """
    #: Electronic population of bond in fundamental charge.
    population: float
    #: Total spin in bond.
    spin: float | None
    #: Length of bond in Ang.
    length: float


#: Full bond information for all pairs.
BondData = Dict[Tuple[AtomIndex, AtomIndex], BondInfo]


class MullikenInfo(TypedDict, total=False):
    """
    Mulliken population analysis report.

    Notes
    -----
    In case of `spin_sep == True`, the properties:
    `total`, `s`, `p`, `d` and `f` also have spin-separated
    components (`up` and `down`) e.g. `up_total`, `down_s`.
    """
    #: Whether orbitals are split by spins.
    spin_sep: bool
    #: Total charge in fundamental charge.
    charge: float
    #: Total spin.
    spin: float
    #: Number of electrons in all orbitals.
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
    projectors: tuple[PSPotProj, ...]
    opt: list[str]
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
    beta: float | str
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
    augmentation_charge_rinner: tuple[float, ...]
    partial_core_correction: tuple[float, ...]
    pseudopotential_definition: PSPotTableInfo
    reference_electronic_structure: list[PSPotElecStruct]
    solver: Literal["Koelling-Harmon", "Schroedinger", "ZORA", "Unknown"]


class PSPotEnergy(TypedDict):
    pseudo_atomic_energy: float
    charge_spilling: tuple[float, ...]


# Symmetry & Constraints

class Symop(TypedDict):
    displacement: ThreeVector
    rotation: ThreeByThreeMatrix
    symmetry_related: list[AtomIndex]


class ConstraintsReport(TypedDict, total=False):
    number_of_cell_constraints: int
    number_of_ionic_constraints: int
    cell_constraints: tuple[int, int, int, int, int, int]
    com_constrained: bool
    ionic_constraints: dict[AtomIndex, ThreeByThreeMatrix]


class SymmetryReport(TypedDict, total=False):
    maximum_deviation_from_symmetry: str
    number_of_symmetry_operations: int
    point_group_of_crystal: str
    space_group_of_crystal: str
    symop: list[Symop]
    n_primitives: int


# KPoints

class KPoint(TypedDict):
    qpt: ThreeVector
    weight: float


class KPointsList(TypedDict):
    points: list[KPoint]
    num_kpoints: int


class KPointsSpec(TypedDict, total=False):
    kpoint_mp_grid: tuple[int, int, int]
    kpoint_mp_offset: tuple[float, float, float]
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
    band: tuple[int, ...]
    energy: tuple[float, ...]


# Thermodynamics

class Thermodynamics(TypedDict):
    t: tuple[float, ...]
    e: tuple[float, ...]
    f: tuple[float, ...]
    s: tuple[float, ...]
    cv: tuple[float, ...]
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
