
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

"""Figures for tests of the plotting backends, with the kinds of plots of
mcpl: curves (also several in one plot), a 2D map, and bars."""

_plots = ( 'ekin;logx=auto;logy;display_by=pdgcode', 'angle(dir,(0,0,1))/deg;logy;display_by=pdgcode',
           'x : y', 'time;logx=auto;logy;display_by=single', 'pdgcode;bar;logy=auto',
           'x;display_by=single' )

def example_figures( mcpl, filename ):
    """An overview of 6 plots of the file (2 rows of 3, with the title of the
    file), followed by each of them on its own (mcpl is the mcpl module)"""
    import pathlib
    hists = [ mcpl.histogram(filename,p) for p in _plots ]
    overview = mcpl.plotting.Figure( title = f'Overview of {pathlib.Path(filename).name}', nrows = 2,
                                     ncols = 3, panels = [ h.panel() for h in hists ] )
    return [ overview ] + [ h.figure() for h in hists ]

def items_figure( mcpl ):
    """A figure with all kinds of items and panels (mcpl is the mcpl module): a
    3D scatter plot, an empty cell, a 2D map with the same scale on both axes,
    bars with colours, and 25 curves (more than the 10 colours, so also dashed
    and dotted), one with the symbol of the gamma in its label"""
    import numpy as np
    P = mcpl.plotting
    Bars, Figure, Hist2D, Panel = P.Bars, P.Figure, P.Hist2D, P.Panel
    Scatter3D, StepHist = P.Scatter3D, P.StepHist
    import importlib
    gamma = importlib.import_module(f'{mcpl.__name__}._particles')._pdg_symbols['gamma']
    t = np.linspace(0.0,6.0,50)
    scatter = Panel( title = '3D', xlabel = 'x', ylabel = 'y', zlabel = 'z',
                     items = [ Scatter3D(np.cos(t),np.sin(t),t,label='helix') ] )
    edges = np.linspace(0.0,4.0,5)
    square = Panel( title = 'Same scales', aspect = 1.0,
                    items = [ Hist2D(edges,edges,np.arange(16.0).reshape(4,4)) ] )
    bars = Panel( title = 'Coloured bars',
                  items = [ Bars(['a','b','c'],[1.0,3.0,2.0],colors=[0,1,12]) ] )
    curves = Panel( title = 'Curves', xlabel = 'x' )
    x = np.linspace(0.0,10.0,11)
    for k in range(25):
        curves.add(StepHist(x,np.full(10,k+1.0),label=gamma if k == 1 else f'c{k}'))
    return Figure( title = 'All items', nrows = 2, ncols = 3,
                   panels = [ scatter, None, square, bars, curves ] )
