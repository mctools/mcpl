
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

"""The description of figures which the plotting backends draw (see
plotting.py, which provides these classes)."""

__all__ = []

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
        """Add an item (e.g. a StepHist) to the panel, and return it"""
        self.items.append(item)
        return item

class Figure:
    """Figure (page) with panels arranged in a grid of nrows x ncols."""
    def __init__( self, title = None, panels = None, nrows = 1, ncols = 1 ):
        self.title = title
        self.panels = list(panels or [])
        self.nrows, self.ncols = nrows, ncols
    def add( self, panel ):
        """Add a panel to the figure, and return it"""
        self.panels.append(panel)
        return panel
