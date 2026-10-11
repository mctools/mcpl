
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

"""Backend-independent description of plots, and functions to show or save
them. Plots are described with the Figure, Panel and item classes below (which
hold numbers, not graphics objects), and are drawn by one of the plotting
backends: matplotlib or plotly (see available_backends()), unicode or ascii
(which draw the plots as text, in the terminal or in .txt files), or a custom
backend (see Backend and register_backend()).

Unless a backend is specified when plotting, the default backend is used: the
one set with set_default_backend(), or else the one named by the
MCPL_PLOT_BACKEND environment variable, or else the first available one.

For instance:

   from mcpl.plotting import Figure, Panel, StepHist, save
   fig = Figure( panels = [ Panel( title = 'My histogram', xlabel = 'x [cm]',
                                   items = [ StepHist(edges,values) ] ) ] )
   save( fig, 'myplot.pdf' )
"""

__all__ = [ 'Backend', 'Bars', 'Figure', 'Hist2D', 'Panel', 'StepHist', 'Text',
            'available_backends', 'formats', 'register_backend', 'save',
            'set_default_backend', 'show' ]

from ._plotbackend import (
    PlotBackend,
    _available_backends,
    _create_backend,
    _formats,
    _register_backend,
    _set_default_backend,
)

Backend = PlotBackend


class StepHist:
    """1D histogram drawn as a step line. The bin edges have one more entry
    than the values. The color is an index into the colour cycle of the
    backend (by default the position of the item in the panel)."""
    def __init__( self, edges, values, label = None, color = None ):
        self.edges, self.values, self.label = edges, values, label
        self.color = color

class Hist2D:
    """2D histogram drawn as a coloured map (with logarithmic colour scale if
    logz is set). The values have shape (len(xedges)-1,len(yedges)-1)."""
    def __init__( self, xedges, yedges, values, logz = True ):
        self.xedges, self.yedges, self.values = xedges, yedges, values
        self.logz = logz

class Bars:
    """Bar chart with a bar for each label (horizontal if horizontal is set)."""
    def __init__( self, labels, values, horizontal = False ):
        self.labels, self.values, self.horizontal = labels, values, horizontal

class Text:
    """Message shown in the middle of a panel (e.g. "No data")."""
    def __init__( self, text ):
        self.text = text

class Panel:
    """One plot (a set of axes) with items like StepHist objects. Items with
    labels are shown in a legend."""
    def __init__( self, title = None, xlabel = None, ylabel = None,
                  logx = False, logy = False, xlim = None, ylim = None,
                  items = None ):
        self.title, self.xlabel, self.ylabel = title, xlabel, ylabel
        self.logx, self.logy, self.xlim, self.ylim = logx, logy, xlim, ylim
        self.items = list(items or [])
    def add( self, item ):
        self.items.append(item)
        return item

class Figure:
    """Figure (page) with panels arranged in a grid of nrows x ncols."""
    def __init__( self, title = None, panels = None, nrows = 1, ncols = 1 ):
        self.title = title
        self.panels = list(panels or [])
        self.nrows, self.ncols = nrows, ncols
    def add( self, panel ):
        self.panels.append(panel)
        return panel

def available_backends():
    """Names of the plotting backends which can be used (i.e. for which the
    required Python packages are installed), in order of preference."""
    return _available_backends()

def register_backend( backend_class ):
    """Register a custom plotting backend, a subclass of Backend, which can
    then be selected by its name (it is added after the built-in backends in
    the order of preference)."""
    _register_backend(backend_class)

def set_default_backend( backend ):
    """Set the plotting backend to use when no backend is specified: the name
    of a backend, or a Backend object. If that backend is not available when
    plotting, an error is raised. Use None to go back to using the
    MCPL_PLOT_BACKEND environment variable (if set) or the first available
    backend."""
    _set_default_backend(backend)

def formats( backend = None ):
    """File extensions of the formats which the backend (name or Backend
    object, default is the default backend) can save in this installation."""
    return list(_formats(backend))

def _as_list( figures ):
    return [ figures ] if isinstance(figures,Figure) else list(figures)

def show( figures, backend = None, **options ):
    """Show a Figure (or a list of figures) interactively, with the plotting
    backend of the given name (or a Backend object, default is the default
    backend). Further keyword arguments are options for the backend, named
    with the backend name as prefix (e.g. matplotlib_backend='qtagg' or
    plotly_renderer='browser')."""
    _create_backend(backend,**options).show(_as_list(figures))

def save( figures, filename, backend = None, **options ):
    """Save a Figure (or a list of figures) in a file, with the plotting
    backend of the given name (or a Backend object, default is the default
    backend).
    The format is given by the extension of the filename: .pdf, .png or .svg
    with matplotlib, .html with plotly (or .pdf, .png or .svg if the
    kaleido package is installed), and .txt with unicode and ascii. If the format can only hold one figure,
    and there are more figures, the files get numbered names (e.g. plot_1.png,
    plot_2.png). Returns the list of created files. Further keyword arguments
    are options for the backend (see show())."""
    return _create_backend(backend,**options).save(_as_list(figures),filename)
