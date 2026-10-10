
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

# Test that the plotly plotting backend can save plots of statistics and
# histograms (as HTML files).

import pathlib

import mcpldev as mcpl
from MCPLTestUtils.dirs import test_data_dir

example_file = test_data_dir.parent.parent.joinpath('examples','example.mcpl')

files = mcpl.plot_stats(mcpl.collect_stats(example_file), backend='plotly',
                        filename='stats.html')
files += mcpl.histogram(example_file, 'ekin/MeV', logx=True,
                        split='pdgcode').plot(backend='plotly', filename='ekin.html',
                                              logy=True)
files += mcpl.histogram2d(example_file, 'x/cm', 'y/cm').plot(backend='plotly',
                                                             filename='xy.html')
for f in files:
    text = pathlib.Path(f).read_text(encoding='utf-8')
    assert 'plotly' in text.lower() and len(text) > 10000
    print(f'created {f}')
try:
    mcpl.histogram(example_file, 'x/cm').plot(backend='plotly', filename='x.foo')
except mcpl.MCPLError as e:
    print(e if 'html' in str(e) else 'unexpected error message')
