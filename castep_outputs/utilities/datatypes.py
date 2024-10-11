"""Types produced by castep_outputs."""
from __future__ import annotations

from collections.abc import Callable
from typing import Dict, Literal, Tuple, TypedDict

#: Parser protocol
ParserFunction = Callable  # [[TextIO], Dict[str, Any]] limited by 3.8


# General types

#: CASTEP atom keys.
AtomIndex = Tuple[str, int]
#: Standard 3D vector.
ThreeVector = Tuple[float, float, float]
#: Complex 3D vector.
ComplexThreeVector = Tuple[complex, complex, complex]
#: Voigt notation vector.
SixVector = Tuple[float, float, float, float, float, float]
#: Three by three matrix.
ThreeByThreeMatrix = Tuple[ThreeVector, ThreeVector, ThreeVector]
#: Atom properties linking unique atom to a physical property.
AtomPropBlock = Dict[AtomIndex, ThreeVector]


class CellInfo(TypedDict):
    """Information from cell block data."""

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
    """Initial spins as read from cell file."""

    #: Spin as spin quantum number.
    spin: float
    #: Magnetic moment in Bohr magnetons.
    magmom: float
    #: Whether spin can vary.
    fix: bool


# Elastic

class ElasticProperties(TypedDict):
    """Elastic properties as measured from elastic calculation."""

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
    """Final configuration following optimisation."""

    #: Cell info block denoting final state.
    cell: CellInfo
    #: Positions of atoms in cell in Ang.
    atoms: AtomPropBlock
    #: Estimated bulk modulus in GPa.
    final_bulk_modulus: float
    #: Estimated enthalpy in eV.
    final_enthalpy: float


class GeomTableElem(TypedDict):
    """Element of mid-run geom opt status."""

    #: Whether component has converted.
    converged: bool
    #: Current tolerance limit.
    tolerance: float
    #: Current measured value.
    value: float


class GeomTable(TypedDict):
    """Mid-run geom opt status table."""

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
    """Molecular dipole status."""

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
    """Character table from group theory analysis of eigenvectors."""

    #: List of symmetry operations for each point.
    chars: tuple[tuple[str, int], ...]
    #: Multiplolarity.
    mul: int
    #: Irreducible representation.
    rep: str
    #: Point group name.
    name: str


class QData(TypedDict, total=False):
    """Phonon Q-Point data."""

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
    """Symmetry analysis report for phonon calculations."""

    #: Class/type of analysis.
    title: str
    #: Matrix of symmetry operations.
    mat: tuple[tuple[int | float, ...], ...]


class RamanReport(TypedDict, total=False):
    """Raman susceptibility report."""

    #: Raman susceptibility.
    tensor: ThreeByThreeMatrix
    #: Trace of susceptibility.
    trace: float
    #: :math:`\sum\limits_{i} \sigma{}_{ii}^{2} -`
    #: :math:`\sum\limits_{i,j} \sigma{}_{ij}\sigma{}_{ji}`
    ii: float
    #: Depolarisation ratio in 0.5 A/amu.
    depolarisation: float | None


# Occupancies

class Occupancies(TypedDict):
    """SCF Band occupancies report."""

    #: Band index.
    band: int
    #: Total eigenvalue.
    eigenvalue: float
    #: Calculated occupancy.
    occupancy: float


# SCF

class WvfnLineMin(TypedDict):
    """Wavefunction minimisation report."""

    #: Energy before minimisation.
    init_energy: float
    #: Estimated gradient.
    init_de_dstep: float
    #: Steps in units.
    steps: tuple[float, ...]
    #: Energy change in eV.
    gain: tuple[float, ...]


class SCFSection(TypedDict):
    """SCF step component."""

    #: Initial energy in eV.
    initial: float
    #: Final energy in eV.
    final: float
    #: Difference between initial and final in eV.
    change: float


class SCFContrib(TypedDict, total=False):
    """Contributions making up total SCF state."""

    #: Correction for apolarity.
    apolar_correction: float
    #: Correction for electronic entropy (TS).
    electronic_entropy_term_ts: float
    #: Ewald contribution.
    ewald_energy_const: float
    #: XC energy.
    exchange_correlation_energy: float
    #: Fermi energy.
    fermi_energy: float
    #: Hartree energy.
    hartree_energy: float
    #: Hubbard U component.
    hubbard_u_correction: float
    #: Kinetic contribution.
    kinetic_energy: float
    #: PSPot contribution.
    local_pseudopotential_energy: float
    #: Non coulombic energy constraint.
    non_coulombic_energy_const: float
    #: NLXC contribution.
    non_local_energy: float
    #: Potential energy total.
    potential_energy_total: float
    #: Free energy.
    total_free_energy_e_ts: float
    #: Correction to XC energy.
    xc_correction: float


class SCFDebugInfo(TypedDict, total=False):
    """SCF full verbosity output summary."""

    #: Number of bands in calculation.
    no_bands: int
    #: Eigenvalue with kinetic contribution.
    kinetic_eigenvalue: list[float]
    #: SCF iterative solution.
    eigenvalue: list[SCFSection]
    #: Contributions making up total state.
    contributions: SCFContrib


class SCFReport(TypedDict, total=False):
    """Full SCF report summary."""

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
    #: Energy in constraint (if constrained).
    constraint_energy: float
    #: Total energy difference due to dipole correction.
    dipole_corr_energy: float
    #: Number of bands to minimise.
    no_bands: int
    #: Kinetic eigenvalue at each band.
    kinetic_eigenvalue: float
    #: Eigenvalue breakdown of minimisation.
    eigenvalue: list[SCFSection]
    #: SCF Debug information at high verbosity.
    debug_info: SCFDebugInfo


# Bonds

class BondInfo(TypedDict):
    """Single-bond information from final bonding report."""

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
    """Pseudopotential projector information."""

    #: Electronic orbital.
    orbital: int
    #: Electronic shell state.
    shell: Literal["s", "p", "d", "f"]
    #: Pseudopotential projector handling.
    #: Type can be:
    #:
    #: - ``U`` - a single ultrasoft projector.
    #: - ``UU`` - Two ultrasoft projectors.
    #: - ``N`` - a single norm-conserving projector.
    #: - ``L`` - use this projector as the local component.
    #: - ``G`` - an ultrasoft GIPAW Gamma projector.
    #: - ``H`` - an norm-conserving GIPAW Gamma projector.
    #: - ``P`` - Dummy: do not make a projector.
    #: - ``LG`` - Make Gammas for local channel (not done by default).
    #:
    #: An unlabelled projector will be `None`
    type: Literal["U", "UU", "N", "L", "G", "H", "P", "LG", "LL", "GG", "LGG", None]


class PSPotStrInfo(TypedDict, total=False):
    """
    Information about pseudopotential string.

    Notes
    -----
    Further info on PSPot strings:

    - https://castep-docs.github.io/castep-docs/documentation/Pseudopotentials/otfg_string/
    - https://www.tcm.phy.cam.ac.uk/castep/otfg.pdf
    """

    #: 0, 1, 2 for s, p, d respectively.
    local_channel: int
    #: Pseudisation radius for augmentation functions (:math:`\beta`) in Bohr.
    beta_radius: float
    #: Pseudisation radius for pseudo-core charge in Bohr.
    core_radius: float
    #: Pseudisation radius for augmentation functions in Bohr.
    r_inner: float
    #: Estimated cut-off energy for coarse precision in Ha.
    coarse: float
    #: Estimated cut-off energy for medium precision in Ha.
    medium: float
    #: Estimated cut-off energy for fine precision in Ha.
    fine: float
    #: Projection
    proj: str
    #: All pseudopotential projectors.
    projectors: tuple[PSPotProj, ...]
    #: Extra options.
    opt: list[str]
    shell_swp: str
    shell_swp_end: str
    #: Print detailed debug information of PSpot.
    print: bool
    #: Total PSPot string.
    string: str


class PSPotElecStruct(TypedDict):
    """Reference electronic structure detail."""

    #: Energy of orbital.
    energy: float
    #: Electronic occupancy of shell.
    occupation: float
    #: Orbital e.g. 6d3/2.
    orb: str


class PSPotDebugInfo(TypedDict):
    """Debugging information from pseudopotential information."""

    #: Eigenvalue of :attr:`nl`
    eigenvalue: float
    #: Nonlocal orbital number.
    nl: int
    #: Type of ?
    type: Literal["AE", "PS"]


class PSPotTableInfo(TypedDict, total=False):
    """Information from the PS pot table summary."""

    #: Orbital cutoff.
    rc: float
    #: The projector name.
    beta: float | str
    #: Energy of corresponding orbital.
    e: float
    #: Spin quantum number.
    j: int
    #: Angular momentum quantum number.
    l: int  # noqa: E741
    #: 1=Norm-conserving, 0=Ultrasoft
    norm: Literal[0, 1]
    #: Pseudisation scheme.
    #:
    #: - ``qc`` - qc tuned.
    #: - ``tm`` - Troullier-Martins pseudosation scheme.
    #: - ``pn`` - Polynomial fit.
    #: - ``pb`` - Bessel fit.
    #: - ``es`` - "extra soft" scheme.
    #: - ``esr=val`` - Extra-soft with explicit specification of r_c.
    #: - ``nonlcc`` - Do not generate of unscreen with a pseudo-core charge.
    #: - ``schro`` - Use non-relativistic schroedinger equation for AE calculation
    #:   (default is scalar relativistic eqn).
    #: - ``aug`` - Explicitly turn on augmentation charges.
    #: - ``scpsp`` - Generate a self-consistent pseudopotential.
    scheme: Literal["2b", "es", "ev", "fh", "pn", "pv", "qb", "qc", "tm"]


class PSPotReport(TypedDict, total=False):
    """PS pot report from table summary."""

    #: Chemical element being calculated.
    element: str
    #: Full breakdown of PSPot string.
    detail: PSPotStrInfo
    #: Core charge of ion.
    ionic_charge: float
    #: Level of DFT theory used.
    level_of_theory: Literal["LDA"]
    #: Argumentation charge nodification.
    augmentation_charge_rinner: tuple[float, ...]
    #: Correction to partial core charge.
    partial_core_correction: tuple[float, ...]
    #: Pseudopotential breakdown of projectors.
    pseudopotential_definition: PSPotTableInfo
    #: Outer electronic orbital set.
    reference_electronic_structure: list[PSPotElecStruct]
    #: Pseudopotential calculator.
    solver: Literal["Koelling-Harmon", "Schroedinger", "ZORA", "Dirac (FR)", "Unknown"]


class PSPotEnergy(TypedDict):
    """PS pot energy minimisation summary."""

    #: Electronic energy of atom.
    pseudo_atomic_energy: float
    #: Spin spilling from pure state.
    charge_spilling: tuple[float, ...]


# Symmetry & Constraints

class Symop(TypedDict):
    """Symmetry operation definition."""

    #: Displacement vector for symop.
    displacement: ThreeVector
    #: Rotational transformation for symop.
    rotation: ThreeByThreeMatrix
    #: List of atoms which are identical under symmetry.
    symmetry_related: list[AtomIndex]


class ConstraintsReport(TypedDict, total=False):
    """Constraints block information."""

    #: Number of constraints on cell vectors.
    number_of_cell_constraints: int
    #: Number of constraints on ions.
    number_of_ionic_constraints: int
    #: Constraints on a,b,c,:math:`\alpha`,:math:`\beta`,:math:`\gamma`.
    #:
    #: 0 implies fixed, matching indices are tied.
    cell_constraints: tuple[int, int, int, int, int, int]
    #: Whether centre of mass is constrained.
    com_constrained: bool
    #: Nonlinear constraints on ions.
    ionic_constraints: dict[AtomIndex, ThreeByThreeMatrix]


class SymmetryReport(TypedDict, total=False):
    """Symmetry block information."""

    #: Largest deviation from ideal symmetry in Ang.
    maximum_deviation_from_symmetry: str
    #: Number of symmetry operations.
    number_of_symmetry_operations: int
    #: Space group.
    point_group_of_crystal: str
    #: Point group.
    space_group_of_crystal: str
    #: List of all symmetry operations.
    symop: list[Symop]
    #: Number of primitive cells in system.
    n_primitives: int


# KPoints

class KPoint(TypedDict):
    """Single :math:`k`-point definition."""

    #: :math:`k`-point position.
    qpt: ThreeVector
    #: :math:`k`-point weighting.
    weight: float


class KPointsList(TypedDict):
    """:math:`k`-points list specification."""

    #: List of :math:`k`-points.
    points: list[KPoint]
    #: Number of :math:`k`-points.
    num_kpoints: int


class KPointsSpec(TypedDict, total=False):
    """:math:`k`-point grid specification."""

    #: Monkhurst-Pack Grid.
    kpoint_mp_grid: tuple[int, int, int]
    #: Monkhurst-Pack offset in 1/Ang.
    kpoint_mp_offset: ThreeVector
    #: Number of :math:`k`-points.
    num_kpoints: int


# Memory Report

class MemoryEst(TypedDict):
    """Memory estimate."""

    #: Estimated RAM usage in MiB.
    memory: float
    #: Estimated disk usage in MiB.
    disk: float


# Band Structure

class BandStructure(TypedDict):
    """Band structure table information."""

    #: Band spin.
    spin: int
    #: :math:`k`-point x coordinate.
    kx: float
    #: :math:`k`-point y coordinate.
    ky: float
    #: :math:`k`-point z coordinate.
    kz: float
    #: :math:`k`-point group.
    kpgrp: int
    #: Band number.
    band: tuple[int, ...]
    #: Energy in eV.
    energy: tuple[float, ...]


# Thermodynamics

class Thermodynamics(TypedDict):
    """
    Thermodynamic properties.

    Notes
    -----
    See
    https://www.tcm.phy.cam.ac.uk/castep/documentation/WebHelp/content/modules/castep/thcastepthermo.htm
    for more info.
    """

    #: Temperature in K.
    t: tuple[float, ...]
    #: Temperature dependence of energy in eV.
    e: tuple[float, ...]
    #: Free energy in eV.
    f: tuple[float, ...]
    #: Entropy in J/mol/K.
    s: tuple[float, ...]
    #: Heat capacity in J/mol/K.
    cv: tuple[float, ...]
    #: Zero-point energy in eV.
    zero_point_energy: float


# MD

class MDInfo(TypedDict, total=False):
    """Per-step MD information block."""

    #: Current MD time passed in s.
    time: float
    #: Hamiltonian energy in eV.
    hamilt_energy: float
    #: Kinetic energy in eV.
    #:
    #: :math:`\mathcal{K} = \sum\limits^{N}\frac{1}{2}mv^{2}`
    kinetic_energy: float
    #: Potential energy in eV.
    potential_energy: float
    #: Kinetic temperature in eV.
    #:
    #: :math:`T = k_{B} \frac{\left<2\mathcal{K}\right>}{3N}`
    temperature: float
    #: Sum of KE and PE.
    total_energy: float


# TDDFT

class TDDFTData(TypedDict):
    """Time-dependent DFT information."""

    #: State energy in eV.
    energy: float
    #: Estimated error.
    error: float
    #: Whether state is: Spurious, Single, Doublet, etc.
    type: str


# Files


class HeaderAtomInfo(TypedDict):
    """Atom info from header."""

    #: Atom indices.
    index: tuple[int, ...]
    #: Atom species.
    spec: list[str]
    #: Positions in u.
    u: tuple[float, ...]
    #: Positions in v.
    v: tuple[float, ...]
    #: Positions in w.
    w: tuple[float, ...]
    #: Atom masses.
    mass: tuple[float, ...]


class StandardHeader(TypedDict):
    """
    Standard header from CASTEP outputs.

    Includes:

    - phonon
    - phonon_dos
    - efield
    - tddft
    - bands
    """

    #: System box.
    unit_cell: ThreeByThreeMatrix
    #: Atomic info.
    coords: HeaderAtomInfo | dict[AtomIndex, ThreeVector]
