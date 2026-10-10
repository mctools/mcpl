
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

# Test indexing of particle blocks, and MCPLOutFile.add_particles with blocks
# and new values of some of their fields.

import mcpldev as mcpl
import numpy as np
from MCPLTestUtils.dirs import test_data_dir

example_file = test_data_dir.parent.parent.joinpath('examples','example.mcpl')

def raw(fn):
    with mcpl.MCPLFile(fn) as f:
        return f.headersize, np.concatenate([ b._data for b in f.particle_blocks ])

def test_block_indexing():
    with mcpl.MCPLFile(example_file, blocklength=300) as f:
        f.read_block()
        b = f.read_block()
        print(f'second block: {len(b)} particles at offset {b.file_offset}')
        for sel, desc in [ (slice(10,20), '[10:20]'),
                           (slice(None,None,2), '[::2]'),
                           (np.array([5,3,5]), '[[5,3,5]]'),
                           (b.pdgcode == 22, '[pdgcode==22]'),
                           (slice(0,0), '[0:0]') ]:
            s = b[sel]
            assert isinstance(s, mcpl.MCPLParticleBlock)
            assert np.array_equal(s.ekin, b.ekin[sel]) and np.array_equal(s.position, b.position[sel])
            print(f'  block{desc}: {len(s)} particles, offset {s.file_offset}, '
                  f'pdgcodes {sorted(set(s.pdgcode.tolist()))}')
        s = b[b.ekin < 0.1][2:4]
        print(f'  nested selection: {len(s)} particles, ekin={np.array2string(s.ekin,precision=5)}')
        p = b[10:20][3]
        assert p.ekin == b[13].ekin
        print(f'  single particle of selection: ekin={p.ekin:.6g}')

def test_transfer_and_edit():
    #Transfer of selected blocks must keep the packed data unchanged:
    with mcpl.MCPLFile(example_file, blocklength=128) as f, mcpl.MCPLOutFile('sel.mcpl') as o:
        o.transfer_metadata(f)
        for b in f.particle_blocks:
            o.add_particles( b[b.pdgcode==2112] )
    _, d = raw('sel.mcpl')
    _, dref = raw(example_file)
    with mcpl.MCPLFile(example_file) as f:
        isn = f.read_block().pdgcode == 2112
    print(f'transferred {len(d)} neutrons, packed data identical: {np.array_equal(d, dref[isn])}')
    assert np.array_equal(d, dref[isn])
    #Edits of some fields keep the packed values of the others unchanged:
    with mcpl.MCPLFile(example_file) as f, mcpl.MCPLOutFile('edit.mcpl') as o:
        o.transfer_metadata(f)
        for b in f.particle_blocks:
            o.add_particles( b, x = -b.y, y = b.x, weight = 2.0 )
    _, d = raw('edit.mcpl')
    with mcpl.MCPLFile(example_file) as f:
        b = f.read_block()
    same = [ k for k in d.dtype.names if np.array_equal(d[k], dref[k]) ]
    print(f'edit of x, y, weight: unchanged packed fields: {same}')
    with mcpl.MCPLFile('edit.mcpl') as f:
        e = f.read_block()
    assert np.array_equal(e.x, (-b.y).astype(np.float32)) and np.array_equal(e.y, b.x)
    assert np.all(e.weight == 2.0)
    #Edits of the direction and ekin:
    with mcpl.MCPLFile(example_file) as f, mcpl.MCPLOutFile('edit2.mcpl') as o:
        for b in f.particle_blocks:
            n = b[b.pdgcode==2112]
            o.add_particles( n, ux = -n.uy, uy = n.ux, wavelength = 4.0 )
    with mcpl.MCPLFile('edit2.mcpl') as f:
        e = f.read_block()
    n = b[b.pdgcode==2112]
    ok = ( np.allclose(e.ux, -n.uy, atol=1e-6) and np.allclose(e.uy, n.ux, atol=1e-6)
           and np.allclose(e.uz, n.uz, atol=1e-6) and np.allclose(e.wavelength, 4.0, rtol=1e-6) )
    print(f'edit of direction and wavelength: {len(e)} particles, as expected: {ok}')
    assert ok
    #Errors:
    with mcpl.MCPLFile(example_file) as f:
        b = f.read_block()
    o = mcpl.MCPLOutFile('err.mcpl')
    for kw in [ { 'wavelength': 1.8 },
                { 'wavelength': 1.8, 'ekin': 1.0 },
                { 'x': np.zeros(3) },
                { 'foo': 1.0 } ]:
        try:
            o.add_particles( b, **kw )
            print(f'add_particles(block,{sorted(kw)}): no error')
        except (mcpl.MCPLError, TypeError) as e:
            print(f'add_particles(block,{sorted(kw)}): {type(e).__name__}: {e}')
    o.close()

def test_file_indices():
    with mcpl.MCPLFile(example_file, blocklength=300) as f:
        f.read_block()
        b = f.read_block()
        s = b[b.pdgcode == 22][1:3]
        print(f'file_indices of selection: {s.file_indices}, of particles:'
              f' {[p.file_index for p in s.particles]}')
        assert np.array_equal(s.file_indices, b.file_indices[b.pdgcode == 22][1:3])

if __name__ == '__main__':
    test_block_indexing()
    test_file_indices()
    test_transfer_and_edit()
