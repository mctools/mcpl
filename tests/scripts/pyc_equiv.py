
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

# Check that the Python API (MCPLOutFile) gives the same results, printouts and
# errors as the C API, by running the same operations with both in separate
# directories and comparing everything.

import contextlib
import gzip
import io
import json
import math
import os
import pathlib
import shutil

import mcpldev as mcpl
from MCPLTestUtils.dirs import test_data_dir
from MCPLTestUtils.loadlib import getlib


def _c_child(resfile, fctname, args):
    lib = getlib('pywriter')
    prints = []
    def write_result(**kw):
        pathlib.Path(resfile).write_text(json.dumps(dict(prints=''.join(prints),**kw)))
    def on_print(msg):
        prints.append(msg)
    def on_error(msg):
        write_result(error=msg)
        os._exit(0)
    lib.mcpltestdetail_set_print_handler(on_print)
    lib.mcpltestdetail_set_error_handler(on_error)
    rv = getattr(lib,fctname)(*args)
    write_result(error=None, rv=rv)

def run_c(fctname, *args, cwd):
    """Run function from the C test library in a child process (since errors
    end the process). Returns (error message or None, printouts, return
    value)."""
    import multiprocessing as mp
    resfile = pathlib.Path(cwd).absolute().parent / 'c_result.json'
    if resfile.exists():
        resfile.unlink()
    oldcwd = pathlib.Path.cwd()
    os.chdir(cwd)
    try:
        p = mp.get_context(None).Process( target = _c_child,
                                          args = (str(resfile), fctname, args) )
        p.start()
        p.join()
    finally:
        os.chdir(oldcwd)
    r = json.loads(resfile.read_text())
    return r['error'], r['prints'], r.get('rv')

def run_py(fct, *args, cwd):
    oldcwd = pathlib.Path.cwd()
    os.chdir(cwd)
    out = io.StringIO()
    err, rv = None, None
    try:
        with contextlib.redirect_stdout(out):
            rv = fct(*args)
    except mcpl.MCPLError as e:
        err = str(e)
    finally:
        os.chdir(oldcwd)
    return err, out.getvalue(), rv

def norm(msg):
    #Function names in messages from the C API start with "mcpl_", and the C
    #function mcpl_create_outfile corresponds to the MCPLOutFile constructor:
    if msg is None:
        return None
    return ( msg.replace('mcpl_','').replace('MCPLOutFile','create_outfile')
             .replace('transfer_last_read_particle','add_particles').strip() )

def dir_contents(d):
    res = {}
    for f in sorted(pathlib.Path(d).iterdir()):
        data = f.read_bytes()
        if f.name.endswith('.gz') and data[:2] == b'\x1f\x8b':
            data = gzip.decompress(data)
        res[f.name] = data
    return res

input_dir = pathlib.Path('inputs').absolute()
ncases = 0
def compare( title, c_fct, c_args, py_fct, py_args = None, check_rv = True ):
    """Run C and Python versions of an operation in fresh copies of the input
    files and compare everything."""
    global ncases
    ncases += 1
    for d in ('c','py'):
        if pathlib.Path(d).exists():
            shutil.rmtree(d)
        shutil.copytree(input_dir, d)
    cerr, cprints, crv = run_c(c_fct, *c_args, cwd='c')
    perr, pprints, prv = run_py(py_fct, *(c_args if py_args is None else py_args), cwd='py')
    problems = []
    if norm(cerr) != norm(perr):
        problems.append(f'errors differ:\n      C: {cerr}\n     Py: {perr}')
    if norm(cprints) != norm(pprints):
        problems.append(f'printouts differ:\n      C: {cprints!r}\n     Py: {pprints!r}')
    if check_rv and cerr is None and perr is None and bool(crv) != bool(prv):
        problems.append(f'return values differ: C: {crv} Py: {prv}')
    if cerr is None:
        dc, dp = dir_contents('c'), dir_contents('py')
        if set(dc) != set(dp):
            problems.append(f'different files: C: {sorted(dc)} Py: {sorted(dp)}')
        else:
            for k in dc:
                if dc[k] != dp[k]:
                    problems.append(f'file {k} differs')
    outcome = f'error: {norm(cerr)}' if cerr else 'ok'
    print(f'{title}: {outcome}')
    for line in norm(cprints).splitlines():
        print(f'   | {line}')
    for p in problems:
        print(f'   PROBLEM: {p}')
    return not problems

################################################################################
# Writer API via scripts (one command per line, see mcpltest_script in C):

def py_script(outfile, script):
    o = mcpl.MCPLOutFile(outfile)
    try:
        for line in script.split('\n'):
            cmd, _, arg = line.partition(' ')
            if cmd == 'srcname':
                o.hdr_set_srcname(arg)
            elif cmd == 'comment':
                o.hdr_add_comment(arg)
            elif cmd == 'blob':
                key, _, data = arg.partition(' ')
                o.hdr_add_data(key, data.encode())
            elif cmd == 'statsum':
                key, _, val = arg.rpartition(' ')
                o.hdr_add_stat_sum(key, float(val))
            elif cmd == 'scale':
                o.hdr_scale_stat_sums(float(arg))
            elif cmd == 'userflags':
                o.enable_userflags()
            elif cmd == 'pol':
                o.enable_polarisation()
            elif cmd == 'dp':
                o.enable_doubleprec()
            elif cmd == 'updg':
                o.enable_universal_pdgcode(int(arg))
            elif cmd == 'uw':
                o.enable_universal_weight(float(arg))
            elif cmd == 'metadata':
                o.transfer_metadata(arg)
            elif cmd == 'transfer':
                with mcpl.MCPLFile(arg) as f:
                    for b in f.particle_blocks:
                        o.add_particles(b)
            elif cmd == 'particle':
                v = arg.split()
                f = [float(x) for x in v[:12]]
                o.add_particle( position = f[0:3], direction = f[3:6],
                                polarisation = f[6:9], ekin = f[9], time = f[10],
                                weight = f[11], pdgcode = int(v[12]),
                                userflags = int(v[13]) )
            elif cmd == 'close':
                o.close()
                return
            elif cmd == 'closegz':
                o.closeandgzip()
                return
            else:
                raise RuntimeError(f'Unknown script command: {cmd}')
        o.close()
    finally:
        if o._fh is not None:
            #Like in C, a file is left unclosed after an error:
            o._fh.close()
            o._fh = None

def particle(i, pdg = 2112, uf = 0, ekin = None, dirx = None):
    ux, uy, uz = ( 0.6, 0.0, 0.8 ) if dirx is None else ( dirx, 0.0, math.sqrt(max(0.0,1-dirx*dirx)) )
    e = 0.025 * ( i + 1 ) if ekin is None else ekin
    return (f'particle {1.5*i} {-2.0*i} {0.125*i} {ux!r} {uy!r} {uz!r} 0.1 0.2 {0.3*i} '
            f'{e!r} {0.01*i} {1.0+0.5*i} {pdg} {uf}')

def parts(n, **kw):
    return '\n'.join(particle(i, **kw) for i in range(n))

def script(*lines):
    return '\n'.join( line for line in lines if line )

def compare_script(title, s, outfile = 'out'):
    return compare(f'Script "{title}"', 'mcpltest_script', (outfile, s), py_script)

def test_writer_scripts():
    ok = True
    hdr = script('srcname MySim', 'comment first comment', 'blob key1 some data',
                 'statsum nsim -1', 'comment second comment')
    ok &= compare_script('empty file', 'close')
    ok &= compare_script('header only', script(hdr,'close'))
    ok &= compare_script('basic', script(hdr, parts(5), 'statsum nsim 1000', 'close'))
    for opts in ['userflags','pol','dp','updg 2112','uw 2.5','userflags\npol\ndp',
                 'dp\nupdg -11\nuw 0.125','pol\nuserflags\nupdg 22\nuw 1e-3']:
        ok &= compare_script(f'options {opts!r}',
                             script(hdr, opts, parts(4, uf=7), 'close'))
    ok &= compare_script('options set twice', script('pol','pol','dp','dp','userflags',
                                                     'userflags','updg 22','updg 22',
                                                     'uw 2','uw 2',parts(2),'close'))
    ok &= compare_script('gzipped', script(hdr, parts(10), 'closegz'))
    for opts in ('', 'pol', 'dp', 'userflags\npol'):
        for src in ('a1.mcpl', 'b_dp.mcpl', 'b_pol.mcpl', 'b_uf.mcpl', 'b_uw2.mcpl'):
            ok &= compare_script(f'transfer from {src} with options {opts!r}',
                                 script(opts, f'transfer {src}', 'close'))
    ok &= compare_script('metadata and transfer', script('metadata a1.mcpl',
                                                         'transfer a2.mcpl', 'close'))
    ok &= compare_script('transfer into universal pdgcode', script('updg 2112',
                                                                   'transfer a2.mcpl', 'close'))
    ok &= compare_script('transfer into universal weight', script('uw 2',
                                                                  'transfer b_uw.mcpl', 'close'))
    ok &= compare_script('transfer into same universal weight', script('uw 2.5',
                                                                       'transfer b_uw.mcpl', 'close'))
    ok &= compare_script('gzipped empty', 'closegz')
    ok &= compare_script('filename with .mcpl', script(parts(1),'close'), 'out.mcpl')
    ok &= compare_script('filename with .mcpl.gz', script(parts(1),'close'), 'out.mcpl.gz')
    ok &= compare_script('filename .mcpl', 'close', '.mcpl')
    ok &= compare_script('empty filename', 'close', '')
    ok &= compare_script('special directions', script(
        'dp', *[ particle(i,dirx=d) for i,d in enumerate([1.0,-1.0,0.0,-0.0,0.5,1e-12,-0.999999])],
        'close'))
    ok &= compare_script('zero and large ekin', script(
        particle(0,ekin=0.0), particle(1,ekin=-0.0), particle(2,ekin=1e30), 'close'))
    ok &= compare_script('extreme pdgcodes', script(
        particle(0,pdg=-2147483648), particle(1,pdg=2147483647), particle(2,pdg=0),
        'close'))
    ok &= compare_script('userflags values', script(
        'userflags', particle(0,uf=0), particle(1,uf=4294967295), 'close'))
    ok &= compare_script('stat:sum updates', script(
        'statsum a -1', 'statsum b 5', 'statsum a 3', 'scale 2', parts(3),
        'statsum a 1e10', 'statsum b -1', 'scale 0.5', 'close'))
    ok &= compare_script('stat:sum scale -1', script(
        'statsum a 1', 'statsum b 2', 'scale -1', 'close'))
    ok &= compare_script('stat:sum scale overflow', script(
        'statsum a 1e300', 'statsum b 2', 'scale 1e10', 'close'))
    ok &= compare_script('stat:sum scale overflow after header', script(
        'statsum a 1e300', parts(1), 'scale 1e10', 'close'))
    ok &= compare_script('stat:sum values', script(
        'statsum a 0', 'statsum b 1e-300', 'statsum c 1.7976931348623157e308',
        'statsum d 0.1', 'statsum e 123456789012345678', 'close'))
    ok &= compare_script('stat:sum comment', script(
        'comment stat:sum:abc:                       1', 'close'))
    ok &= compare_script('stat:sum key of 64 chars', script(
        'statsum ' + 'k'*64 + ' 1', 'close'))
    #Errors:
    errors = [ ('comment after particle', script(parts(1),'comment x')),
               ('srcname after particle', script(parts(1),'srcname x')),
               ('blob after particle', script(parts(1),'blob k v')),
               ('userflags after particle', script(parts(1),'userflags')),
               ('pol after particle', script(parts(1),'pol')),
               ('dp after particle', script(parts(1),'dp')),
               ('updg after particle', script(parts(1),'updg 22')),
               ('uw after particle', script(parts(1),'uw 2')),
               ('new stat:sum after particle', script(parts(1),'statsum k 1')),
               ('zero universal pdgcode', 'updg 0'),
               ('different universal pdgcodes', script('updg 22','updg 2112')),
               ('negative universal weight', 'uw -1'),
               ('zero universal weight', 'uw 0'),
               ('infinite universal weight', 'uw inf'),
               ('nan universal weight', 'uw nan'),
               ('different universal weights', script('uw 1','uw 2')),
               ('duplicate blob key', script('blob k a','blob k b')),
               ('reserved stat: comment', 'comment stat:foo'),
               ('bad stat:sum: comment', 'comment stat:sum:bad'),
               ('bad stat:sum: comment value', 'comment stat:sum:abc:x'),
               ('stat:sum bad key', 'statsum 1abc 1'),
               ('stat:sum key with space', 'statsum a b 1'),
               ('stat:sum key too long', 'statsum ' + 'k'*65 + ' 1'),
               ('stat:sum negative', 'statsum k -2'),
               ('stat:sum nan', 'statsum k nan'),
               ('stat:sum inf', 'statsum k inf'),
               ('stat:sum -inf', 'statsum k -inf'),
               ('scale zero', 'scale 0'),
               ('scale negative', 'scale -2'),
               ('scale nan', 'scale nan'),
               ('scale inf', 'scale inf'),
               ('non-unit direction', 'particle 0 0 0 1 1 0 0 0 0 1 0 1 2112 0'),
               ('zero direction', 'particle 0 0 0 0 0 0 0 0 0 1 0 1 2112 0'),
               ('negative ekin', 'particle 0 0 0 0 0 1 0 0 0 -1 0 1 2112 0'),
               ('nan direction', 'particle 0 0 0 nan 0 1 0 0 0 1 0 1 2112 0') ]
    for title, s in errors:
        ok &= compare_script(title, s)
    return ok

################################################################################
# Input files:

def make_inputs():
    """Create input files with the C library"""
    if input_dir.exists():
        shutil.rmtree(input_dir)
    input_dir.mkdir()
    lib = getlib('pywriter')
    def w(name, s):
        lib.mcpltest_script(str(input_dir/name), s)
    hdr = script('srcname MySim', 'comment a comment', 'blob key1 some data')
    w('a1', script(hdr, 'statsum nsim 1000', 'statsum other -1', parts(5), 'close'))
    w('a2', script(hdr, 'statsum nsim 2000.5', 'statsum other -1', parts(3, pdg=22), 'close'))
    w('a3', script(hdr, 'statsum nsim -1', 'statsum other -1', parts(2), 'close'))
    w('a4', script(hdr, 'statsum nsim 1e308', 'statsum other -1', parts(1), 'close'))
    w('a5', script(hdr, 'statsum nsim 1e308', 'statsum other -1', parts(1), 'close'))
    w('a_empty', script(hdr, 'statsum nsim 7', 'statsum other -1', 'close'))
    w('agz', script(hdr, 'statsum nsim 1', 'statsum other -1', parts(4), 'closegz'))
    w('b_dp', script(hdr, 'dp', 'statsum nsim 1', parts(3), 'close'))
    w('b_pol', script('srcname Other', 'pol', parts(3), 'close'))
    w('b_uf', script('srcname Other', 'userflags', parts(3, uf=99), 'close'))
    w('b_updg', script('srcname Other', 'updg 2112', parts(3), 'close'))
    w('b_updg2', script('srcname Other', 'updg 2112', parts(2), 'close'))
    w('b_updg_g', script('srcname Other', 'updg 22', parts(2, pdg=22), 'close'))
    w('b_uw', script('srcname Other', 'uw 2.5', parts(3), 'close'))
    w('b_uw2', script('srcname Other', 'uw 2.5', 'dp', parts(3), 'close'))
    w('b_empty_pol', script('srcname Other', 'pol', 'dp', 'close'))
    w('c_comment', script(hdr, 'comment extra', 'statsum nsim 1', 'statsum other -1', parts(2), 'close'))
    w('c_blob', script('srcname MySim', 'comment a comment', 'blob key1 other data',
                       'statsum nsim 1', 'statsum other -1', parts(2), 'close'))
    w('c_statkey', script(hdr, 'statsum nsim 1', 'statsum otherkey -1', parts(2), 'close'))
    for f in ('reffile_1.mcpl', 'reffile_crash.mcpl', 'reffile_empty.mcpl',
              'reffile_skip123.mcpl', 'reffile_truncated.mcpl', 'reffile_5.mcpl.gz',
              'ref_statsum_crash.mcpl', 'ref_statsum.mcpl.gz'):
        shutil.copy(test_data_dir.joinpath('ref',f), input_dir / f)
    for f in ('reffile_1.mcpl', 'reffile_5.mcpl'):
        shutil.copy(test_data_dir.joinpath('reffmt2',f), input_dir / ('fmt2_'+f))

def test_random_scripts(n):
    #Random sequences of writer calls (valid or not):
    import random
    rng = random.Random(123)
    pool = [ lambda : 'srcname ' + rng.choice(['A','B','long name with spaces']),
             lambda : 'comment ' + rng.choice(['c1','c2','stat:x','stat:sum:k:'+' '*23+'1']),
             lambda : 'blob ' + rng.choice(['k1','k2']) + ' ' + rng.choice(['data','']),
             lambda : 'statsum ' + rng.choice(['a','b','1x']) + ' ' + rng.choice(['-1','0','5','1e300','-3']),
             lambda : 'scale ' + rng.choice(['2','0.5','-1','1e10','0']),
             lambda : 'userflags', lambda : 'pol', lambda : 'dp',
             lambda : 'updg ' + rng.choice(['2112','22','0']),
             lambda : 'uw ' + rng.choice(['1','2.5','-1']),
             lambda : particle(rng.randrange(5), pdg=rng.choice([2112,22,-11]),
                               uf=rng.randrange(1000), dirx=rng.choice([None,0.0,1.0,0.3])),
             lambda : particle(0, ekin=rng.choice([0.0,1.0,-1.0])) ]
    ok = True
    for i in range(n):
        lines = [ rng.choice(pool)() for _ in range(rng.randrange(1,12)) ]
        lines.append(rng.choice(['close','closegz']))
        title = f'random script {i}'
        ok &= compare(f'Script "{title}"', 'mcpltest_script', ('out', script(*lines)), py_script)
    return ok

def main():
    make_inputs()
    results = [ test_writer_scripts(), test_random_scripts(150) ]
    print(f'Compared {ncases} operations')
    assert all(results), 'C and Python APIs give different results'

if __name__ == '__main__':
    main()
