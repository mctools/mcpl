
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
import os
import pathlib

from ._common import MCPLError


class PlotBackend:
    """Interface of plotting backends (public as mcpl.plotting.Backend), which
    show or save lists of Figure objects. Subclasses set name (a unique name
    used to select the backend), formats (the file extensions which save() can
    create), and requirement (the Python package needed, if any), and implement
    show() and save(), and is_available() if not always available. Options can
    be given as keyword arguments to __init__, named with the backend name as
    prefix (like matplotlib_backend)."""
    name = None
    formats = ()
    requirement = None

    @classmethod
    def is_available( cls ):
        """Whether the backend can be used (e.g. if its requirement is
        installed). This should not import any heavy modules."""
        return True

    @classmethod
    def available_formats( cls ):
        """File extensions which save() can create in this installation"""
        return tuple(cls.formats)

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
        ext = pathlib.Path(filename).suffix.lower().lstrip('.')
        avail = self.available_formats()
        if ext not in avail:
            raise MCPLError(f'The {self.name} plotting backend can not create'
                            f' .{ext} files (supported: '
                            + ', '.join(f'.{e}' for e in avail) + ')')
        return ext

def numbered_filenames( filename, n ):
    """Filenames for n figures: just filename if n==1, otherwise with
    numbers added before the extension."""
    if n == 1:
        return [ filename ]
    p = pathlib.Path(filename)
    return [ str(p.with_name(f'{p.stem}_{i+1}{p.suffix}')) for i in range(n) ]

#Registered backends in order of preference (by name), as names of the modules
#implementing the built-in ones (loaded when needed, with the name of the class
#after a colon if it is not Backend), or classes:
_registry = { 'matplotlib' : '_plotbackend_mpl',
              'plotly' : '_plotbackend_plotly',
              'unicode' : '_plotbackend_text:UnicodeBackend',
              'ascii' : '_plotbackend_text:AsciiBackend' }
#Backend for unit tests (not listed by available_backends):
_hidden = { 'test' : '_plotbackend_test' }
#Default backend set with set_default_backend (name or PlotBackend object):
_default = None
_envvar = 'MCPL_PLOT_BACKEND'

def _backend_class( name, source = None ):
    entry = _registry.get(name) or _hidden.get(name)
    if entry is None:
        raise MCPLError(f'Unknown plotting backend "{name}"{_from(source)}. The'
                        ' plotting backends are: ' + ', '.join(_registry))
    if isinstance(entry,str):
        modname, _, clsname = entry.partition(':')
        mod = importlib.import_module(f'.{modname}',__package__)
        entry = getattr(mod,clsname or 'Backend')
    return entry

def _from( source ):
    return f' (selected with {source})' if source else ''

def _register_backend( cls ):
    if not ( isinstance(cls,type) and issubclass(cls,PlotBackend) ):
        raise MCPLError('register_backend must be called with a subclass of'
                        ' mcpl.plotting.Backend')
    if not ( isinstance(cls.name,str) and cls.name ):
        raise MCPLError('Plotting backends must have a name')
    if cls.name in _registry or cls.name in _hidden:
        raise MCPLError(f'A plotting backend named "{cls.name}" is already'
                        ' registered')
    _registry[cls.name] = cls

def _available_backends():
    return [ n for n in _registry if _backend_class(n).is_available() ]

def _set_default_backend( backend ):
    global _default
    if backend is not None and not isinstance(backend,PlotBackend):
        if not isinstance(backend,str):
            raise MCPLError('set_default_backend must be called with the name'
                            ' of a plotting backend, a mcpl.plotting.Backend'
                            ' object, or None')
        _backend_class(backend)#check that the name is known
    _default = backend

def _chosen( backend ):
    """Backend selected (name or object), and how it was selected (for error
    messages), or (None,None) if the first available should be used"""
    if backend is not None:
        return backend, None
    if _default is not None:
        return _default, 'set_default_backend'
    env = os.environ.get(_envvar,'').strip()
    if env:
        return env, f'the {_envvar} environment variable'
    return None, None

def _backend_name( backend = None ):
    """Name of the backend which would be used (None if none available)"""
    b, _ = _chosen(backend)
    if isinstance(b,PlotBackend):
        return b.name
    if b is None:
        avail = _available_backends()
        return avail[0] if avail else None
    return b

def _resolve( backend ):
    """Backend object or class to use"""
    b, source = _chosen(backend)
    if isinstance(b,PlotBackend):
        return b
    if b is None:
        avail = _available_backends()
        if not avail:
            raise MCPLError('No plotting backend available. Please install'
                            ' matplotlib (or plotly) to make plots.')
        b = avail[0]
    if not isinstance(b,str):
        raise MCPLError('The backend must be the name of a plotting backend or'
                        ' a mcpl.plotting.Backend object')
    cls = _backend_class(b,source)
    if not cls.is_available():
        raise MCPLError(f'The {b} plotting backend{_from(source)} is not'
                        ' available' + ( f' (install the {cls.requirement}'
                                         ' Python package)' if cls.requirement else '' ))
    return cls

def _create_backend( backend = None, **options ):
    """Backend object to use (see _chosen), created with the options."""
    b = _resolve(backend)
    if isinstance(b,PlotBackend):
        if options:
            raise MCPLError('Options for plotting backends ('
                            + ', '.join(sorted(options)) + ') can not be used'
                            ' together with a mcpl.plotting.Backend object')
        return b
    unsupported = set(options) - set(inspect.signature(b).parameters)
    if unsupported:
        raise MCPLError(f'Unsupported option(s) for the {b.name} plotting'
                        ' backend: ' + ', '.join(sorted(unsupported)))
    return b(**options)

def _formats( backend = None ):
    return tuple(_resolve(backend).available_formats())
