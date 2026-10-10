
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

# Test the select and edit arguments of MCPLFile and MCPLOutFile, and the
# blocks of edited particles.

import pathlib
import shutil

import mcpldev as mcpl
import numpy as np
from MCPLTestUtils.dirs import test_data_dir

shutil.copy(test_data_dir.parent.parent.joinpath('examples','example.mcpl'),'example.mcpl')
ex = 'example.mcpl'

def same_file(f1, f2):
    return pathlib.Path(f1).read_bytes() == pathlib.Path(f2).read_bytes()

def test_read():
    ref = mcpl.MCPLFile(ex).read_block()
    isn = ref.pdgcode == 2112
    f = mcpl.MCPLFile(ex, blocklength=100, select='pdgcode == neutron')
    print(f'select={f.select!r} edit={f.edit!r} nparticles={f.nparticles}')
    lens = [ len(b) for b in f.particle_blocks ]
    print(f'block lengths with blocklength=100: {lens}')
    assert sum(lens) == isn.sum()
    idx = np.concatenate([ b.file_indices for b in f.particle_blocks ])
    assert np.array_equal(idx, np.flatnonzero(isn))
    ps = list(f.particles)
    assert [ p.file_index for p in ps ] == list(np.flatnonzero(isn))
    assert all( p.ekin == ref.ekin[p.file_index] for p in ps[:20] )
    f.rewind()
    print(f'first particle after rewind: {f.read().file_index}')
    try:
        f.skip_forward(5)
    except mcpl.MCPLError as e:
        print(f'skip_forward: {e}')
    g = mcpl.MCPLFile(ex, select='pdgcode == neutron', edit='z += 1m, rotate_z(90deg)')
    b = g.read_block()
    n = ref[isn]
    ok = ( np.allclose(b.z, n.z+100) and np.allclose(b.x, -n.y) and np.allclose(b.ux, -n.uy)
           and np.allclose(b.position[:,0], -n.y) and np.allclose(b.direction[:,1], n.ux)
           and np.allclose(b.polarisation, 0) and np.array_equal(b.ekin, n.ekin) )
    print(f'edited block ({type(b).__name__}) as expected: {ok}')
    assert ok
    sub = b[b.ekin < 0.1]
    ok = ( np.allclose(sub.z, n.z[n.ekin<0.1]+100)
           and np.array_equal(sub.file_indices, np.flatnonzero(isn)[n.ekin<0.1]) )
    print(f'selection from edited block: {len(sub)} particles, as expected: {ok}')
    assert ok
    p = sub[2]
    print(f'particle {p.file_index}: z={p.z:g} x={p.x:.6g} y={p.y:.6g}')
    mcpl.dump_file(ex, header=False, limit=3, select='pdgcode == gamma', edit='x = 0')
    mcpl.dump_stats(mcpl.collect_stats(mcpl.MCPLFile(ex, select='pdgcode == neutron',
                                                     edit='z += 1m'),
                                       bin_data=False, select='ekin < 1MeV'))

def test_write():
    with mcpl.MCPLOutFile('a.mcpl') as o:
        for blk in mcpl.MCPLFile(ex, select='pdgcode == neutron', edit='z += 1m').particle_blocks:
            o.add_particles(blk)
    with mcpl.MCPLOutFile('b.mcpl') as o:
        for blk in mcpl.MCPLFile(ex).particle_blocks:
            s = blk[blk.pdgcode == 2112]
            o.add_particles(s, z = s.z + 100)
    with mcpl.MCPLOutFile('c.mcpl', select='pdgcode == neutron', edit='z += 1m') as o:
        for blk in mcpl.MCPLFile(ex).particle_blocks:
            o.add_particles(blk)
    with mcpl.MCPLOutFile('d.mcpl', select='pdgcode == neutron', edit='z += 1m') as o:
        for p in mcpl.MCPLFile(ex).particles:
            o.add_particle(p)
    print('edited blocks written like explicit field values:', same_file('a.mcpl','b.mcpl'))
    print('MCPLOutFile with select and edit gives the same:', same_file('a.mcpl','c.mcpl'),
          same_file('a.mcpl','d.mcpl'))
    assert same_file('a.mcpl','b.mcpl') and same_file('a.mcpl','c.mcpl') and same_file('a.mcpl','d.mcpl')
    #Fields given with add_particles are applied before the selection and edit:
    with mcpl.MCPLOutFile('e.mcpl', select='z > 50cm', edit='weight *= 2') as o:
        for blk in mcpl.MCPLFile(ex).particle_blocks:
            o.add_particles(blk, z = np.where(blk.pdgcode == 22, 100.0, 0.0))
    e = mcpl.MCPLFile('e.mcpl').read_block()
    print(f'fields then selection and edit: {len(e)} particles, weights {set(e.weight.tolist())},'
          f' pdgcodes {set(e.pdgcode.tolist())}')
    #Particles given as arrays:
    with mcpl.MCPLOutFile('r.mcpl', select='ekin > 1MeV', edit='weight *= 2, x = 2cm') as o:
        o.add_particles(direction=(0,0,1), ekin=[0.5,1.5,2.5], weight=1.0, pdgcode=2112)
        o.add_particle(direction=(0,0,1), ekin=3.0, weight=1.0, pdgcode=22)
        o.add_particle(direction=(0,0,1), ekin=0.1, weight=1.0, pdgcode=22)
    r = mcpl.MCPLFile('r.mcpl').read_block()
    print(f'arrays: ekin={r.ekin} weight={r.weight} x={r.x} pdgcode={r.pdgcode}')
    for kw in ( {'select':'x > 2'}, {'edit':'x = 2'}, {'select':'wavelength > 1Aa'} ):
        try:
            with mcpl.MCPLOutFile('err.mcpl', **kw) as o:
                for blk in mcpl.MCPLFile(ex).particle_blocks:
                    o.add_particles(blk)
            print(f'MCPLOutFile({kw}): no error')
        except mcpl.MCPLError as err:
            print(f'MCPLOutFile({kw}): {err}')

test_read()
test_write()
