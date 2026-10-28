
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

# The contents of the reference files of MCPL format 4 in
# tests/data/reffmt4 (with userdata, without, and broken ones), read in small
# blocks, with all values given exactly, so changes in how they are read are
# noticed (that the C and Python readers agree is tested by b.py).

import numpy as np
from mcpldev import MCPLError, MCPLFile
from MCPLTestUtils.dirs import test_data_dir


def text( v ):
    """A value exactly, as Python numbers (floats as the shortest text giving
    the same double, also for float32 values)"""
    if isinstance(v,np.ndarray):
        return '[' + ','.join( text(e) for e in v ) + ']'
    if isinstance(v,(np.floating,float)):
        return repr(float(v))
    return repr(int(v))

def show( path ):
    print(f'==> {path.name}')
    try:
        f = MCPLFile(path,blocklength=7)
    except MCPLError as e:
        print(f'  MCPLError: {e}')
        return
    with f:
        print(f'  version {f.version}, {f.nparticles} particles, userflags: {f.opt_userflags},'
              f' polarisation: {f.opt_polarisation}, single precision: {f.opt_singleprec},'
              f' universal pdgcode: {f.opt_universalpdgcode}, universal weight:'
              f' {f.opt_universalweight}')
        print(f'  userdata layout: {f.userdata_layout!r}')
        print(f'  comments: {list(f.comments)}')
        print(f'  blobs: { {k:bytes(v).hex() for k,v in f.blobs.items()} }')
        print(f'  stat:sum: {dict(f.stat_sum)}')
        fields = [ 'pdgcode', 'x', 'y', 'z', 'ux', 'uy', 'uz', 'ekin', 'time', 'weight' ]
        if f.opt_polarisation:
            fields += [ 'polx', 'poly', 'polz' ]
        if f.opt_userflags:
            fields.append('userflags')
        for b in f.particle_blocks:
            for i in range(len(b)):
                values = [ f'{n}={text(getattr(b,n)[i])}' for n in fields ]
                if f.userdata_layout:
                    ud = b.userdata[i]
                    values += [ f'{n}={text(ud[n])}' for n in ud.dtype.names ]
                print(f'  {b.file_offset+i}: ' + ' '.join(values))

for path in sorted(test_data_dir.joinpath('reffmt4').iterdir()):
    show(path)
