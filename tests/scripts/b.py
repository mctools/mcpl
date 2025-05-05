
################################################################################
##                                                                            ##
##  This file is part of MCPL (see https://mctools.github.io/mcpl/)           ##
##                                                                            ##
##  Copyright 2015-2025 MCPL developers.                                      ##
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

import sys
import pathlib
from mcpldev import MCPLError
from mcpldev import dump_file as pymcpltool_dump_file
from MCPLTestUtils.dirs import test_data_dir, mcpltool_cmd
from MCPLTestUtils.checkasciicompat import check_compat
import subprocess
from MCPLTestUtils.stdout_redirect import RedirectStdout
from MCPLTestUtils.common import flush

def run_pymcpltool(*args):
    from mcpldev.mcpl import app_pymcpltool
    try:
        app_pymcpltool(['pymcpltool']+[str(e) for e in args])
    except SystemExit as e:
        if str(e) != '0':
            raise

def run_mcpltool(*args, check = False):
    flush()
    rv = subprocess.run( [mcpltool_cmd]+[str(e) for e in args],
                         capture_output = True, check = check )
    flush()
    assert not rv.stderr
    if check:
        return rv.stdout
    else:
        return rv.returncode, rv.stdout


files = {}
for subdir in ('ref','reffmt2'):
    for pat in ('*.mcpl','*.mcpl.gz'):
        for f in sorted(test_data_dir.joinpath(subdir).glob(pat)):
            key = '%s/%s'%(subdir,f.name)
            files[key] = f

errors = False
for file_key in sorted(files.keys()):
    file_path = files[file_key]
    print("Testing %s"%file_key)
    expect_crash = False
    truncated_file = 'reffile_truncated' in file_key
    if ('crash' in file_key and file_key.endswith('.gz')) or 'reffile_bad' in file_key or truncated_file:
        expect_crash = True
        print(" -- assuming this is a broken file which can't be read without errors")

        #First compare mcpltool-like output:
    with RedirectStdout('dump_pymcpltool.txt'):
        try:
            if truncated_file:
                pymcpltool_dump_file(file_path,limit=0,blocklength=1)#need bl=1 to get same output as C-mcpltool
            else:
                pymcpltool_dump_file(file_path,limit=0)
            ec=0
        except MCPLError as mpe:
            print('MCPL ERROR: %s'%str(mpe))
            ec=1
    if (ec!=0) !=  expect_crash:
        errors = True
        print("ERRORS DETECTED in python dump (unexpected exception status)")
        continue

    ec,mcpltool_output = run_mcpltool('-l0',file_path)
    with open('dump_mcpltool.txt','wb') as f:
        f.write(mcpltool_output)
    if (ec!=0) !=  expect_crash:
        errors = True
        print("ERRORS DETECTED in mcpltool (unexpected error status)")
        continue

    if pathlib.Path('dump_pymcpltool.txt').read_bytes() != mcpltool_output:
        errors = True
        print("ERRORS DETECTED in mcpltool-like output")

    #Now compare numbers based on high-res ascii output:
    if expect_crash:
        continue

    def rm_f(f):
        p = pathlib.Path(f)
        if p.exists():
            p.unlink()
    rm_f('dump_ascii_c.txt')
    rm_f('dump_ascii_py.txt')
    flush()
    out_c = run_mcpltool('--text',file_path,'dump_ascii_c.txt',check=True)
    flush()
    sys.stdout.buffer.write(out_c)
    flush()
    rm_f('out_pymcpltool.txt')
    with RedirectStdout('out_pymcpltool.txt'):
        run_pymcpltool('--text',file_path,'dump_ascii_py.txt')
    out_py = pathlib.Path('out_pymcpltool.txt').read_bytes()
    if out_c!=out_py:
        errors = True
        print("ERRORS DETECTED in stdout during creation of ascii output")
    incompat_errmsg = check_compat('./dump_ascii_c.txt','./dump_ascii_py.txt')
    if incompat_errmsg is not None:
        raise SystemExit('ERRORS DETECTED in high-res ascii output.'
                        f' C and Py tool output differs: {incompat_errmsg}')

assert not errors
