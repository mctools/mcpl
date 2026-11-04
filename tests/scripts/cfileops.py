
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


# The file operations of the C library (dumps, merges, in-place merges, forced
# merges, repairs, and gzipping), called directly (with the test library
# fileops), on the reference files and their failures. The command line is
# tested with mcpltool (tool and others).

import gzip
import shutil
import sys
from pathlib import Path

import mcpldev as mcpl
from MCPLTestUtils.dirs import test_data_dir
from MCPLTestUtils.loadlib import getlib

lib = getlib('fileops')

def copy( name, target = None, subdir = 'ref' ):
    """Copy of the reference file (in the directory, with its name or target)"""
    target = Path(target or name)
    shutil.copyfile( test_data_dir.joinpath(subdir,name), target )
    return target

def dump( fn, parts = 0, skip = 0, limit = 0 ):
    print(f'---- dump {fn} (parts {parts}, skip {skip}, limit {limit})', flush=True)
    #(the version of MCPL in the source names of forced merges is not shown,
    #so the log does not change with it):
    res = lib.mcpltest_dump(str(fn),parts,skip,limit,'dump.txt')
    if Path('dump.txt').exists():
        sys.stdout.buffer.write( Path('dump.txt').read_bytes()
                                 .replace(f'MCPL v{mcpl.__version__}'.encode(),
                                          b'MCPL v<current>') )
        Path('dump.txt').unlink()
    print(f'---- -> {res}', flush=True)

def merge( output, *files, force = False, keepuserflags = False ):
    how = 'forcemerge' + ( ' (keeping userflags)' if keepuserflags else '' ) if force else 'merge'
    print(f'---- {how} {" ".join(str(f) for f in files)} into {output}', flush=True)
    res = lib.mcpltest_merge(str(output),'\n'.join(str(f) for f in files),
                             int(force),int(keepuserflags))
    print(f'---- -> {res}', flush=True)
    return res == 'ok'

def merge_inplace( f1, f2 ):
    print(f'---- merge {f2} into {f1} (in place)', flush=True)
    print(f'---- -> {lib.mcpltest_merge_inplace(str(f1),str(f2))}', flush=True)

def repair( fn ):
    print(f'---- repair {fn}', flush=True)
    print(f'---- -> {lib.mcpltest_repair(str(fn))}', flush=True)

def gzip_file( fn ):
    print(f'---- gzip {fn}', flush=True)
    print(f'---- -> {lib.mcpltest_gzip(str(fn))}', flush=True)

def same( f1, f2 ):
    """Whether the files have the same contents (after decompressing)"""
    def data( f ):
        b = Path(f).read_bytes()
        return gzip.decompress(b) if str(f).endswith('.gz') else b
    return data(f1) == data(f2)

def test_dumps():
    #Header and particles, the header only, the particles only, and parts of
    #them, of files of each format and compression, and failures:
    f16 = copy('reffile_16.mcpl')
    dump(f16)
    dump(f16,parts=1)
    dump(f16,parts=2,skip=3,limit=2)
    dump(f16,skip=9)
    dump(f16,skip=20)
    dump(copy('reffile_16.mcpl','rf16_fmt2.mcpl','reffmt2'),limit=3)
    dump(copy('reffile_5.mcpl.gz'),limit=2)
    dump(copy('reffile_empty.mcpl'))
    dump(copy('reffile_empty.mcpl.gz'))
    for fn in ( 'reffile_crash.mcpl', 'reffile_truncated.mcpl', 'reffile_truncated.mcpl.gz',
                'reffile_bad1.mcpl', 'reffile_notreallygz.mcpl.gz' ):
        dump(copy(fn),limit=3)
    dump('nosuchfile.mcpl')
    Path('adirectory.mcpl').mkdir()
    dump('adirectory.mcpl')

def test_merges():
    #New files from compatible files (also gzipped), refusing existing
    #outputs, incompatible files, and wrong names:
    a, b = copy('reffile_5.mcpl','a.mcpl'), copy('reffile_5.mcpl.gz','b.mcpl.gz')
    print('can merge a and b:', lib.mcpltest_can_merge(str(a),str(b)))
    merge('ab.mcpl',a,b)
    dump('ab.mcpl',parts=1)
    merge('ab_gz.mcpl.gz',a,b)
    print('same particles in ab.mcpl and ab_gz.mcpl.gz:', same('ab.mcpl','ab_gz.mcpl.gz'))
    merge('ab.mcpl',a,b)
    merge('ab_wrongname.gz',a,b)
    f16 = copy('reffile_16.mcpl')
    print('can merge a and reffile_16:', lib.mcpltest_can_merge(str(a),str(f16)))
    merge('a16.mcpl',a,f16)
    merge('a.mcpl',a,b)
    merge('missing.mcpl',a,'nosuchfile.mcpl')
    print('can merge a and a missing file:', lib.mcpltest_can_merge(str(a),'nosuchfile.mcpl'))
    #(files of format versions 2 and 3, into a file of version 3):
    f16v2 = copy('reffile_16.mcpl','rf16_fmt2.mcpl','reffmt2')
    merge('mixed.mcpl',f16v2,f16)
    dump('mixed.mcpl',parts=1)
    #(the stat:sum entries are added up):
    s1, s2 = copy('ref_statsum.mcpl.gz','s1.mcpl.gz'), copy('ref_statsum.mcpl.gz','s2.mcpl.gz')
    merge('statsum_merged.mcpl',s1,s2)
    dump('statsum_merged.mcpl',parts=1)

def test_merges_inplace():
    #Appending to an uncompressed file, refusing gzipped files, other format
    #versions, and incompatible files:
    a, b = copy('reffile_5.mcpl','ia.mcpl'), copy('reffile_5.mcpl.gz','ib.mcpl.gz')
    merge_inplace(a,b)
    dump(a,parts=1)
    print('same as the merge into a new file:',
          merge('inew.mcpl',copy('reffile_5.mcpl','ic.mcpl'),b) and same(a,'inew.mcpl'))
    merge_inplace(b,a)
    merge_inplace(copy('reffile_16.mcpl','i16.mcpl'),copy('reffile_16.mcpl','i16_fmt2.mcpl','reffmt2'))
    merge_inplace(a,copy('reffile_16.mcpl','i16b.mcpl'))
    s1, s2 = copy('ref_statsum.mcpl.gz','is1.mcpl.gz'), copy('ref_statsum.mcpl.gz','is2.mcpl.gz')
    gzip_s1 = Path('is1.mcpl')
    gzip_s1.write_bytes(gzip.decompress(s1.read_bytes()))
    merge_inplace(gzip_s1,s2)
    dump(gzip_s1,parts=1)

def test_forcemerges():
    #Incompatible files merged by dropping what they do not share (userflags
    #only when asked to keep them):
    files = [ copy(fn) for fn in ( 'miscphys.mcpl.gz', 'gammas_uw.mcpl.gz', 'reffile_3.mcpl',
                                   'reffile_10.mcpl', 'reffile_13.mcpl' ) ]
    merge('forced.mcpl',*files,force=True)
    dump('forced.mcpl',parts=1)
    merge('forced_uf.mcpl',*files,force=True,keepuserflags=True)
    dump('forced_uf.mcpl',parts=1)
    #(compatible files are merged as usual):
    a, b = copy('reffile_5.mcpl','fa.mcpl'), copy('reffile_5.mcpl','fb.mcpl')
    merge('forced_compatible.mcpl',a,b,force=True)
    print('same as the usual merge:', merge('usual.mcpl',a,b) and same('usual.mcpl','forced_compatible.mcpl'))

def test_repairs():
    #Files which were not closed (some with stat:sum entries, which become -1),
    #refusing gzipped and complete files:
    for fn in ( 'reffile_crash.mcpl', 'reffile_crash_0p4.mcpl', 'reffile_crash_8p7.mcpl',
                'ref_statsum_crash.mcpl', 'reffile_truncated.mcpl' ):
        f = copy(fn,'repaired_' + fn)
        dump(f,parts=1)
        repair(f)
        dump(f,parts=1)
        repair(f)
    repair(copy('reffile_crash.mcpl.gz'))
    repair(copy('reffile_empty.mcpl','repaired_empty.mcpl'))
    repair('nosuchfile.mcpl')

def test_gzip():
    #Compressing a file (replacing it), and refusing missing files:
    f = copy('reffile_16.mcpl','tozip.mcpl')
    gzip_file(f)
    print('compressed:', not f.exists(), Path('tozip.mcpl.gz').exists(),
          '| same particles:', same('tozip.mcpl.gz',test_data_dir.joinpath('ref','reffile_16.mcpl')))
    gzip_file('nosuchfile.mcpl')

test_dumps()
test_merges()
test_merges_inplace()
test_forcemerges()
test_repairs()
test_gzip()
