
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

# Files with the other byte order (big-endian files on little-endian
# platforms, and vice versa) can be read, merged in place and repaired with
# mcpl-python (the C library refuses them). The files are made by converting
# files to the other byte order.

import pathlib
import struct

import mcpldev as mcpl
import numpy as np
from MCPLTestUtils.dirs import test_data_dir


def to_other_endian( src, dst ):
    """Write a copy of the MCPL file src with the other byte order"""
    with mcpl.MCPLFile(src, raw_strings = True) as f:
        e = '>' if f.endianness == 'L' else '<'
        out = bytearray( b'MCPL' + b'%03d' % f.version
                         + ( b'B' if e == '>' else b'L' ) )
        out += struct.pack( e + 'Q', f.nparticles )
        uf = int(f.opt_userflags) | ( 2 if f.userdata_layout else 0 )
        out += struct.pack( e + '5I', len(f.comments), len(f.blobs), uf,
                            int(f.opt_polarisation), int(f.opt_singleprec) )
        out += struct.pack( e + 'i', f.opt_universalpdgcode )
        out += struct.pack( e + '2I', f.particlesize,
                            1 if f.opt_universalweight else 0 )
        if f.opt_universalweight:
            out += struct.pack( e + 'd', f.opt_universalweight )
        def add( b ):
            out.extend( struct.pack( e + 'I', len(b) ) + b )
        if f.userdata_layout:
            add( f.userdata_layout.encode('ascii') )
        add( f.sourcename )
        for c in f.comments:
            add( c )
        for k in f.blobs:
            add( k )
        for v in f.blobs.values():
            add( v )
        for b in f.particle_blocks:
            out += b._data.astype( b._data.dtype.newbyteorder(e) ).tobytes()
    pathlib.Path(dst).write_bytes(out)

fields = ( 'x', 'y', 'z', 'ux', 'uy', 'uz', 'polx', 'poly', 'polz', 'ekin',
           'time', 'weight', 'pdgcode', 'userflags' )

def contents( fn ):
    """Header and particles of a file, for comparisons"""
    with mcpl.MCPLFile(fn) as f:
        hdr = ( f.nparticles, f.sourcename, f.comments, dict(f.blobs),
                dict(f.stat_sum), f.userdata_layout )
        blocks = list(f.particle_blocks)
        parts = { k : np.concatenate([getattr(b,k) for b in blocks])
                  for k in fields }
        if f.userdata_layout:
            ud = np.concatenate([b.userdata for b in blocks])
            for name in ud.dtype.names:
                parts['userdata.'+name] = ud[name]
        return hdr, parts

def same( c1, c2 ):
    return ( c1[0] == c2[0] and c1[1].keys() == c2[1].keys()
             and all( np.array_equal(c1[1][k],c2[1][k]) for k in c1[1] ) )

def main():
    #A file with userdata and stat:sum entries, and reference files:
    with mcpl.MCPLOutFile('ud.mcpl', userdata_layout = 'temp:float32:K,n:uint16',
                          stat_sum = {'nsrc':10.0}, opt_polarisation = True,
                          opt_userflags = True ) as f:
        n = 7
        f.hdr_add_comment('a comment')
        f.hdr_add_data('key',b'blob data')
        f.add_particles( pdgcode = 2112, ekin = 1.0 + np.arange(n),
                         direction = (0,0,1), polarisation = (0,1,0),
                         userflags = 5,
                         userdata = { 'temp' : 300.0 + np.arange(n),
                                      'n' : np.arange(n) } )
    sources = [ 'ud.mcpl', test_data_dir.joinpath('example.mcpl'),
                test_data_dir.joinpath('ref','miscphys.mcpl.gz') ]
    for i, src in enumerate(sources):
        other = f'other{i}.mcpl'
        to_other_endian( src, other )
        assert mcpl.MCPLFile(other).endianness != mcpl.MCPLFile(src).endianness
        assert same( contents(src), contents(other) )
        print(f'{pathlib.Path(src).name}: the copy with the other byte order'
              ' is read identically')

    #Merging in place (with stat:sum entries and userdata):
    to_other_endian( 'ud.mcpl', 'm1.mcpl' )
    to_other_endian( 'ud.mcpl', 'm2.mcpl' )
    mcpl.merge_inplace( 'm1.mcpl', 'm2.mcpl' )
    hdr, parts = contents( 'm1.mcpl' )
    ref_hdr, ref_parts = contents( 'ud.mcpl' )
    assert hdr[0] == 2 * ref_hdr[0] and hdr[4] == {'nsrc':20.0}, hdr
    assert all( np.array_equal( parts[k], np.concatenate([ref_parts[k]]*2) )
                for k in parts )
    print(f'merge_inplace: {hdr[0]} particles, stat:sum {hdr[4]}')

    #Repairing files which were not closed properly, or truncated:
    for what, nparticles, cut in ( ('not closed', 0, 0),
                                   ('truncated', None, 10) ):
        to_other_endian( 'ud.mcpl', 'r.mcpl' )
        d = bytearray(pathlib.Path('r.mcpl').read_bytes())
        if nparticles is not None:
            d[8:16] = struct.pack('>Q' if d[7:8] == b'B' else '<Q', nparticles)
        pathlib.Path('r.mcpl').write_bytes(bytes(d[:len(d)-cut]))
        mcpl.repair('r.mcpl')
        hdr, parts = contents( 'r.mcpl' )
        nexpected = ref_hdr[0] - ( 1 if cut else 0 )
        assert hdr[0] == nexpected, (what, hdr[0])
        assert all( np.array_equal( parts[k], ref_parts[k][:nexpected] )
                    for k in parts )
        print(f'repair ({what}): {hdr[0]} particles, stat:sum {hdr[4]}')

if __name__ == '__main__':
    main()
