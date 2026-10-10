
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


# NEEDS: numpy matplotlib

# Test that plot_stats and the matplotlib plotting backend can create files.

import pathlib

import mcpldev as mcpl
from MCPLTestUtils.dirs import test_data_dir

example_file = test_data_dir.parent.parent.joinpath('examples','example.mcpl')

def test_plot_stats():
    import matplotlib
    matplotlib.use('agg')
    files = sorted( f for f in test_data_dir.joinpath('ref').glob('*.mcpl*')
                    if not any(e in f.name for e in ('bad','crash','truncated',
                                                      'statunsupported')) )
    files.append(example_file)
    for i, f in enumerate(files):
        with mcpl.MCPLFile(f) as mf:
            if not mf.nparticles:
                continue
        pdf = f'plots_{i}.pdf'
        mcpl.plot_stats(mcpl.collect_stats(f), pdf=pdf)
        assert pathlib.Path(pdf).stat().st_size > 1000
        print(f'plot_stats ok for {f.name}')

def test_png():
    from mcpldev._stats import _stats_figures
    figs = _stats_figures(example_file)[:3]
    files = mcpl.plotting.save(figs, 'stats.png', backend='matplotlib', mpl_backend='agg')
    for f in files:
        assert pathlib.Path(f).read_bytes()[:4] == b'\x89PNG'
    print(f'Created {files}')

if __name__ == '__main__':
    test_plot_stats()
    test_png()
