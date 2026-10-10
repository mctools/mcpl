
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

"""Physical constants used by MCPL.

The values are the CODATA 2022 recommended values of the fundamental physical
constants (released by NIST in May 2024, https://physics.nist.gov/cuu/Constants/
), where the Planck constant, the speed of light and the elementary charge are
exact by the definition of the SI units (since 2019). The neutron mass is the
only measured value used.

The constants are given in SI units, and the derived values in the units used
by MCPL (MeV for energies, and Aa for wavelengths).
"""

__all__ = [
            'c_light',
            'e_charge',
            'h_planck',
            'hc_eV_Aa',
            'neutron_mass',
            'neutron_mass_energy' ]

#Exact (SI definition):
h_planck = 6.62607015e-34#Planck constant [J s]
c_light = 299792458.0#speed of light in vacuum [m/s]
e_charge = 1.602176634e-19#elementary charge [C]

#Measured (CODATA 2022, relative standard uncertainty 5.1e-10):
neutron_mass = 1.67492750056e-27#neutron mass [kg]

#Derived:
neutron_mass_energy = neutron_mass * c_light**2 / e_charge * 1e-6#[MeV]
hc_eV_Aa = h_planck * c_light / e_charge * 1e10#h*c [eV*Aa]
