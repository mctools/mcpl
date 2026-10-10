
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

"""MCPLError, the version, and small helpers used by the other modules."""

__all__ = ['MCPLError']

__version__ = '2.2.9'

import os
import sys


def _checkpyversion():
    pyversion = sys.version_info[0:3]
    _minpyv=(3,8,0)
    if pyversion < _minpyv:
        a = '.'.join(str(i) for i in pyversion)
        b = '.'.join(str(i) for i in _minpyv)
        raise ImportError('MCPL Error: Unsupported python version'
                          f' {a} detected (needs {b} or later).')
_checkpyversion()


#For raw output of byte-array contents to stdout, without any troubles depending
#on encoding or python versions:
def _output_bytearray_raw(b):
    sys.stdout.flush()
    getattr(sys.stdout,'buffer',sys.stdout).write(b)
    sys.stdout.flush()


class MCPLError(Exception):
    """Common exception class for all exceptions raised by module"""

def _determine_version():
    if os.environ.get('PYMCPLTOOL_FAKE_PYVERSION','').strip():
        return '99.99.99'
    else:
        return __version__
