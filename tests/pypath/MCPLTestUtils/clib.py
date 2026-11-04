
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

"""The file operations of the C library, as mcpltool-c gave them on the
command line, with the test library fileops (see tests/modules/lib_fileops)"""

import pathlib

from .loadlib import getlib
from .stdout_redirect import RedirectStdout


def lib():
    return getlib('fileops')

def dump( file_path, parts = 0, skip = 0, limit = 0 ):
    """The dump of the file by the C library (as by mcpl_dump: its warnings,
    the line with the file name, unless it can not be opened, the header and
    the particles, and the error, if any), as bytes (with \n line endings)"""
    #(the warnings are given to the print handler):
    with RedirectStdout('dump_clib_messages.txt'):
        res = lib().mcpltest_dump(str(file_path),parts,skip,limit,'dump_clib.txt')
    opened = not res.endswith(' (when opening)')
    res = res.removesuffix(' (when opening)')
    error = '' if res == 'ok' else f'MCPL ERROR: {res.split(": ",1)[1]}\n'
    return ( pathlib.Path('dump_clib_messages.txt').read_bytes()
             + ( f'Opened MCPL file {pathlib.Path(file_path).name}:\n'.encode() if opened else b'' )
             + ( pathlib.Path('dump_clib.txt').read_bytes() if opened else b'' )
             + error.encode() ).replace(b'\r\n',b'\n')

def merge( output, *files ):
    """Merge the files into the new file output: "ok", or the error"""
    return lib().mcpltest_merge(str(output),'\n'.join(str(f) for f in files),0,0)
