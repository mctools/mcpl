
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

# Test that MCPLFile closes the files it opens, also those of gzipped files
# (closing a GzipFile does not close the file it reads, and open files can not
# be removed on Windows).

import gc
import gzip
import pathlib
import warnings

from mcpldev import MCPLFile
from MCPLTestUtils.dirs import test_data_dir

pathlib.Path('example.mcpl.gz').write_bytes(gzip.compress(test_data_dir.joinpath('example.mcpl').read_bytes()))

def unclosed( fct ):
    """The files left open by fct (with their ResourceWarnings)"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        fct()
        gc.collect()
    return [ str(x.message) for x in w if issubclass(x.category,ResourceWarning) ]

def with_statement():
    with MCPLFile('example.mcpl.gz') as f:
        f.read_block()

def all_particles():
    with MCPLFile('example.mcpl.gz') as f:
        sum( 1 for p in f.particles )

for name, fct in ( ('one block',with_statement), ('all particles',all_particles) ):
    print(f'{name}: unclosed files: {unclosed(fct)}')
pathlib.Path('example.mcpl.gz').unlink()
print('removed the file afterwards')
