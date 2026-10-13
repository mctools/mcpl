
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

"""Plotting backends drawing figures as text, with ASCII characters or with
Unicode characters (block elements and box drawing, which give smoother
plots), for showing plots in a terminal or saving them in text files."""

__all__ = []

import math
import pathlib
import shutil
import sys

from ._numpy import np
from ._plotbackend import PlotBackend
from .plotting import Bars, Hist2D, StepHist, Text


class _Chars:
    """Characters used for drawing"""
    def __init__( self, fill, hfill, shades, markers, vline, hline, corner,
                  ytick, xtick ):
        self.fill = fill#vertical fill: "" (empty), partial levels..., full
        self.hfill = hfill#horizontal fill (for bars): "", partial..., full
        self.shades = shades#for 2D maps, from empty to full
        self.markers = markers#for curves of 1D histograms with several curves
        self.vline, self.hline, self.corner = vline, hline, corner
        self.ytick, self.xtick = ytick, xtick

_ascii = _Chars( fill = ' #', hfill = ' #', shades = ' .:-=+*#%@',
                 markers = '*o+x@%&=', vline = '|', hline = '-', corner = '+',
                 ytick = '+', xtick = '+' )
#Unicode characters (written as escape sequences, to keep the code ASCII):
_unicode = _Chars(
    #lower one eighth block ... full block:
    fill = ' \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588',
    #left one eighth block ... full block:
    hfill = ' \u258f\u258e\u258d\u258c\u258b\u258a\u2589\u2588',
    #middle dot, light, medium and dark shade, full block:
    shades = ' \u00b7\u2591\u2592\u2593\u2588',
    #black and white circles, diamonds, squares and triangles:
    markers = '\u25cf\u25cb\u25c6\u25c7\u25a0\u25a1\u25b2\u25b3',
    #box drawing: light vertical, horizontal, up and right, vertical and
    #left, down and horizontal:
    vline = '\u2502', hline = '\u2500', corner = '\u2514', ytick = '\u2524',
    xtick = '\u252c' )

def _fmt( v ):
    return f'{v:.4g}'

#Width of the labels of the y axis (fixed, so the width of the plot area is
#known before the data, see resolution()):
_ylw = 8

def _fmt_y( v ):
    s = _fmt(v)
    return s if len(s) <= _ylw else f'{v:.2g}'

def _center( text, width ):
    return text.center(width).rstrip()

class _TextBackend(PlotBackend):
    """Draws figures as text (with the characters in self._chars)"""
    formats = ('txt',)
    _chars = None
    encoding = 'utf-8'

    def __init__( self, width = None, height = None ):
        if width is None:
            width = min( 250, shutil.get_terminal_size((80,24)).columns )
        self._width = max( 40, int(width) )
        self._height = max( 5, int(height or 15) )

    def resolution( self ):
        return ( self._width - _ylw - 3, self._height )

    def _fit_resolution( self, bins ):
        """Reduce the size of the plots so histograms with the given number of
        bins (or (nx,ny) for 2D histograms) are drawn with a whole number of
        columns (and rows) per bin."""
        ncols, nrows = self.resolution()
        nx, ny = bins if isinstance(bins,(tuple,list)) else ( bins, None )
        if nx and nx <= ncols:
            self._width = ( ncols - ncols % nx ) + _ylw + 3
        if ny and ny <= nrows:
            self._height = nrows - nrows % ny

    def show( self, figures ):
        print('\n\n'.join( self.draw(f) for f in figures ))

    def save( self, figures, filename ):
        self.check_format(filename)
        pathlib.Path(filename).write_text( '\n\n'.join( self.draw(f) for f in figures )
                                           + '\n', encoding = self.encoding )
        return [ filename ]

    def draw( self, figure ):
        """Text representation of the figure"""
        out = []
        if figure.title:
            out += [ _center(line,self._width) for line in figure.title.split('\n') ]
            out.append('')
        for panel in figure.panels:
            out += self._draw_panel(panel)
            out.append('')
        return '\n'.join(out).rstrip('\n')

    def _draw_panel( self, panel ):
        out = []
        if panel.title:
            out += [ _center(line,self._width) for line in panel.title.split('\n') ]
        steps = [ i for i in panel.items if isinstance(i,StepHist) ]
        if steps:
            out += self._draw_stephists(panel,steps)
        for item in panel.items:
            if isinstance(item,Hist2D):
                out += self._draw_hist2d(panel,item)
            elif isinstance(item,Bars):
                out += self._draw_bars(item)
            elif isinstance(item,Text):
                out += [ _center(line,self._width) for line in item.text.split('\n') ]
        if panel.xlabel and not steps and not any( isinstance(i,Hist2D) for i in panel.items ):
            out += [ _center(line,self._width) for line in panel.xlabel.split('\n') ]
        return out

    #Coordinates:

    @staticmethod
    def _to_display( v, log ):
        v = np.asarray(v,dtype=float)
        if not log:
            return v
        with np.errstate(divide='ignore',invalid='ignore'):
            return np.where( v > 0, np.log10(np.where(v > 0, v, 1.0)), -np.inf )

    def _xrange( self, panel, edges ):
        lo, hi = panel.xlim if panel.xlim else ( edges[0], edges[-1] )
        if panel.logx:
            pos = [ e for e in edges if e > 0 ]
            lo = lo if lo > 0 else ( pos[0] if pos else 1.0 )
            hi = hi if hi > lo else lo * 10
        elif not hi > lo:
            lo, hi = lo - 1.0, hi + 1.0
        return lo, hi

    @staticmethod
    def _overlap_matrix( edges, lo, hi, n ):
        """Matrix (n x nbins) with the fraction of each of the n equal cells
        between lo and hi which is covered by each bin. Multiplied with the
        bin values, it gives the average of the values over each cell, i.e.
        the step function of the histogram resampled to the cells (assuming
        the contents of each bin to be uniformly distributed inside it). The
        rows sum to the fraction of the cell covered by any bin (at most 1).
        Bins can extend to +-infinity (e.g. in log scale)."""
        edges = np.asarray(edges,dtype=float)
        cellwidth = ( hi - lo ) / n
        bounds = lo + np.arange(n+1) * cellwidth
        with np.errstate(invalid='ignore'):
            overlap = ( np.minimum( edges[None,1:], bounds[1:,None] )
                        - np.maximum( edges[None,:-1], bounds[:-1,None] ) )
            ok = ( edges[1:] > edges[:-1] )
            frac = np.where( ok[None,:], overlap / cellwidth, 0.0 )
        return np.clip( np.nan_to_num(frac,nan=0.0), 0.0, 1.0 )

    def _columns( self, edges, values, lo, hi, log, ncols ):
        """Values of the columns, i.e. the average of the bin values over each
        column (NaN for columns outside the range of the bins)"""
        d = self._to_display(edges,log)
        dlo, dhi = self._to_display([lo,hi],log)
        m = self._overlap_matrix(d,dlo,dhi,ncols)
        res = m @ np.asarray(values,dtype=float)
        res[ m.sum(axis=1) <= 0.0 ] = np.nan
        return res

    def _yscale( self, panel, allvals ):
        """Function mapping values to heights (in rows, from 0 to height), and
        the labels of the y axis (top, bottom)"""
        h = self._height
        v = np.asarray(allvals,dtype=float)
        v = v[np.isfinite(v)]
        if panel.logy:
            pos = v[v>0]
            if not len(pos):
                return ( lambda x : np.zeros_like(np.asarray(x,dtype=float)) ), ( '1', '1' )
            vmin, vmax = ( panel.ylim if panel.ylim else ( pos.min(), pos.max() ) )
            vmin = vmin if vmin > 0 else pos.min()
            lmin, lmax = math.log10(vmin), math.log10(vmax)
            if not lmax > lmin:
                lmin, lmax = lmin - 1, lmax + 1
            def height( x ):
                x = np.asarray(x,dtype=float)
                with np.errstate(divide='ignore',invalid='ignore'):
                    lx = np.log10(np.where(x > 0, x, vmin))
                return np.where( x > 0, np.clip( ( lx - lmin ) / ( lmax - lmin ) * h, 0, h ), 0.0 )
            return height, ( _fmt_y(10**lmax), _fmt_y(10**lmin) )
        vmin, vmax = panel.ylim if panel.ylim else ( min(0.0,v.min()) if len(v) else 0.0,
                                                     v.max() if len(v) else 1.0 )
        if not vmax > vmin:
            vmax = vmin + 1.0
        def height( x ):
            return np.clip( ( np.asarray(x,dtype=float) - vmin ) / ( vmax - vmin ) * h, 0, h )
        return height, ( _fmt_y(vmax), _fmt_y(vmin) )

    #Drawing:

    def _frame( self, rows, ylabels, ncols, lo, hi, logx, xlabel ):
        """Add y axis (with labels at top and bottom), x axis with tick labels
        at the ends and the middle, and the x label, to the rows of the plot
        area (top row first)"""
        c = self._chars
        top, bottom = ylabels
        lw = _ylw
        out = []
        for i,r in enumerate(rows):
            label = top if i == 0 else ( bottom if i == len(rows) - 1 else '' )
            tick = c.ytick if label else c.vline
            out.append( f'{label:>{lw}} {tick}{r}'.rstrip() )
        out.append( ' ' * lw + ' ' + c.corner + c.xtick + c.hline * ( ncols - 2 ) + c.xtick )
        mid = math.sqrt(lo*hi) if logx else 0.5 * ( lo + hi )
        a, m, b = _fmt(lo), _fmt(mid), _fmt(hi)
        axis = [' '] * ( ncols + 2 )
        def put( text, pos ):
            pos = max( 0, min( len(axis) - len(text), pos ) )
            axis[pos:pos+len(text)] = list(text)
        put(a,0)
        put(b,ncols+1-len(b))
        if ncols > len(a) + len(b) + len(m) + 4:
            put(m,( ncols + 1 ) // 2 - len(m) // 2)
        out.append( ' ' * ( lw + 1 ) + ''.join(axis).rstrip() )
        if xlabel:
            out += [ ' ' * ( lw + 2 ) + _center(line,ncols) for line in xlabel.split('\n') ]
        return out

    def _draw_stephists( self, panel, steps ):
        c = self._chars
        lo, hi = self._xrange(panel, [ e for s in steps for e in ( s.edges[0], s.edges[-1] ) ])
        ncols = self.resolution()[0]
        cols = [ self._columns(s.edges,s.values,lo,hi,panel.logx,ncols) for s in steps ]
        #(the vertical scale is for the values of the columns):
        allvals = np.concatenate(cols)
        height, ylabels = self._yscale(panel,allvals[np.isfinite(allvals)])
        h = self._height
        grid = [ [' '] * ncols for _ in range(h) ]
        if len(steps) == 1:
            #Filled columns, with partial characters for fractions of rows:
            nlev = len(c.fill) - 1
            for j,v in enumerate(cols[0]):
                if not np.isfinite(v):
                    continue
                units = round( float(height(v)) * nlev )
                for row in range(h):
                    k = min( nlev, max( 0, units - row * nlev ) )
                    if k:
                        grid[h-1-row][j] = c.fill[k]
        else:
            #A marker symbol for each curve (for bins with contents, drawing
            #the first curves last, so they are on top):
            for k in reversed(range(len(cols))):
                sym = self._marker(steps[k],k)
                for j,v in enumerate(cols[k]):
                    if not ( np.isfinite(v) and v > 0 ):
                        continue
                    row = min( h - 1, int(float(height(v))) )
                    grid[h-1-row][j] = sym
        out = self._frame([ ''.join(r) for r in grid ], ylabels, ncols, lo, hi,
                          panel.logx, panel.xlabel)
        if panel.ylabel:
            out.insert( 0, f'({panel.ylabel})' )
        labels = [ s.label for s in steps ]
        if any( lab is not None for lab in labels ):
            if len(steps) == 1:
                out.append( f'{c.fill[-1]} {labels[0]}' )
            else:
                out += [ f'{self._marker(s,k)} {s.label}'
                         for k,s in enumerate(steps) if s.label is not None ]
        return out

    def _marker( self, item, k ):
        """Marker symbol of the k'th StepHist of a panel"""
        m = self._chars.markers
        return m[ ( item.color if item.color is not None else k ) % len(m) ]

    def _draw_bars( self, item ):
        c = self._chars
        labels = [ ' '.join(str(lab).split()) for lab in item.labels ]
        values = [ float(v) for v in item.values ]
        lw = max( ( len(lab) for lab in labels ), default = 0 )
        vtexts = [ _fmt(v) for v in values ]
        vw = max( ( len(t) for t in vtexts ), default = 0 )
        nmax = max( 1, self._width - lw - vw - 4 )
        vmax = max( [ v for v in values if v > 0 ], default = 1.0 )
        nlev = len(c.hfill) - 1
        out = []
        for lab, v, t in zip(labels,values,vtexts):
            units = round( max(0.0,v) / vmax * nmax * nlev )
            if v > 0:
                units = max( 1, units )#non-zero values are always visible
            bar = c.hfill[-1] * ( units // nlev ) + ( c.hfill[units % nlev] if units % nlev else '' )
            out.append( f'{lab:>{lw}} {c.vline}{bar} {t}' )
        return out

    def _draw_hist2d( self, panel, item ):
        c = self._chars
        xlo, xhi = self._xrange(panel,item.xedges)
        ylo, yhi = ( panel.ylim if panel.ylim else ( item.yedges[0], item.yedges[-1] ) )
        if not yhi > ylo:
            ylo, yhi = ylo - 1.0, yhi + 1.0
        ylabels = ( _fmt_y(yhi), _fmt_y(ylo) )
        ncols, nrows = self.resolution()
        v = np.asarray(item.values,dtype=float)
        cells = ( self._overlap_matrix(item.xedges,xlo,xhi,ncols) @ v
                  @ self._overlap_matrix(item.yedges,ylo,yhi,nrows).T )
        pos = cells[cells>0]
        nlev = len(c.shades) - 1
        grid = [ [' '] * ncols for _ in range(nrows) ]
        if len(pos):
            vmin, vmax = pos.min(), pos.max()
            for i in range(ncols):
                for j in range(nrows):
                    val = cells[i,j]
                    if not val > 0:
                        continue
                    if item.logz and vmax > vmin:
                        f = ( math.log(val) - math.log(vmin) ) / ( math.log(vmax) - math.log(vmin) )
                    else:
                        f = val / vmax
                    grid[nrows-1-j][i] = c.shades[ max( 1, math.ceil( f * nlev ) ) ]
        out = self._frame([ ''.join(r) for r in grid ], ylabels, ncols, xlo, xhi,
                          False, panel.xlabel)
        if panel.ylabel:
            out.insert( 0, f'(y: {panel.ylabel})' )
        if len(pos):
            out.append( f'{c.shades[1]} = {_fmt(vmin)} ... {c.shades[-1]} = {_fmt(vmax)}'
                        + ( ' (log scale)' if item.logz else '' ) )
        return out

class UnicodeBackend(_TextBackend):
    """Plots drawn as text with Unicode characters (block elements and box
    drawing), for terminals (in terminals which can not show these characters,
    the ASCII characters are used instead). The unicode_width and unicode_height options set
    the size of the plots in characters (default is the width of the
    terminal, up to 250, and a height of 15)."""
    name = 'unicode'
    _chars = _unicode

    def show( self, figures ):
        #In terminals which can not show the characters, the ASCII characters
        #are used instead (files are always written as UTF-8):
        enc = getattr(sys.stdout,'encoding',None) or 'ascii'
        c = self._chars
        try:
            ( c.fill + c.hfill + c.shades + c.markers + c.vline + c.hline
              + c.corner + c.ytick + c.xtick ).encode(enc)
        except (UnicodeEncodeError,LookupError):
            self._chars = _ascii
        try:
            super().show(figures)
        finally:
            self._chars = c

    def __init__( self, unicode_width = None, unicode_height = None ):
        super().__init__(unicode_width,unicode_height)

class AsciiBackend(_TextBackend):
    """Plots drawn as text with ASCII characters only, for any terminal. The
    ascii_width and ascii_height options set the size of the plots in
    characters (default is the width of the terminal, up to 250, and a height
    of 15)."""
    name = 'ascii'
    _chars = _ascii
    encoding = 'ascii'

    def __init__( self, ascii_width = None, ascii_height = None ):
        super().__init__(ascii_width,ascii_height)
