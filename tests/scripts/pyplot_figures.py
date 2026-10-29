
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

# Test the plotting module with the test backend (which prints descriptions of
# the figures), also with figures of histograms.

import pathlib

import mcpldev as mcpl
import numpy as np
from mcpldev.plotting import Bars, Figure, Hist2D, Panel, StepHist, Text
from MCPLTestUtils.dirs import test_data_dir
from MCPLTestUtils.plots import example_figures, items_figure

example_file = test_data_dir.joinpath('example.mcpl')

def test_backends():
    avail = mcpl.plotting.available_backends()
    assert set(avail) <= {'matplotlib','unicode','ascii'} and 'test' not in avail
    print('available_backends() only lists known backends, and not the test backend')
    for name, fn in ( ('nosuchbackend', 'x.pdf'), ('test', 'x.foo') ):
        try:
            mcpl.plotting.save(Figure(), fn, backend=name)
        except mcpl.MCPLError as e:
            print(f'save(...,{fn!r},backend={name!r}): {e}')
    try:
        mcpl.plotting.save(Figure(), 'x.txt', backend='test', matplotlib_backend='agg')
    except mcpl.MCPLError as e:
        print(f"save(...,backend='test',matplotlib_backend='agg'): {e}")

def test_figures():
    edges = np.linspace(0.0,10.0,11)
    fig = Figure( title = 'Example', nrows = 2, ncols = 2 )
    p = fig.add(Panel( title = 'Steps', xlabel = 'x [cm]', logy = True,
                       xlim = (0.0,10.0) ))
    p.add(StepHist(edges,np.arange(10.0),label='first'))
    p.add(StepHist(edges,np.ones(10),label='second',color=3))
    fig.add(Panel( title = '2D', items = [ Hist2D(edges,edges[:5],np.ones((10,4))) ] ))
    fig.add(Panel( title = 'Bars', items = [ Bars(['a','b'],[1.0,2.0],horizontal=True) ] ))
    fig.add(Panel( title = 'Text', items = [ Text('No data') ] ))
    mcpl.plotting.show(fig, backend='test')
    files = mcpl.plotting.save([fig,Figure(title='Empty')], 'figs.txt', backend='test')
    nlines = len(pathlib.Path(files[0]).read_text(encoding='utf-8').splitlines())
    print(f'save() created {files}, with {nlines} lines')

def test_example_figures():
    mcpl.plotting.show(example_figures(mcpl,example_file), backend='test')

def test_items():
    #All kinds of items, also as text (where 3D plots give a message, and the
    #symbol of the gamma is written as its name with the ascii backend):
    from mcpldev._figures import _line_style
    fig = items_figure(mcpl)
    mcpl.plotting.show(fig, backend='test')
    print('line styles of curves 0, 9, 10, 20 and 30:',
          [ _line_style(k) for k in (0, 9, 10, 20, 30) ])
    for backend in ('unicode','ascii'):
        files = mcpl.plotting.save(fig, f'items_{backend}.txt', backend=backend,
                                   **{ f'{backend}_width' : 60, f'{backend}_height' : 6 })
        text = pathlib.Path(files[0]).read_text(encoding='utf-8')
        print(f'==> {backend}:')
        print(text)

if __name__ == '__main__':
    test_backends()
    test_figures()
    test_example_figures()
    test_items()
