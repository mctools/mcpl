
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

"""The plotting backends which show or save figures: matplotlib (in windows,
and .pdf, .png and .svg files) and unicode, or else ascii (in the terminal, and
.txt files)."""

__all__ = []

import contextlib
import importlib

from ._common import MCPLError
from ._plotbackend import _extension

#The backends, as the modules implementing them (loaded when needed, with the
#name of the class after a colon if it is not Backend), including the backend
#for unit tests:
_registry = { 'matplotlib' : '_plotbackend_mpl',
              'unicode' : '_plotbackend_text:UnicodeBackend',
              'ascii' : '_plotbackend_text:AsciiBackend',
              'test' : '_plotbackend_test' }
#Backend used instead of the others (see _forced_backend):
_forced = None

def _backend_class( name ):
    modname, _, clsname = _registry[name].partition(':')
    mod = importlib.import_module(f'.{modname}',__package__)
    return getattr(mod,clsname or 'Backend')

@contextlib.contextmanager
def _forced_backend( name ):
    """Within the context, plots are shown and saved with the backend of the
    given name (for unit tests, e.g. 'test', which describes the figures)"""
    global _forced
    old, _forced = _forced, name
    try:
        yield
    finally:
        _forced = old

def _create( cls, width = None, height = None, color = None ):
    """Backend object of the class, with the settings of plots in the terminal
    (if given)"""
    opts = { k : v for k, v in ( ('width',width), ('height',height), ('color',color) )
             if v is not None }
    return cls(**opts)

_window_hint = ' Use terminal=True to show them in the terminal.'

def _show_backend( terminal = False, width = None, height = None, color = None,
                   hint = _window_hint ):
    """Backend object for showing plots: in a window with matplotlib, or in the
    terminal if terminal is True (with unicode, or else ascii, characters) or
    'ascii' (with ascii characters), with the size (width and height in
    characters) and the colour setting of plots in the terminal. When plots
    can not be shown in a window, the error message ends with hint."""
    if not ( terminal is True or terminal is False or terminal == 'ascii' ):
        raise MCPLError(f'terminal must be True, False or "ascii" (not {terminal!r})')
    if not terminal:
        for name, v in ( ('width',width), ('height',height), ('color',color) ):
            if v is not None:
                raise MCPLError(f'terminal_{name} can only be used with terminal=True')
    if _forced is not None:
        return _create(_backend_class(_forced),width,height,color)
    if not terminal:
        cls = _backend_class('matplotlib')
        if not cls.is_available():
            raise MCPLError('Plots can not be shown in a window, since matplotlib'
                            ' is not installed.' + hint)
        if not cls.can_show():
            raise MCPLError('Plots can not be shown in a window here (is there no'
                            ' display?).' + hint)
        return cls()
    cls = _backend_class('unicode')
    if terminal == 'ascii' or not cls.can_show():
        cls = _backend_class('ascii')
    return _create(cls,width,height,color)

#The formats of saved plots, and the backends creating them:
_save_formats = { 'pdf' : 'matplotlib', 'png' : 'matplotlib', 'svg' : 'matplotlib',
                  'txt' : 'unicode' }

def _save_backend( filename, width = None, height = None ):
    """Backend object for saving plots in filename, for the format given by
    the extension (with the size of plots in .txt files, if given)"""
    ext = _extension(filename)
    if ext not in _save_formats:
        what = ( f'The file name {filename} has no extension' if not ext else
                 f'Plots can not be saved as .{ext} files' )
        raise MCPLError(f'{what} (the extension gives the format of the plots: '
                        + ', '.join( f'.{e}' for e in _save_formats ) + ')')
    name = _save_formats[ext]
    if name != 'unicode':
        for n, v in ( ('width',width), ('height',height) ):
            if v is not None:
                raise MCPLError(f'terminal_{n} can only be used for plots in the'
                                ' terminal or in .txt files')
    if _forced is not None:
        return _create(_backend_class(_forced),width,height)
    cls = _backend_class(name)
    if not cls.is_available():
        raise MCPLError(f'Plots can not be saved as .{ext} files, since'
                        f' {cls.requirement} is not installed')
    return _create(cls,width,height)

def _resolution( terminal = False, width = None, height = None ):
    """Number of bins which histograms should have to match the resolution of
    the plots shown (as with show), as a tuple (nx,ny), or None if the
    backend has no preference. The text backends have a resolution (their
    numbers of columns and rows), so histograms with that many bins are drawn
    without any resampling."""
    return _show_backend(terminal,width,height).resolution()
