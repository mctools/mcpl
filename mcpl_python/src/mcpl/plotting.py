
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

"""Description of plots, and functions to show or save them. Plots are
described with the Figure, Panel and item classes below (which hold numbers,
not graphics objects), and are shown in a window with matplotlib, or in the
terminal with terminal=True (drawn as text with Unicode characters, or else
ASCII, or always ASCII with terminal='ascii'). They are saved in files of the
format given by the extension: .pdf, .png or .svg (with matplotlib), or .txt
(as text with Unicode characters).

For instance:

   from mcpl.plotting import Figure, Panel, StepHist
   from mcpl.plotting import save
   hist = StepHist(edges,values)
   panel = Panel( title = 'My histogram',
                  xlabel = 'x [cm]',
                  items = [ hist ] )
   save( Figure( panels = [ panel ] ), 'myplot.pdf' )
"""

__all__ = [ 'Bars', 'Figure', 'Hist2D', 'Panel', 'Scatter3D', 'StepHist', 'Text',
            'save', 'show' ]

from ._figures import Bars, Figure, Hist2D, Panel, Scatter3D, StepHist, Text
from ._plotregistry import _save_backend, _show_backend


def _as_list( figures ):
    return [ figures ] if isinstance(figures,Figure) else list(figures)

def show( figures, terminal = False, terminal_width = None, terminal_height = None,
          terminal_color = None ):
    """Show a Figure (or a list of figures) in a window with matplotlib, or in
    the terminal if terminal is True (drawn with Unicode characters, or else
    ASCII) or 'ascii' (with ASCII characters). The size of plots in the
    terminal is terminal_width and terminal_height characters (default is the
    width of the terminal, up to 250, and a height of 15), and terminal_color
    sets whether they are in colour: 'auto' (the default: in terminals,
    unless the NO_COLOR environment variable is set, or always if FORCE_COLOR
    is set), 'always' or 'never'."""
    _show_backend(terminal,terminal_width,terminal_height,
                  terminal_color).show(_as_list(figures))

def save( figures, filename, terminal_width = None, terminal_height = None ):
    """Save a Figure (or a list of figures) in a file, in the format given by
    the extension of the filename: .pdf, .png or .svg (with matplotlib), or
    .txt (as text with Unicode characters, terminal_width and terminal_height
    characters wide and high, see show()). If the format can only hold one
    figure, and there are more figures, the files get numbered names (e.g.
    plot_1.png, plot_2.png). Returns the list of created files."""
    return _save_backend(filename,terminal_width,
                         terminal_height).save(_as_list(figures),filename)
