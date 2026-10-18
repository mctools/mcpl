
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

# Test the statistics collected for the overview page of plot_stats, that
# plot_stats works for all reference files, and that the matplotlib plotting
# backend can create PNG files.

import pathlib

import mcpldev as mcpl
import numpy as np
from MCPLTestUtils.dirs import test_data_dir

example_file = test_data_dir.joinpath('example.mcpl')

def check_overview(fn, pick=None):
    s = mcpl.collect_stats(fn, pick=pick)
    ov = s['overview']
    integral = s['file']['integral']
    print(f'{pathlib.Path(fn).name} (pick: {pick}): {s["file"]["nparticles"]} particles,'
          f' ekin bins log: {ov["ekin_log"]}, time bins log: {ov["time_log"]}')
    for k, h in ov['ekin'].items():
        print(f'   ekin hist of {k}: sum {h.sum():g}, theta hist sum {ov["theta"][k].sum():g}')
    for k, h in ov['wl'].items():
        print(f'   wavelength hist of {k}: sum {h.sum():g}')
    tot = sum(h.sum() for h in ov['ekin'].values())
    assert np.isclose(tot, integral)
    assert np.isclose(sum(h.sum() for h in ov['theta'].values()), integral)
    assert np.isclose(ov['time'].sum(), integral)
    for k, h in ov['wl'].items():
        assert np.isclose(h.sum(), ov['ekin'][k].sum())
    xyout = s['x']['hist_outside'] + s['y']['hist_outside']
    print(f'   xy hist sum {ov["xy"].sum():g} (weight outside x or y range: {xyout:g})')
    assert ov['xy'].sum() <= integral and ov['xy'].sum() >= integral - xyout - 1e-9
    for v in ('ekin','x','time'):
        print(f'   {v} weight outside plot range: {s[v]["hist_outside"]:g}')
    return s

def test_plots():
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
        mcpl.plot_stats(mcpl.collect_stats(f), filename=pdf)
        assert pathlib.Path(pdf).stat().st_size > 1000
        print(f'plot_stats ok for {f.name}')

def test_png():
    figs = mcpl.stats_figures(example_file)[:3]
    files = mcpl.plotting.save(figs, 'stats.png', backend='matplotlib', matplotlib_backend='agg')
    for f in files:
        assert pathlib.Path(f).read_bytes()[:4] == b'\x89PNG'
    print(f'Created {files}')
    #mcpltool with the default backend (matplotlib, which then uses its agg
    #backend for saving files):
    rc = 0
    try:
        mcpl.app_mcpltool(['mcpltool','-S','-o','tool.png',str(example_file)])
    except SystemExit as e:
        rc = e.code
    created = sorted(f.name for f in pathlib.Path('.').glob('tool*.png'))
    assert rc == 0 and created == ['tool.png'] and all(
        pathlib.Path(f).read_bytes()[:4] == b'\x89PNG' for f in created )
    print('mcpltool -S -o tool.png created the overview plot in tool.png')

check_overview(example_file)
check_overview(example_file, 'pdgcode == neutron and ekin < 1MeV')
check_overview(example_file, 'pdgcode == gamma')
check_overview(test_data_dir.joinpath('ref','reffile_1.mcpl'))
test_plots()
test_png()
