
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

"""The interface implemented by the plotting backends, and their registry (see
also plotting.py)."""

__all__ = []

import importlib
import inspect
import pathlib

from ._common import MCPLError


class PlotBackend:
    """Interface for plotting backends, which can show or save a list of
    Figure objects."""
    name = None
    #File extensions supported by save():
    formats = ()
    def show( self, figures ):
        """Show the figures interactively."""
        raise NotImplementedError
    def save( self, figures, filename ):
        """Save the figures in a file, with format given by the extension of
        the filename (one of the formats). If the format can only hold a single
        figure, and there are more figures, files with numbered names are
        created (e.g. plot_1.png, plot_2.png). Returns the list of created
        files."""
        raise NotImplementedError
    def check_format( self, filename ):
        ext = pathlib.Path(filename).suffix.lower().lstrip('.')
        if ext not in self.formats:
            raise MCPLError(f'The {self.name} plotting backend can not create'
                            f' .{ext} files (supported: '
                            + ', '.join(f'.{e}' for e in self.formats) + ')')
        return ext

def numbered_filenames( filename, n ):
    """Filenames for n figures: just filename if n==1, otherwise with
    numbers added before the extension."""
    if n == 1:
        return [ filename ]
    p = pathlib.Path(filename)
    return [ str(p.with_name(f'{p.stem}_{i+1}{p.suffix}')) for i in range(n) ]

#Backends in order of preference, with the modules implementing them. Each
#module has a Backend class implementing the PlotBackend interface, and
#is_available() and requirement for checking if the needed Python package is
#installed (without importing it). The modules are loaded when needed:
_backends = { 'matplotlib' : '_plotbackend_mpl',
              'plotly' : '_plotbackend_plotly' }
#Backend for unit tests (not listed by available_backends):
_test_backends = { 'test' : '_plotbackend_test' }

def _load( name ):
    modname = _backends.get(name) or _test_backends.get(name)
    if not modname:
        raise MCPLError(f'Unknown plotting backend "{name}" (the plotting'
                        ' backends are: ' + ', '.join(_backends) + ')')
    mod = importlib.import_module(f'.{modname}',__package__)
    return mod

def _available_backends():
    return [ n for n in _backends if _load(n).is_available() ]

def _create_backend( name = None, **kwargs ):
    """Create plotting backend with the given name, or the first available
    one in the order of _available_backends() if no name is given. Keyword
    arguments are passed on to the backend."""
    if name is None:
        avail = _available_backends()
        if not avail:
            raise MCPLError('No plotting backend available. Please install'
                            ' matplotlib (or plotly) to make plots.')
        name = avail[0]
    mod = _load(name)
    if not mod.is_available():
        raise MCPLError(f'The {name} plotting backend is not available'
                        f' (install the {mod.requirement} Python module)')
    unsupported = set(kwargs) - set(inspect.signature(mod.Backend).parameters)
    if unsupported:
        raise MCPLError(f'Unsupported option(s) for the {name} plotting'
                        ' backend: ' + ', '.join(sorted(unsupported)))
    return mod.Backend(**kwargs)
