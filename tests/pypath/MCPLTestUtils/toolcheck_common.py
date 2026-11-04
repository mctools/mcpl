
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

import gzip
import hashlib
import os
import shlex
import subprocess
import sys
from pathlib import Path

from .common import flush
from .dirs import mcpltool_cmd, test_data_dir


def gunzip( f ):
    f = Path(f)
    assert f.name.endswith('.gz')
    ftgt = f.absolute().parent.joinpath(f.name[:-3])
    assert f.is_file()
    assert not ftgt.is_file()
    content = gzip.decompress(f.read_bytes())
    f.unlink()
    ftgt.write_bytes(content)

#The tool run by cmd: mcpltool-c, or with use_python_tool the mcpltool of
#Python (which will replace mcpltool-c, when it is retired):
_python_tool = False

def use_python_tool():
    global _python_tool
    _python_tool = True

def python_tool():
    """Whether cmd runs the mcpltool of Python"""
    return _python_tool

def _py_arg( a ):
    """The arguments of mcpltool for the argument a of mcpltool-c (see py_args)"""
    if a.startswith('-') and not a.startswith('--'):
        #(the short options before p, unless one takes a value, which then is
        #the rest, like the key of -bKEY):
        for i, c in enumerate(a[1:],1):
            if c in 'lsb':
                break
            if c == 'p':
                if a[i+1:]:
                    return [ a[:i] ] * ( i > 1 ) + [ '-p', f'pdgcode == {a[i+1:]}' ]
                break
    return [ a ]

def py_args( args ):
    """Arguments for mcpltool corresponding to those of mcpltool-c: -pPDGCODE
    is -p "pdgcode == PDGCODE" for mcpltool (also after other short options,
    as in -ep2112)"""
    return [ b for a in args for b in _py_arg(str(a)) ]

def tool_command( args ):
    """The command running the tool with the arguments (those of mcpltool-c),
    with a fixed version in its printouts, and its name"""
    if _python_tool:
        return [ sys.executable, '-m', 'mcpldev', *py_args(args) ], 'mcpltool'
    return [ mcpltool_cmd, *( str(a) for a in args ), '--fakeversion' ], 'mcpltool-c'

def cmd(*args, print_md5sum_of_output = False, fail = False, pyfail = None):
    """Run the tool with the arguments, printing its output, and check that it
    fails if fail is set (or pyfail, if given, for the mcpltool of Python,
    where it differs)"""
    if _python_tool and pyfail is not None:
        fail = pyfail
    flush()
    print("----------------------------------------------")
    def argfmt( a ):
        a = str(a)
        if str(test_data_dir) in a:
            a = a.replace(str(test_data_dir),'<TESTDATADIR>')
        if '\\' in a and '/' not in a:
            a = a.replace('\\','/')
        return a
    args_print = shlex.join( argfmt(a) for a in args )
    fullcmd, name = tool_command(args)
    print(f"Running {name} {args_print}")
    print("----------------------------------------------")
    flush()
    rv = subprocess.run( fullcmd, capture_output = True, check = False,
                         env = { **os.environ, 'PYMCPLTOOL_FAKE_PYVERSION' : '1' } )
    flush()
    assert not rv.stderr, "process had stderr"
    flush()
    if print_md5sum_of_output:
        print('>>>{}<<<'.format(rv.stdout
              .replace(b'\r',b'<CR>')
              .replace(b'\n',b'<LF>')
              .decode('ascii','backslashreplace')))
        print( hashlib.md5(rv.stdout).hexdigest() )
    else:
        sys.stdout.buffer.write(rv.stdout)
    print()
    flush()
    if rv.returncode != 0:
        print("===> Command failed!")
    if bool(fail) != (rv.returncode != 0):
        raise SystemExit('Command did not end as expected!')

def check_same( f1, f2 ):
    f1 = Path(f1)
    f2 = Path(f2)
    if not f1.exists() and not f2.exists():
        #no files, no check
        return
    print(f"===> Checking that {f1.name} and {f2.name} have identical contents.")
    c1 = f1.read_bytes()
    c2 = f2.read_bytes()
    if f1.name.endswith('.gz'):
        c1 = gzip.decompress( c1 )
    if f2.name.endswith('.gz'):
        c2 = gzip.decompress( c2 )
    if c1 != c2:
        print("===> Check failed!")
        raise SystemExit(1)

def copy( src, tgt ):
    psrc = Path(src)
    if isinstance(tgt,str) and tgt == '.':
        ptgt = Path('.').joinpath(psrc.name)
    else:
        ptgt = Path(tgt)
    assert psrc.is_file()
    assert not ptgt.exists()
    ptgt.write_bytes(psrc.read_bytes())
    return ptgt
