
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

# Check that pymcpltool gives the same results and printouts as mcpltool for
# the operations they share.

import gzip
import pathlib
import shutil
import subprocess
import sys

from MCPLTestUtils.dirs import mcpltool_cmd, test_data_dir
from MCPLTestUtils.loadlib import getlib

input_dir = pathlib.Path('inputs').absolute()

def make_inputs():
    input_dir.mkdir()
    lib = getlib('pywriter')
    def w(name, *lines):
        lib.mcpltest_script(str(input_dir/name), '\n'.join(lines))
    def parts(n, pdgs=(2112,22,11), dp=False):
        res = []
        for i in range(n):
            ux = 0.6 if i%2 else -0.8
            uz = (1.0-ux*ux)**0.5
            res.append(f'particle {1.5*i} {-2.0*i} {0.1*i} {ux} 0 {uz} 0 0 0'
                       f' {0.001*(i+1)} {0.01*i} {1.0+0.5*i} {pdgs[i%len(pdgs)]} {i}')
        return res
    hdr = ('srcname MySim', 'comment a comment', 'blob key1 some data')
    w('a1', *hdr, 'statsum nsim 1000', *parts(30), 'close')
    w('a2', *hdr, 'statsum nsim 2000', *parts(20), 'close')
    w('a3', *hdr, 'statsum nsim -1', *parts(5), 'closegz')
    w('b_dp', 'srcname Other', 'dp', 'userflags', *parts(12), 'close')
    w('b_pol', 'srcname Other', 'pol', *parts(7), 'close')
    w('c_nostat', 'srcname MySim', *parts(9), 'close')
    shutil.copy(test_data_dir.joinpath('ref','reffile_crash.mcpl'), input_dir/'crash.mcpl')
    shutil.copy(test_data_dir.joinpath('ref','reffile_1.mcpl'), input_dir/'ref1.mcpl')

def dir_contents(d):
    res = {}
    for f in sorted(pathlib.Path(d).iterdir()):
        data = f.read_bytes()
        if f.name.endswith('.gz') and data[:2] == b'\x1f\x8b':
            data = gzip.decompress(data)
        res[f.name] = data
    return res

def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, check=False)
    return r.returncode, r.stdout.decode().replace('\r\n','\n'), r.stderr.decode()

def fresh(d):
    if pathlib.Path(d).exists():
        shutil.rmtree(d)
    shutil.copytree(input_dir, d)

ncases = 0
def compare(*args):
    global ncases
    ncases += 1
    fresh('c')
    fresh('py')
    c = run([str(mcpltool_cmd), *args], 'c')
    #the Python API has no mcpl_ prefix on function names:
    c = ( c[0], c[1].replace('mcpl_',''), c[2] )
    p = run([sys.executable, '-m', 'mcpldev', *args], 'py')
    problems = []
    if c[0] != p[0]:
        problems.append(f'exit codes differ: C: {c[0]} Py: {p[0]}')
    if c[1] != p[1]:
        problems.append(f'printouts differ:\n      C: {c[1]!r}\n     Py: {p[1]!r}')
    if p[2]:
        problems.append(f'pymcpltool stderr: {p[2]!r}')
    dc, dp = dir_contents('c'), dir_contents('py')
    if set(dc) != set(dp):
        problems.append(f'different files: C: {sorted(dc)} Py: {sorted(dp)}')
    else:
        problems += [ f'file {k} differs' for k in dc if dc[k] != dp[k] ]
    print(f'mcpltool {" ".join(args)}: exit code {c[0]}')
    for line in c[1].splitlines():
        print(f'   | {line}')
    for problem in problems:
        print(f'   PROBLEM: {problem}')
    return not problems

def test_compare_with_mcpltool():
    ok = True
    cases = [
        ['--merge','out.mcpl','a1.mcpl','a2.mcpl'],
        ['-m','out.mcpl.gz','a1.mcpl','a2.mcpl','a3.mcpl.gz'],
        ['--merge','out','a1.mcpl'],
        ['--merge','--inplace','a1.mcpl','a2.mcpl','a3.mcpl.gz'],
        ['-m','--inplace','a3.mcpl.gz','a1.mcpl'],
        ['--merge','out.mcpl','a1.mcpl','b_dp.mcpl'],
        ['--merge','out.mcpl','a1.mcpl'],
        ['--merge','a2.mcpl','a1.mcpl','a1.mcpl'],
        ['--merge','out.gz','a1.mcpl','a2.mcpl'],
        ['--merge','out.mcpl','a1.mcpl','a1.mcpl'],
        ['--forcemerge','out.mcpl','a1.mcpl','b_dp.mcpl','b_pol.mcpl'],
        ['--forcemerge','--keepuserflags','out.mcpl.gz','b_dp.mcpl','b_pol.mcpl'],
        ['--forcemerge','out.mcpl','a1.mcpl','a2.mcpl'],
        ['--forcemerge','out.mcpl'],
        ['--extract','a1.mcpl','out.mcpl'],
        ['-e','a1.mcpl','out.mcpl.gz'],
        ['--extract','-l5','a1.mcpl','out.mcpl'],
        ['--extract','-s25','a1.mcpl','out'],
        ['--extract','-l3','-s4','a3.mcpl.gz','out.mcpl'],
        ['--extract','-l100','-s0','a1.mcpl','out.mcpl'],
        ['--extract','-p22','a1.mcpl','out.mcpl'],
        ['-e','-p-11','b_dp.mcpl','out.mcpl'],
        ['-e','-p11','-l10','-s3','a1.mcpl','out.mcpl'],
        ['--extract','-p2112','c_nostat.mcpl','out.mcpl'],
        ['--extract','-s5','c_nostat.mcpl','out.mcpl'],
        ['--extract','crash.mcpl','out.mcpl'],
        ['--extract','ref1.mcpl','out.mcpl'],
        ['--extract','a1.mcpl','a2.mcpl'],
        ['--extract','a1.mcpl','out.gz'],
        ['--extract','a1.mcpl'],
        ['--extract','a1.mcpl','x.mcpl','y.mcpl'],
        ['--extract','-p0','a1.mcpl','out.mcpl'],
        ['--extract','-pabc','a1.mcpl','out.mcpl'],
        ['--extract','--no-comment','-p22','-l5','a1.mcpl','out.mcpl'],
        ['--extract','-p11','-l3','-s4','a1.mcpl','out.mcpl'],
        ['--no-comment','a1.mcpl'],
        ['--extract','-pgamma','a1.mcpl','out.mcpl'],
        ['--extract','-pphoton','-l10','a1.mcpl','out.mcpl'],
        ['--extract','-pantielectron','b_dp.mcpl','out.mcpl'],
        ['--extract','-pneutron','c_nostat.mcpl','out.mcpl'],
        ['--extract','-pNeutron','a1.mcpl','out.mcpl'],
        ['--extract','-pfoo','a1.mcpl','out.mcpl'],
        ['--inplace','a1.mcpl','a2.mcpl'],
        ['--keepuserflags','a1.mcpl'],
        ['--merge','--forcemerge','out.mcpl','a1.mcpl','a2.mcpl'],
        ['--merge','--extract','a1.mcpl','out.mcpl'],
        ['-j','--extract','a1.mcpl','out.mcpl'],
        ['--repair','crash.mcpl'],
        ['--repair','a1.mcpl'],
        ['--repair','a3.mcpl.gz'],
        ['-r','a1.mcpl','a2.mcpl'],
        ['-l3','a1.mcpl'],
        ['-j','b_dp.mcpl'],
    ]
    for args in cases:
        ok &= compare(*args)
    return ok

def main():
    make_inputs()
    results = [ test_compare_with_mcpltool() ]
    print(f'Compared {ncases} command lines with mcpltool')
    assert all(results), 'Problems found'

if __name__ == '__main__':
    main()
