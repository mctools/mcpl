
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

"""The dimensions and units of the quantities in particle expressions (see
_expressions)."""

__all__ = []

import math

#Dimensions (length,energy,time,temperature) and units of quantities in
#expressions. Values are internally in the units of MCPL (cm, MeV, ms), also for
#wavelengths, and temperatures (of userdata) in K:
_dim_none = (0,0,0,0)
_dim_L, _dim_E, _dim_T, _dim_K = (1,0,0,0), (0,1,0,0), (0,0,1,0), (0,0,0,1)
#(the dimension of fields of the userdata when expressions are checked
#without a file, which have units only in the layouts of files: everything
#computed from them has unknown units, which are never refused):
_dim_unknown = 'unknown'
_expr_units = { 'meV' : (1e-9,_dim_E), 'eV' : (1e-6,_dim_E),
                'keV' : (1e-3,_dim_E), 'MeV' : (1.0,_dim_E),
                'GeV' : (1e3,_dim_E), 'TeV' : (1e6,_dim_E),
                'ns' : (1e-6,_dim_T), 'us' : (1e-3,_dim_T),
                'ms' : (1.0,_dim_T), 's' : (1e3,_dim_T),
                'Aa' : (1e-8,_dim_L), 'nm' : (1e-7,_dim_L),
                'um' : (1e-4,_dim_L), 'mm' : (0.1,_dim_L),
                'cm' : (1.0,_dim_L), 'm' : (100.0,_dim_L),
                'km' : (1e5,_dim_L), 'K' : (1.0,_dim_K),
                'deg' : (math.pi/180,None), 'rad' : (1.0,None) }
