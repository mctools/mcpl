
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

"""Python module for accessing MCPL files.

The MCPL (Monte Carlo Particle Lists) format is thoroughly documented on the
project homepage, from where it is also possible to download the entire MCPL
distribution:

     https://mctools.github.io/mcpl/

Specifically, more documentation about how to use the present python module to
access MCPL files can be found at:

     https://mctools.github.io/mcpl/usage_python/

This file can freely used as per the terms in the LICENSE file distributed with
MCPL, also available at https://github.com/mctools/mcpl/blob/master/LICENSE .

A substantial effort went into developing MCPL. If you use it for your work, we
would appreciate it if you would use the following reference in your work:

   T. Kittelmann, et al., Monte Carlo Particle Lists: MCPL, Computer Physics
   Communications 218, 17-42 (2017), https://doi.org/10.1016/j.cpc.2017.04.012

mcpl.py written by Thomas Kittelmann, 2017-2022. The work was supported by the
European Union's Horizon 2020 research and innovation programme under grant
agreement No 676548 (the BrightnESS project)
"""

__all__ = [
            'MCPLError',
            'MCPLFile',
            'MCPLOutFile',
            'MCPLParticle',
            'MCPLParticleBlock',
            'ParticleEdit',
            'ParticleFilter',
            'ParticleValue',
            'app_pymcpltool',
            'can_merge',
            'collect_stats',
            'constants',
            'convert2ascii',
            'create_outfile_mpi',
            'dump_file',
            'dump_stats',
            'encode_stat_sum',
            'forcemerge_files',
            'gzip_file',
            'is_valid_stat_sum_key',
            'merge_files',
            'merge_inplace',
            'merge_outfiles_mpi',
            'name_helper',
            'plot_stats',
            'repair',
            'use_logging',
           ]

__version__ = '2.2.9'

from . import constants
from ._blocks import MCPLParticle, MCPLParticleBlock
from ._cli import app_pymcpltool
from ._common import MCPLError
from ._expressions import ParticleEdit, ParticleFilter, ParticleValue
from ._fileops import (
    can_merge,
    convert2ascii,
    create_outfile_mpi,
    dump_file,
    forcemerge_files,
    merge_files,
    merge_inplace,
    merge_outfiles_mpi,
    name_helper,
    repair,
)
from ._messages import use_logging
from ._reader import MCPLFile
from ._stats import collect_stats, dump_stats, plot_stats
from ._statsum import encode_stat_sum, is_valid_stat_sum_key
from ._writer import MCPLOutFile, gzip_file
