
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

import pathlib

import mcpldev
from mcpldev import MCPLError
from mcpldev import dump_file as pymcpltool_dump_file
from MCPLTestUtils.checkasciicompat import load_file
from MCPLTestUtils.clib import dump as c_library_dump
from MCPLTestUtils.common import flush
from MCPLTestUtils.dirs import test_data_dir
from MCPLTestUtils.stdout_redirect import RedirectStdout


def run_pymcpltool(*args):
    from mcpldev import app_mcpltool
    try:
        app_mcpltool(['mcpltool']+[str(e) for e in args])
    except SystemExit as e:
        if str(e) != '0':
            raise

def check_text( text_file, file_path ):
    """None if the numbers in the file of mcpltool --text are those of the
    particles (as read by Python), otherwise an error message"""
    import numpy
    cols = load_file(text_file)
    #(its warnings were already shown by the dump):
    hidden = RedirectStdout('check_text_messages.txt')
    with hidden, mcpldev.MCPLFile(file_path,blocklength=10**6) as f:
        blocks = list(f.particle_blocks)
    if cols is None:
        return None if not blocks else 'no particles in the text file'
    #(the columns after the index):
    names = ( 'pdgcode', 'ekin', 'x', 'y', 'z', 'ux', 'uy', 'uz', 'time',
              'weight', 'polx', 'poly', 'polz', 'userflags' )
    for colname, name in zip(cols.dtype.names[1:], names):
        expected = numpy.concatenate([ getattr(b,name) for b in blocks ])
        if not numpy.allclose( numpy.atleast_1d(cols[colname]).astype(float),
                               numpy.asarray(expected,dtype=float),
                               rtol = 1e-14, atol = 0.0, equal_nan = True ):
            return f'different {name}'
    return None


files = {}
for subdir in ('ref','reffmt2','reffmt4'):
    for pat in ('*.mcpl','*.mcpl.gz'):
        for f in sorted(test_data_dir.joinpath(subdir).glob(pat)):
            key = f'{subdir}/{f.name}'
            files[key] = f

errors = False
for file_key in sorted(files.keys()):
    file_path = files[file_key]
    print(f"Testing {file_key}")
    expect_crash = False
    truncated_file = 'reffile_truncated' in file_key
    if ('crash' in file_key and file_key.endswith('.gz')) or 'reffile_bad' in file_key or truncated_file:
        expect_crash = True
        print(" -- assuming this is a broken file which can't be read without errors")

        #First compare the dumps:
    with RedirectStdout('dump_pymcpltool.txt'):
        try:
            if truncated_file:
                pymcpltool_dump_file(file_path,limit=0,blocklength=1)#need bl=1 to get the same output as the C library
            else:
                pymcpltool_dump_file(file_path,limit=0)
            ec=0
        except MCPLError as mpe:
            print(f'MCPL ERROR: {mpe!s}')
            ec=1
    if (ec!=0) != expect_crash:
        errors = True
        print("ERRORS DETECTED in python dump (unexpected exception status)")
        continue

    #The same as the dump by the C library (with \n line endings, also on
    #Windows):
    clib_output = c_library_dump(file_path)
    pydump = pathlib.Path('dump_pymcpltool.txt').read_bytes().replace(b'\r\n',b'\n')
    if pydump != clib_output:
        errors = True
        print("ERRORS DETECTED in the output compared with the C library")

    #The small files of format 4 are also read in blocks of 3 particles (so
    #across several blocks), which must give the same output:
    if file_key.startswith('reffmt4/') and not expect_crash:
        with RedirectStdout('dump_pymcpltool_bl3.txt'):
            pymcpltool_dump_file(file_path,limit=0,blocklength=3)
        pydump_bl3 = pathlib.Path('dump_pymcpltool_bl3.txt').read_bytes()
        if pydump_bl3.replace(b'\r\n',b'\n') != clib_output:
            errors = True
            print("ERRORS DETECTED in mcpltool-like output with blocklength=3")

    #Now compare numbers based on high-res ascii output:
    if expect_crash:
        continue

    def rm_f(f):
        p = pathlib.Path(f)
        if p.exists():
            p.unlink()
    rm_f('dump_ascii_py.txt')
    flush()
    run_pymcpltool('--text',file_path,'dump_ascii_py.txt')
    flush()
    incompat_errmsg = check_text('./dump_ascii_py.txt',file_path)
    if incompat_errmsg is not None:
        raise SystemExit('ERRORS DETECTED in high-res ascii output:'
                         f' {incompat_errmsg}')

assert not errors
