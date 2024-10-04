import re
import os

class GamessOut:
    def __init__(self):
        self.success = False
        self.error_message = ""
        self.total_energy = None
        self.coordinates = []

    def __str__(self):
        return "Success:{}".format(self.success)

def gparse(molecule, method, basis, parse_type="default"):
    r = GamessOut()

    r.molecule = molecule
    r.method = method
    r.basis = basis
    r.filepath = f'data/{molecule}.gamess'

    out_str = open(r.filepath, "r").read()
    r.output = out_str

    if os.name == "nt":
        r.success = True
    elif os.name == "posix":
        # exited gracefully?
        if not out_str.endswith("gracefully.\n"):
            r.error_message = out_str[-1000:]
            return r
        else:
            r.success = True
    else:
        r.success = True

    # NOTE: Above check appears to be version-dependent.
    #   Temporary fix: assume it worked until proven otherwise:

    if parse_type == "default":
        r = default_parse(out_str, r)

    return r


def default_parse(out_str, r):

    runtyp_re = re.compile("RUNTYP=(\S+)[\s]*")

    num_basis_re = re.compile("TOTAL NUMBER OF BASIS SET SHELLS(.*?)\n")
    num_electron_re = re.compile("NUMBER OF ELECTRONS(.*?)\n")
    eigen_re = re.compile("EIGENVECTORS(.*?)\n\n     ------", re.DOTALL)
    eng_total_re = re.compile("TOTAL ENERGY =(.*)\n")
    eng_potential_re = re.compile("TOTAL POTENTIAL ENERGY =(.*)\n")
    eng_kinetic_re = re.compile("TOTAL KINETIC ENERGY =(.*)\n")
    virial_ratio_re = re.compile("VIRIAL RATIO \(V/T\) =(.*)\n")
    pop_re = re.compile("TOTAL MULLIKEN AND LOWDIN ATOMIC POPULATIONS(.*?)\n\n", re.DOTALL)
    dipole_moment_re = re.compile("DEBYE\)\n(.*?)\n \.\.", re.DOTALL)

    # if RUNTYP is OPTIMIZE
    nsearch_re = re.compile("    NSERCH=(.*)\n")
    coord_re = re.compile("COORDINATES OF ALL ATOMS ARE (.*?)------------\n(.*?)\n\n", re.DOTALL)
    #mo_re = re.compile("MOLECULAR ORBITALS(.*?)\n\n     ------", re.DOTALL)

    # if RUNTYP is HESSIAN
    offset_re = re.compile("MODES    1 TO (.*) ARE TAKEN", re.DOTALL)
    ir_re = re.compile("SYMMETRY  RED\. MASS  IR INTENS\.\n(.*?)\n\n     ------", re.DOTALL)
    temperature_re = re.compile("THERMOCHEMISTRY AT T=(.*?) K\n", re.DOTALL)
    zpe_re = re.compile("THE HARMONIC ZERO POINT ENERGY IS(.*?)KCAL/MOL", re.DOTALL)
    thermo_re = re.compile("CAL/MOL-K\n(.*?)\n VIB. THERMAL", re.DOTALL)
    stationary_point_re = re.compile("THIS IS NOT A STATIONARY POINT ON THE MOLECULAR PES")

    nmr_re = re.compile("GIAO CHEMICAL SHIELDING TENSOR \(PPM\):\n(.*?)DONE WITH NMR SHIELDINGS", re.DOTALL)
    tddft_re = re.compile("SUMMARY OF TDDFT RESULTS\n\n(.*?)\n TRANSITION", re.DOTALL)
    pcm_eng_re = re.compile("RESULTS OF PCM CALCULATION(.*?)A\.U\.\n\n", re.DOTALL)

    # RUNTYP
    r.runtyp = None
    match = runtyp_re.search(out_str)
    if match is not None:
        r.runtyp = match.group(1).strip()

    # Num of basis
    r.num_basis = None
    match = num_basis_re.search(out_str)
    if match is not None:
        r.num_basis = match.group().split("=")[1][:-1]
        r.num_basis = int(r.num_basis)

    # Num of electrons
    r.num_electrons = None
    match = num_electron_re.search(out_str)
    if match is not None:
        r.num_electrons = match.group().split("=")[1][:-1]
        r.num_electrons = int(r.num_electrons)

    # Orbital energies
    r.orbital_energies = []
    match = eigen_re.search(out_str)
    if match is not None:
        for line in match.group(1).split("\n"):
            # startwith many spaces and line contains float value
            if line.startswith("                  ") and line.find(".") > 0:
                a = [float(v) for v in line.split()]
                r.orbital_energies += a

        r.nHOMO = r.orbital_energies[int(r.num_electrons / 2) - 2]
        r.HOMO  = r.orbital_energies[int(r.num_electrons / 2) - 1]
        r.LUMO  = r.orbital_energies[int(r.num_electrons / 2)]
        r.nLUMO = r.orbital_energies[int(r.num_electrons / 2) + 1]

    # Optimization output file contains "MOLECULAR ORBITALS" section.
    # mo_energies = []
    # match = mo_re.search(out_str)
    # if match is not None:
    #     for line in match.group(1).split("\n"):
    #         # startwith many spaces and line contains float value
    #         if line.startswith("                  ") and line.find(".") > 0:
    #             ls = [float(v) for v in line.split()]
    #             mo_energies += ls

    # Total energy (this only match in gas phase calculations)
    r.total_energy = None
    for match in eng_total_re.finditer(out_str):
        r.total_energy = float(match.group(1).strip())

    r.potential_energy = None
    for match in eng_potential_re.finditer(out_str):
        r.potential_energy = float(match.group(1).strip())

    r.kinetic_energy = None
    for match in eng_kinetic_re.finditer(out_str):
        r.kinetic_energy = float(match.group(1).strip())

    r.virial_ratio = None
    for match in virial_ratio_re.finditer(out_str):
        r.virial_ratio = float(match.group(1).strip())

    # MULLIKEN and LOWDIN charge
    r.atoms = []
    r.mulliken_populations = []
    r.mulliken_charges = []
    r.lowdin_populations = []
    r.lowdin_charges = []
    for match in pop_re.finditer(out_str):
        for line in match.group(1).split("\n"):
            a = line.split()
            if len(a) == 6:
                r.atoms.append(a[1])
                r.mulliken_populations.append(float(a[2]))
                r.mulliken_charges.append(float(a[3]))
                r.lowdin_populations.append(float(a[4]))
                r.lowdin_charges.append(float(a[5]))

    # Dipole morment
    r.dipole_moment = None
    r.dipole_x = None
    r.dipole_y = None
    r.dipole_z = None
    for match in dipole_moment_re.finditer(out_str):
        a = match.group(1).split()
        r.dipole_x = float(a[0])
        r.dipole_y = float(a[1])
        r.dipole_z = float(a[2])
        r.dipole_moment = float(a[3])

    # if RUNTYP is OPTIMIZE

    # NSERCH (optimization enegy transition)
    r.nsearches = []
    for match in nsearch_re.finditer(out_str):
        line = match.group(1).strip()
        r.nsearches.append(float(line.split()[-1]))

    # Coordinates
    r.coordinates = []
    for match in coord_re.finditer(out_str):
        for line in match.group(2).split("\n"):
            coord = line.split()
            xyz = [float(coord[2]), float(coord[3]), float(coord[4])]
            r.coordinates.append(xyz)

    # if RUNTYP is HESSIAN

    r.offset = None
    match = offset_re.search(out_str)
    if match is not None:
        r.offset = int(match.group(1).strip())

    thermotable = []
    match = thermo_re.search(out_str)
    if match is not None:
        for line in match.group(1).split("\n"):
            a = line.split()
            if len(a) == 7:
                thermotable.append([float(v) for v in a[1:]])
        r.internal_energy = thermotable[-1][0]
        r.enthalpy = thermotable[-1][1]
        r.gibbs = thermotable[-1][2]
        r.heat_capacity_v = thermotable[-1][3]
        r.heat_capacity_p = thermotable[-1][4]
        r.entropy = thermotable[-1][5]

    r.temperature = None
    match = temperature_re.search(out_str)
    if match is not None:
        r.temperature = float(match.group(1).strip())

    r.ZPE = None
    match = zpe_re.search(out_str)
    if match is not None:
        r.ZPE = float(match.group(1).split("\n")[-1])

    r.ir_spectra = []
    match = ir_re.search(out_str)
    if match is not None:
        for line in match.group(1).split("\n"):
            a = line.split()
            r.ir_spectra.append((float(a[1]), float(a[4])))

    r.is_stationary_point = True
    match = stationary_point_re.search(out_str)
    if match is not None:
        r.is_stationary_point = False

    # TDDFT
    uv_spectra = []
    match = tddft_re.search(out_str)
    if match is not None:
        for line in match.group(1).split("\n")[2:]:
            a = line.split()
            if len(a) == 8:
                uv_spectra.append((float(a[3]), float(a[7])))
        r.uv_spectra = uv_spectra

    # parse PCM result if eng_re didn't match
    match = pcm_eng_re.search(out_str)
    if match is not None:
        for line in match.group().split("\n"):
            if line.endswith("A.U."):
                if line.startswith(" FREE ENERGY IN SOLVENT"):
                    r.free_energy = float(l[-20:-5].strip())
                elif line.startswith(" INTERNAL ENERGY IN SOLVENT"):
                    r.internal_energy = float(l[-20:-5].strip())
                elif line.startswith(" DELTA INTERNAL ENERGY"):
                    r.delta_internal_energy = float(l[-20:-5].strip())
                elif line.startswith(" ELECTROSTATIC INTERACTION"):
                    r.electrostatic_interaction = float(l[-20:-5].strip())
                elif line.startswith(" PIEROTTI CAVITATION ENERGY"):
                    r.pierotti_cavitation_energy = float(l[-20:-5].strip())
                elif line.startswith(" DISPERSION FREE ENERGY"):
                    r.dispersion_free_energy = float(l[-20:-5].strip())
                elif line.startswith(" REPULSION FREE ENERGY"):
                    r.repulsion_free_energy = float(l[-20:-5].strip())
                elif line.startswith(" TOTAL INTERACTION"):
                    r.total_interacion = float(l[-20:-5].strip())
                elif line.startswith(" TOTAL FREE ENERGY"):
                    r.total_energy = float(l[-20:-5].strip())
                else:
                    pass

    # NMR
    r.isotropic_shielding = []
    match = nmr_re.search(out_str)
    if match is not None:
        for line in match.group(1).split("\n"):
            ls = line.split()
            if len(ls) == 1:
                try:
                    r.isotropic_shielding.append(float(ls[0]))
                except:
                    pass

    return r
