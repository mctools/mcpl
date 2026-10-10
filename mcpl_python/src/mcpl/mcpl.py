
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

"""The mcpl.mcpl module of earlier releases, kept for backwards compatibility.

All the names are also available directly in the mcpl package (after "import
mcpl"), which is the recommended way to use them.
"""

__all__ = [
    'MCPLError',
    'MCPLFile',
    'MCPLParticle',
    'MCPLParticleBlock',
    'app_pymcpltool',
    'collect_stats',
    'convert2ascii',
    'dump_file',
    'dump_stats',
    'encode_stat_sum',
    'is_valid_stat_sum_key',
    'main',
    'plot_stats',
]

from ._blocks import MCPLParticle, MCPLParticleBlock
from ._cli import app_pymcpltool, main
from ._common import MCPLError, __version__  # noqa: F401
from ._fileops import convert2ascii, dump_file
from ._reader import MCPLFile
from ._stats import collect_stats, dump_stats, plot_stats
from ._statsum import encode_stat_sum, is_valid_stat_sum_key

if __name__ == '__main__':
    main()
