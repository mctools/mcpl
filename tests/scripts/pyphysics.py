
################################################################################
##                                                                            ##
##  This file is part of MCPL (see https://mctools.github.io/mcpl/)           ##
##                                                                            ##
##  Copyright 2015-2026 MCPL developers.                                      ##
##                                                                            ##
##  Licensed under the Apache License, Version 2.0 (the "License");           ##
##  you may not use this file except in compliance with the License.          ##
##  You may obtain a copy of the License at                                   ##
##                                                                            ##
##      http://www.apache.org/licenses/LICENSE-2.0                            ##
##                                                                            ##
##  Unless required by applicable law or agreed to in writing, software       ##
##  distributed under the License is distributed on an "AS IS" BASIS,         ##
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  ##
##  See the License for the specific language governing permissions and       ##
##  limitations under the License.                                            ##
##                                                                            ##
################################################################################


# NEEDS: numpy

# Test the constants module, the conversions between kinetic energies and
# wavelengths, and the wavelength attributes of particles and blocks.

import mcpldev as mcpl
import numpy as np
from mcpldev._physics import ekin_from_wavelength, wavelength_from_ekin
from MCPLTestUtils.dirs import test_data_dir

example_file = test_data_dir.joinpath('example.mcpl')

def test_constants():
    for n in mcpl.constants.__all__:
        print(f'mcpl.constants.{n} = {getattr(mcpl.constants,n)!r}')
    #h/(m_n) in the usual units for thermal neutrons [Aa*m/s]:
    c = mcpl.constants
    print(f'h/m_n = {c.h_planck/c.neutron_mass*1e10:.10g} Aa*m/s')

def test_conversions():
    for ekin, pdg in [ (0.0253e-6, 2112), (25e-9, 2112), (1.0, 2112),
                       (1e4, 2112), (12.398e-3, 22), (1e-6, 22), (1.0, 11),
                       (0.0, 2112) ]:
        wl = wavelength_from_ekin(ekin, pdg)
        back = ekin_from_wavelength(wl, pdg)
        print(f'ekin={ekin:g}MeV pdgcode={pdg}: wavelength={wl:.6g}Aa,'
              f' back to ekin={back:.6g}MeV')
        assert np.isnan(wl) or abs(back-ekin) <= 1e-14 * ekin
    wl = wavelength_from_ekin(np.array([25e-9,25e-9,1e-3]), np.array([2112,22,2212]))
    print(f'arrays: {np.array2string(wl, precision=6)}')
    #Non-relativistic limit, lambda = h/sqrt(2*m*E):
    c = mcpl.constants
    e = 25e-9
    wl_nr = c.h_planck / np.sqrt(2*c.neutron_mass*e*1e6*c.e_charge) * 1e10
    print(f'relative difference to non-relativistic result at {e:g}MeV:'
          f' {wavelength_from_ekin(e)/wl_nr-1:.3g}')

def test_attributes():
    with mcpl.MCPLFile(example_file) as f:
        b = f.read_block()
        p = f.read()
        print(f'first particle: pdgcode={p.pdgcode} ekin={p.ekin:.6g}'
              f' wavelength={p.wavelength:.6g}')
        isng = np.isin(b.pdgcode,(2112,22))
        ng = b[isng]
        wl = ng.wavelength
        assert np.allclose(ekin_from_wavelength(wl,ng.pdgcode),ng.ekin,rtol=1e-12)
        print(f'wavelengths of the {len(ng)} neutrons and gammas in the block:'
              f' {np.min(wl):.6g}Aa - {np.max(wl):.6g}Aa')
        #Errors for other particles, and for zero kinetic energy:
        for desc, obj in ( ('block with other particles', b),
                           ('particle which is not a neutron or gamma',
                            b[int(np.argmax(~isng))]) ):
            try:
                obj.wavelength  # noqa: B018
            except mcpl.MCPLError as e:
                print(f'wavelength of {desc}: MCPLError: {e}')
    with mcpl.MCPLOutFile('zero_ekin.mcpl', opt_universalpdgcode=2112) as o:
        o.add_particles( direction = (0,0,1), ekin = [0.0, 1e-6] )
    with mcpl.MCPLFile('zero_ekin.mcpl') as f:
        b = f.read_block()
        try:
            b.wavelength  # noqa: B018
        except mcpl.MCPLError as e:
            print(f'wavelength of neutrons with zero ekin: MCPLError: {e}')
        print(f'wavelength of the other neutron: {b[1:].wavelength[0]:.6g}Aa')

def test_particle_names():
    #Names of particle types (as shown by the statistics), including ions
    #(PDG codes 10LZZZAAAI):
    from mcpldev._physics import _pdg_database
    for pdg in ( 2112, -2212, 22, 1000020040, 1000060120, 1000922350,
                 1000060121, 1010060120, 1010060122, 1001190300, -1000060120,
                 1000000000, 99 ):
        print(f'pdgcode {pdg}: {_pdg_database(pdg)}')

if __name__ == '__main__':
    test_particle_names()
    test_constants()
    test_conversions()
    test_attributes()
