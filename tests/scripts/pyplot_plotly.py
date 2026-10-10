
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


# NEEDS: numpy plotly

# Test that the plotly plotting backend can save plots (as HTML files).

import pathlib

import mcpldev as mcpl
from mcpldev._stats import _stats_figures
from MCPLTestUtils.dirs import test_data_dir

example_file = test_data_dir.parent.parent.joinpath('examples','example.mcpl')

files = mcpl.plotting.save(_stats_figures(example_file), 'stats.html', backend='plotly')
for f in files:
    text = pathlib.Path(f).read_text()
    assert 'plotly' in text.lower() and len(text) > 10000
    print(f'created {f}')
try:
    mcpl.plotting.save(_stats_figures(example_file), 'stats.foo', backend='plotly')
except mcpl.MCPLError as e:
    print(e if 'html' in str(e) else 'unexpected error message')
