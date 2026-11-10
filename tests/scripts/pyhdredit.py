
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

# Test editing headers of MCPLOutFile after transfer_metadata (before the
# first particle): comments, blobs, stat:sum entries, and the storage of the
# particles.

import pathlib

import mcpldev as mcpl
import numpy as np


def make_file( fn, stat_sum, comments = (), blobs = (), **kw ):
    rng = np.random.default_rng(len(fn))
    n = 50
    d = rng.normal(size=(n,3))
    d /= np.linalg.norm(d,axis=1)[:,None]
    with mcpl.MCPLOutFile(fn, stat_sum = stat_sum, **kw) as f:
        for c in comments:
            f.hdr_add_comment(c)
        for k, v in blobs:
            f.hdr_add_data(k,v)
        f.enable_polarisation()
        f.enable_userflags()
        f.add_particles( position = rng.normal(size=(n,3)), direction = d,
                         polarisation = d, ekin = rng.uniform(0.1,1.0,n),
                         time = rng.uniform(0,1,n), weight = rng.uniform(0.5,2.0,n),
                         pdgcode = 2112, userflags = np.arange(n) )

def describe( fn ):
    with mcpl.MCPLFile(fn) as f:
        print(f'  {fn}: {f.nparticles} particles, comments {f.comments},'
              f' blobs {sorted(f.blobs)}, stat_sum {dict(f.stat_sum)},'
              f' single precision {f.opt_singleprec}, polarisation {f.opt_polarisation},'
              f' userflags {f.opt_userflags}, universal pdgcode {f.opt_universalpdgcode},'
              f' universal weight {f.opt_universalweight}, userdata {f.userdata_layout!r},'
              f' particle size {f.particlesize}')

def copy_with( fin_name, fout_name, change ):
    """Copy the file, with the header changed by change(fout)"""
    with mcpl.MCPLFile(fin_name) as fin, mcpl.MCPLOutFile(fout_name) as fout:
        fout.transfer_metadata(fin, editable = True)
        change(fout)
        for block in fin.particle_blocks:
            fout.add_particles(block)

def expect_error( fct, *args ):
    try:
        fct(*args)
    except mcpl.MCPLError as e:
        print(f'  error: {e}')
        return
    raise SystemExit('expected an error')

def test_merge_blocked_by_statsum():
    print('Files with different stat:sum entries can not be merged:')
    make_file('mcstas.mcpl', { 'initial_ray_count' : 1e6 })
    make_file('geant4.mcpl', { 'geant4_nevts' : 1e4 })
    print('  can_merge:', mcpl.can_merge('mcstas.mcpl','geant4.mcpl'))
    def remove_statsums( fout ):
        for key in list(fout.stat_sum):
            fout.hdr_remove_stat_sum(key)
    copy_with('mcstas.mcpl','mcstas_nostat.mcpl',remove_statsums)
    copy_with('geant4.mcpl','geant4_nostat.mcpl',remove_statsums)
    print('  without them, can_merge:', mcpl.can_merge('mcstas_nostat.mcpl','geant4_nostat.mcpl'))
    mcpl.merge_files('merged.mcpl',['mcstas_nostat.mcpl','geant4_nostat.mcpl'])
    describe('merged.mcpl')
    #(the particles are unchanged):
    with mcpl.MCPLFile('mcstas.mcpl') as a, mcpl.MCPLFile('mcstas_nostat.mcpl') as b:
        print('  same particles:', a.read_block()._data.tobytes() == b.read_block()._data.tobytes())

def test_single_precision():
    print('Single precision:')
    make_file('double.mcpl', { 'n' : 50.0 }, opt_singleprec = False)
    copy_with('double.mcpl','single.mcpl',lambda fout : fout.enable_doubleprec(False))
    for fn in ( 'double.mcpl', 'single.mcpl' ):
        describe(fn)
        print(f'    {pathlib.Path(fn).stat().st_size} bytes')
    with mcpl.MCPLFile('double.mcpl') as a, mcpl.MCPLFile('single.mcpl') as b:
        ea, eb = a.read_block().ekin, b.read_block().ekin
        print('  ekin as float32:', np.array_equal(eb,ea.astype(np.float32)))

def test_comments_and_blobs():
    print('Comments, blobs, and the source name:')
    make_file('orig.mcpl', { 'n' : 50.0 }, comments = [ 'first', 'second', 'third' ],
              blobs = [ ( 'a', b'aaa' ), ( 'b', b'bbb' ) ])
    def change( fout ):
        #(the stat:sum entry is among the comments, and is kept):
        c = fout.comments
        c[c.index('second')] = 'a longer second comment'
        c.remove('third')
        fout.hdr_set_comments([ 'new first', *c ])
        #(a blob is replaced in its place, another removed, and one added):
        fout.hdr_add_data('a',b'new data of a')
        fout.hdr_remove_data('b')
        fout.hdr_add_data('c',b'ccc')
        fout.hdr_set_srcname('Edited')
    copy_with('orig.mcpl','edited.mcpl',change)
    describe('orig.mcpl')
    describe('edited.mcpl')
    with mcpl.MCPLFile('edited.mcpl') as f:
        print(f'  source name {f.sourcename!r}, blobs in order {list(f.blobs.items())}')

def test_storage():
    print('Storage:')
    def change( fout ):
        fout.enable_polarisation(False)
        fout.enable_userflags(False)
        fout.enable_universal_pdgcode(2112)
    copy_with('orig.mcpl','storage.mcpl',change)
    describe('storage.mcpl')
    def change_back( fout ):
        fout.enable_universal_pdgcode(22)
        fout.enable_universal_pdgcode(None)
        fout.enable_universal_weight(2.0)
        fout.enable_universal_weight(None)
    copy_with('storage.mcpl','storage2.mcpl',change_back)
    describe('storage2.mcpl')

def test_userdata():
    print('Userdata:')
    rng = np.random.default_rng(1)
    with mcpl.MCPLOutFile('ud.mcpl', userdata_layout = 'temp:float32:K,origin:float32[3]:cm') as f:
        f.add_particles( ekin = rng.uniform(0.1,1.0,10), uz = 1.0, weight = 1.0,
                         pdgcode = 2112,
                         userdata = { 'temp' : rng.uniform(1,300,10),
                                      'origin' : rng.normal(size=(10,3)) } )
    #(removing the userdata):
    copy_with('ud.mcpl','ud_none.mcpl',lambda fout : fout.enable_userdata(None))
    describe('ud_none.mcpl')
    #(another layout: the userdata of the particles must be given):
    with mcpl.MCPLFile('ud.mcpl') as fin, mcpl.MCPLOutFile('ud_temp.mcpl') as fout:
        fout.transfer_metadata(fin, editable = True)
        fout.enable_userdata('temp:float32:K')
        for block in fin.particle_blocks:
            expect_error(fout.add_particles,block)
            fout.add_particles(block, userdata = { 'temp' : block.userdata['temp'] })
    describe('ud_temp.mcpl')

def test_not_editable():
    print('Without editable=True, the settings copied can not be changed:')
    with mcpl.MCPLOutFile('noedit0.mcpl') as f:
        f.transfer_metadata('double.mcpl')
        for fct in ( f.enable_polarisation, f.enable_doubleprec, f.enable_userflags ):
            expect_error(fct,False)
    with mcpl.MCPLOutFile('noedit.mcpl') as f:
        f.transfer_metadata('storage.mcpl')
        expect_error(f.enable_universal_pdgcode,22)
        expect_error(f.enable_universal_pdgcode,None)
        expect_error(f.hdr_add_data,'b',b'replaced')
        #(but the comments, blobs, and stat:sum entries can):
        f.hdr_remove_data('a')
        f.hdr_remove_stat_sum('n')
        f.hdr_set_comments([ 'only this one' ])
        print('  comments', f.comments, 'blobs', sorted(f.blobs))
    with mcpl.MCPLOutFile('noedit2.mcpl') as f:
        f.enable_universal_weight(2.0)
        expect_error(f.enable_universal_weight,3.0)
        f.enable_userdata('a:uint8')
        expect_error(f.enable_userdata,'b:uint8')
        expect_error(f.enable_userdata,None)

def test_errors():
    print('Errors:')
    with mcpl.MCPLOutFile('err.mcpl', allow_overwrite = True) as f:
        f.transfer_metadata('orig.mcpl', editable = True)
        expect_error(f.hdr_remove_data,'nosuchkey')
        expect_error(f.hdr_remove_stat_sum,'nosuchkey')
        before = f.comments
        expect_error(f.hdr_set_comments,[ 'fine', 'stat:sum:bad' ])
        print('  comments unchanged after the error:', f.comments == before)
        expect_error(f.enable_universal_weight,-1.0)
        f.add_particle(ekin=1.0,uz=1.0,weight=1.0,pdgcode=2112)
        for fct, args in ( ( f.hdr_set_comments, ([],) ), ( f.hdr_remove_data, ('b',) ),
                           ( f.hdr_remove_stat_sum, ('n',) ), ( f.enable_polarisation, (False,) ),
                           ( f.enable_doubleprec, (True,) ), ( f.enable_userflags, (False,) ),
                           ( f.enable_universal_pdgcode, (22,) ), ( f.enable_userdata, (None,) ) ):
            if fct == f.enable_userdata:
                fct(*args)#(no change: the file has no userdata)
                continue
            expect_error(fct,*args)
        #(asking for the settings the file already has is fine):
        f.enable_polarisation(True)
        f.enable_userflags(True)

test_merge_blocked_by_statsum()
test_single_precision()
test_comments_and_blobs()
test_storage()
test_userdata()
test_not_editable()
test_errors()
