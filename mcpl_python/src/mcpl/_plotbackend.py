
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

"""The interface implemented by the plotting backends (see also plotting.py, and
_plotregistry.py for their registry)."""

__all__ = []

import pathlib
from typing import ClassVar

from ._common import MCPLError


class PlotBackend:
    """Interface of plotting backends (public as mcpl.plotting.Backend), which
    show or save lists of Figure objects. Subclasses set name (a unique name
    used to select the backend), kind (what plots are shown on: 'window' or
    'terminal', or None for backends which are only used when
    selected by name), priority (the preference among the backends of the
    same kind, higher is preferred), formats (a dict with the file extensions
    which save() can create, and their priorities among the backends which can
    create them) and requirement (the Python package needed, if any). They
    implement show() and save(), and is_available() and can_show() if the
    backend is not always available or able to show plots. Options can be
    given as keyword arguments to __init__, named with the backend name as
    prefix (like matplotlib_backend)."""
    name = None
    kind = None
    priority = 0
    formats: ClassVar[dict] = {}
    requirement = None
    #Options to use when plots are only saved in files, e.g. by mcpltool (like
    #a backend of matplotlib which needs no display):
    batch_options: ClassVar[dict] = {}

    @classmethod
    def is_available( cls ):
        """Whether the backend can be used (e.g. if its requirement is
        installed). This should not import any heavy modules."""
        return True

    @classmethod
    def can_show( cls ):
        """Whether the backend can show plots here (e.g. if there is a
        display), assuming that it is available."""
        return True

    @classmethod
    def available_formats( cls ):
        """File extensions which save() can create in this installation"""
        return tuple(cls.formats)

    def resolution( self ):
        """Number of bins which histograms should have to match the resolution
        of the plots, as a tuple (nx,ny) for the two axes, or None if the
        backend has no preference (like matplotlib, which draws
        bins at any resolution). The text backends return the numbers of
        columns and rows of their plots, so histograms with that many bins
        are shown without any resampling."""
        return

    def show( self, figures ):
        """Show the figures interactively."""
        raise NotImplementedError

    def save( self, figures, filename ):
        """Save the figures in a file, with format given by the extension of
        the filename (one of the available formats). If the format can only
        hold a single figure, and there are more figures, files with numbered
        names are created (e.g. plot_1.png, plot_2.png). Returns the list of
        created files."""
        raise NotImplementedError

    def check_format( self, filename ):
        """Extension of filename, if it is an available format (otherwise
        MCPLError is raised)."""
        ext = _extension(filename)
        avail = self.available_formats()
        if ext not in avail:
            raise MCPLError(f'The {self.name} plotting backend can not create'
                            f' .{ext} files (supported: '
                            + ', '.join(f'.{e}' for e in avail) + ')')
        return ext

def _extension( filename ):
    return pathlib.Path(filename).suffix.lower().lstrip('.')

def numbered_filenames( filename, n ):
    """Filenames for n figures: just filename if n==1, otherwise with
    numbers added before the extension."""
    if n == 1:
        return [ filename ]
    p = pathlib.Path(filename)
    return [ str(p.with_name(f'{p.stem}_{i+1}{p.suffix}')) for i in range(n) ]
