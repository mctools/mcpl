
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

# Test the MCPLOutFile class by comparing the files it writes with files
# written by the C library, and test its API.

import gzip
import itertools
import pathlib

import mcpldev as mcpl
import numpy as np
from MCPLTestUtils.dirs import test_data_dir
from MCPLTestUtils.loadlib import getlib

lib = getlib('pywriter')

def same_file(f1, f2):
    return pathlib.Path(f1).read_bytes() == pathlib.Path(f2).read_bytes()

def reference_files():
    for f in sorted(itertools.chain(test_data_dir.joinpath('ref').glob('*.mcpl*'),
                                    test_data_dir.joinpath('reffmt2').glob('*.mcpl*'))):
        if not any(s in f.name for s in ('bad','crash','truncated','statunsupported')):
            yield f

def test_reference_files():
    for f in reference_files():
        name = '/'.join(f.parts[-2:])
        orig = f.read_bytes()
        if not orig.startswith(b'MCPL'):
            orig = gzip.decompress(orig)
        with mcpl.MCPLFile(f, raw_strings=True, blocklength=7) as src:
            with mcpl.MCPLOutFile('xfer.mcpl') as o:
                o.transfer_metadata(src)
                for b in src.particle_blocks:
                    o.add_particles(b)
            exact = ( pathlib.Path('xfer.mcpl').read_bytes() == orig )
            src.rewind()
            with mcpl.MCPLOutFile('repack_py.mcpl') as o:
                o.transfer_metadata(src)
                for b in src.particle_blocks:
                    o.add_particles(position=b.position, direction=b.direction,
                                    polarisation=b.polarisation, ekin=b.ekin,
                                    time=b.time, weight=b.weight,
                                    pdgcode=b.pdgcode, userflags=b.userflags)
            version = src.version
        lib.mcpltest_repack(str(f),'repack_c.mcpl')
        repack_same = same_file('repack_py.mcpl','repack_c.mcpl')
        print(f'{name} (MCPL-{version}): exact transfer reproduces file: {exact},'
              f' repacking identical to C: {repack_same}')
        assert repack_same
        assert exact == (version == 3)

def raw_particles(n):
    rng = np.random.default_rng(1)
    d = rng.normal(size=(n,3))
    d /= np.linalg.norm(d,axis=1)[:,None]
    edge = np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1],
                     [0.0,-0.0,1],[-0.0,0,-1],[0,1,-0.0],[0,-1,0.0],
                     [1/np.sqrt(3)]*3,[-1/np.sqrt(2),1/np.sqrt(2),0],
                     [0.6,0.8,0],[0.8,0,-0.6],[0,0.6,-0.8]],float)
    d[:len(edge)] = edge
    rec = np.zeros(n, dtype=[('v','f8',(12,)),('pdg','i4'),('uf','u4')])
    v = rec['v']
    v[:,0:3] = rng.normal(size=(n,3)) * 10.0**rng.integers(-30,30,size=(n,1))
    v[:,3:6] = d
    v[:,6:9] = rng.normal(size=(n,3))
    v[:,9] = np.abs(rng.normal(size=n)) * 10.0**rng.integers(-12,6,size=n)
    v[:20,9] = 0.0
    v[:,10] = rng.random(n) * 1e3
    v[:,11] = rng.random(n) * 5
    rec['pdg'] = rng.choice([2112,22,-11,11,-2147483648,2147483647,1000922350],size=n)
    rec['uf'] = rng.integers(0,2**32,size=n,dtype=np.uint64).astype(np.uint32)
    rec.tofile('raw.bin')
    return { 'x': v[:,0], 'y': v[:,1], 'z': v[:,2], 'direction': v[:,3:6],
             'polarisation': v[:,6:9], 'ekin': v[:,9], 'time': v[:,10],
             'weight': v[:,11], 'pdgcode': rec['pdg'], 'userflags': rec['uf'] }

all_opts = ['', 'd', 'p', 'u', 'P', 'W', 'dpu', 'dPW', 'puPW', 'dpuPW']

def opts_kwargs(opts):
    return { 'opt_singleprec': 'd' not in opts,
             'opt_polarisation': 'p' in opts,
             'opt_userflags': 'u' in opts,
             'opt_universalpdgcode': 2112 if 'P' in opts else 0,
             'opt_universalweight': 2.5 if 'W' in opts else 0 }

def test_raw_values():
    n = 3000
    fields = raw_particles(n)
    for opts in all_opts:
        lib.mcpltest_writefromraw('raw.bin','raw_c.mcpl',opts or '-')
        kw = dict( sourcename='writefromraw', comments=['a comment'],
                   stat_sum={'nsim':-1}, blobs={'blobkey':b'abc\0d'},
                   **opts_kwargs(opts) )
        with mcpl.MCPLOutFile('raw_py_blocks.mcpl', **kw) as o:
            o.add_particles(**{k:v[:1000] for k,v in fields.items()})
            o.add_particles(**{k:v[1000:] for k,v in fields.items()})
            o.hdr_add_stat_sum('nsim', 12345.0)
        with mcpl.MCPLOutFile('raw_py_single.mcpl', blocklength=100, **kw) as o:
            for i in range(n):
                o.add_particle(**{k:v[i] for k,v in fields.items()})
            o.hdr_add_stat_sum('nsim', 12345.0)
        same_blocks = same_file('raw_py_blocks.mcpl','raw_c.mcpl')
        same_single = same_file('raw_py_single.mcpl','raw_c.mcpl')
        print(f'Options "{opts}": identical to C with add_particles: {same_blocks},'
              f' with add_particle: {same_single}')
        assert same_blocks and same_single

def test_transfers():
    #Transfer particles into files with other settings, compared with
    #mcpl_transfer_last_read_particle in C:
    fields = raw_particles(500)
    for src_opts in ['', 'dpu']:
        lib.mcpltest_writefromraw('raw.bin','src.mcpl',src_opts or '-')
        for opts in all_opts:
            if 'P' in opts or 'W' in opts:
                continue#universal pdgcode/weight do not match source
            lib.mcpltest_transfer('src.mcpl','xfer_c.mcpl',opts or '-')
            with mcpl.MCPLFile('src.mcpl', blocklength=77) as src:  # noqa: SIM117
                with mcpl.MCPLOutFile('xfer_py.mcpl', **opts_kwargs(opts)) as o:
                    for b in src.particle_blocks:
                        o.add_particles(b)
            same = same_file('xfer_py.mcpl','xfer_c.mcpl')
            print(f'Transfer from "{src_opts}" to "{opts}": identical to C: {same}')
            assert same
    #Double to single precision: packed direction+ekin are narrowed:
    lib.mcpltest_writefromraw('raw.bin','src.mcpl','dpu')
    with mcpl.MCPLFile('src.mcpl') as src, mcpl.MCPLOutFile('xfer_py.mcpl') as o:
        for b in src.particle_blocks:
            o.add_particles(b)
    with mcpl.MCPLFile('src.mcpl') as src, mcpl.MCPLFile('xfer_py.mcpl') as res:
        b, r = src.read_block(), res.read_block()
        assert np.array_equal(r.ekin, b.ekin.astype(np.float32))
        assert np.allclose(r.direction, b.direction, atol=1e-6)
        assert np.array_equal(r.x, b.x.astype(np.float32))
        assert np.array_equal(r.pdgcode, fields['pdgcode'])
        print('Transfer from double to single precision gives expected values')
    #Single particles from MCPLFile.read(), including into a file with universal
    #pdgcode where only particles with that pdgcode are accepted:
    with mcpl.MCPLFile('src.mcpl') as src:  # noqa: SIM117
        with mcpl.MCPLOutFile('filtered.mcpl', opt_universalpdgcode=2112) as o:
            while ( p := src.read() ) is not None:
                if p.pdgcode == 2112:
                    o.add_particle(p)
    with mcpl.MCPLFile('filtered.mcpl') as f:
        print(f'Filtered {f.nparticles} neutrons with universal pdgcode {f.opt_universalpdgcode}')
        assert f.nparticles == int(np.sum(fields['pdgcode'] == 2112))

def expect_error(fct, *a, **kw):
    try:
        fct(*a, **kw)
    except mcpl.MCPLError as e:
        print(f'  Got expected error: {e}')
        return
    raise AssertionError('No error raised')

def test_api():
    #Mix keyword arguments and method calls:
    with mcpl.MCPLOutFile('api', sourcename='MySim', comments=['first comment'],
                          stat_sum={'nsim':-1}, opt_polarisation=True) as o:
        print(f'Writing to {o.filename}')
        o.hdr_add_comment('second comment')
        o.hdr_add_data('cfg', b'\x00\x01binary')
        o.enable_universal_weight(1.5)
        o.enable_polarisation()#already enabled, ignored like in C
        o.add_particle(position=(1,2,3), direction=(0,0,1), ekin=0.025,
                       pdgcode=2112, polarisation=(0,1,0))
        o.add_particles(direction=[[1,0,0],[0,1,0]], ekin=[1.0,2.0], pdgcode=22)
        print(f'  nparticles={o.nparticles} particlesize={o.particlesize}')
        expect_error(o.hdr_add_comment,'too late')
        expect_error(o.enable_userflags)
        expect_error(o.hdr_add_stat_sum,'other',1.0)
        o.hdr_add_stat_sum('nsim', 1000)
        print(f'  stat_sum={dict(o.stat_sum)}')
    with mcpl.MCPLFile('api.mcpl') as f:
        f.dump_hdr()
        f.dump_particles(limit=0)
        print(f'blobs={f.blobs} stat_sum={dict(f.stat_sum)}')
    #Errors:
    print('Errors:')
    with mcpl.MCPLOutFile('err.mcpl') as o:
        expect_error(o.add_particles, direction=(1,1,0))
        expect_error(o.add_particles, direction=(1,0,0), ekin=-1.0)
        expect_error(o.add_particle, direction=(0,0.5,0))
        expect_error(o.add_particles, direction=[[1,0,0]]*3, ekin=[1.0,2.0])
        expect_error(o.add_particles, position=(0,0,0), x=1.0, direction=(1,0,0))
        expect_error(o.add_particles, direction=(1,0,0), pdgcode=2**31)
    with mcpl.MCPLOutFile('err.mcpl') as o:
        expect_error(o.hdr_add_comment,'stat:something')
        expect_error(o.hdr_add_comment,'stat:sum:bad')
        expect_error(o.hdr_add_stat_sum,'bad key',1.0)
        expect_error(o.hdr_add_stat_sum,'key',-2.0)
        o.hdr_add_data('k',b'x')
        expect_error(o.hdr_add_data,'k',b'y')
        expect_error(o.enable_universal_pdgcode,0)
        expect_error(o.enable_universal_weight,-1.0)
        o.enable_universal_pdgcode(22)
        expect_error(o.enable_universal_pdgcode,2112)
        o.hdr_add_stat_sum('a',1.0)
        expect_error(o.hdr_add_comment,'stat:sum:a:' + ' '*23 + '2')
        o.hdr_scale_stat_sums(2.0)
        print(f'  stat_sum after scaling={dict(o.stat_sum)}')
        expect_error(o.hdr_scale_stat_sums,0.0)
    expect_error(mcpl.MCPLOutFile,'.mcpl')
    #Gzipped output:
    with mcpl.MCPLOutFile('gz') as o:
        o.add_particles(direction=(0,0,1), ekin=np.linspace(1,2,5))
    o = mcpl.MCPLOutFile('gz2', opt_singleprec=False)
    o.add_particles(direction=(0,0,1), ekin=np.linspace(1,2,5))
    assert o.closeandgzip()
    with mcpl.MCPLFile('gz2.mcpl.gz') as f:
        print(f'gz2.mcpl.gz: {f.nparticles} particles, ekin={f.read_block().ekin}')
    assert not pathlib.Path('gz2.mcpl').exists()

def test_example():
    #Run examples/pyexample_writemcpl with the mcpl module being tested:
    import sys
    f = test_data_dir.parent.parent.joinpath('examples','pyexample_writemcpl')
    code = f.read_text().replace('\nimport mcpl\n','\nimport mcpldev as mcpl\n')
    assert 'import mcpldev as mcpl' in code
    sys.argv = [ str(f), 'example_output' ]
    exec(compile(code,str(f),'exec'),{'__name__':'__main__'})  # noqa: S102
    with mcpl.MCPLFile('example_output.mcpl.gz') as f:
        print(f'pyexample_writemcpl wrote {f.nparticles} particles from'
              f' "{f.sourcename}" with comments {f.comments}')

test_reference_files()
test_raw_values()
test_transfers()
test_api()
test_example()
