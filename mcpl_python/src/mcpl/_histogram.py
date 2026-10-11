
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

"""Histograms of values calculated with expressions from the particles in MCPL
files, and plots of them."""

__all__ = [ 'Histogram', 'Histogram2D', 'histogram', 'histogram2d',
            'plot_histograms' ]

import os

from ._common import MCPLError
from ._expressions import ParticleFilter, ParticleValue
from ._numpy import np
from ._physics import _pdg_database
from ._reader import MCPLFile
from .plotting import Figure, Hist2D, Panel, StepHist, save, show


def _as_files( sources ):
    """List of (label,source) for a file or a list of files"""
    if isinstance(sources,(str,bytes,os.PathLike,MCPLFile)):
        sources = [ sources ]
    res = []
    for s in sources:
        if isinstance(s,MCPLFile):
            label = os.path.basename(os.fsdecode(s._filename))
        else:
            label = os.path.basename(os.fsdecode(s))
        res.append( (label,s) )
    if not res:
        raise MCPLError('No files given')
    return res

def _blocks( source, flt ):
    """Iterate over (selected) particle blocks in a file"""
    f = source if isinstance(source,MCPLFile) else MCPLFile(source)
    for b in f.particle_blocks:
        yield b[flt(b)] if flt is not None else b

def _as( cls, expr ):
    if expr is None or isinstance(expr,cls):
        return expr
    return cls(expr)

def _split_label( split, key ):
    if split is None or key is None:
        #No split, or no particles (so no values of the split expression):
        return None
    if split.expression.strip() == 'pdgcode':
        descr = _pdg_database(int(key))
        return f'{descr} ({int(key)})' if descr else str(int(key))
    if key in (0.0,1.0) and split._is_bool:
        return split.expression if key else f'!({split.expression})'
    return f'{split.expression} = {key:g}'

class _SplitValue:
    """Values used to split particles into separate histograms"""
    def __init__( self, expr ):
        self._v = _as(ParticleValue,expr)
        self.expression = self._v.expression
        self._is_bool = None
    def __call__( self, block ):
        v = self._v(block)
        return v

class Histogram:
    """1D histogram of the values of an expression, created by the histogram()
    function. The bin edges are in edges, and the contents (sums of weights,
    or numbers of particles if unweighted) in the dictionary contents, with
    one entry per curve (keyed by label, None for a single curve). The sums of
    squared weights are in sumw2 (with the same keys), and the sums of weights
    below and above the range of the edges are in underflow and overflow."""
    def __init__( self, expression, edges, logx, weighted, lethargy, title ):
        self.expression = expression
        self.edges = edges
        self.logx = logx
        self.weighted = weighted
        self.lethargy = lethargy
        self.title = title
        self.contents = {}
        self.sumw2 = {}
        self.underflow = {}
        self.overflow = {}

    def values( self, label = None ):
        """Values to plot: the contents, or for lethargy plots the contents
        divided by the bin widths in lethargy (ln(E2/E1))."""
        c = self.contents[label]
        if self.lethargy:
            return c / np.log(self.edges[1:]/self.edges[:-1])
        return c

    @property
    def ylabel( self ):
        what = 'weights' if self.weighted else 'particles'
        if self.lethargy:
            return f'{what} per unit lethargy'
        return f'{what} per bin'

    def panel( self, logy = False ):
        """Panel (see mcpl.plotting) with the histogram."""
        p = Panel( title = self.title, xlabel = self.expression,
                   ylabel = self.ylabel, logx = self.logx, logy = logy,
                   xlim = ( self.edges[0], self.edges[-1] ) )
        labels = list(self.contents)
        for i,label in enumerate(labels):
            p.add(StepHist(self.edges,self.values(label),
                           label = label if len(labels) > 1 else None,
                           color = i))
        outside = sum(self.underflow.values()) + sum(self.overflow.values())
        total = outside + sum( c.sum() for c in self.contents.values() )
        if outside and total:
            p.xlabel += (f'\n({100.0*outside/total:.3g}% of'
                         f' {"weights" if self.weighted else "particles"}'
                         ' outside plot range)')
        return p

    def figure( self, logy = False ):
        """Figure (see mcpl.plotting) with the histogram."""
        return Figure( panels = [ self.panel(logy = logy) ] )

    def plot( self, filename = None, backend = None, logy = False, **options ):
        """Show the histogram (or save it in a file if filename is given) with
        the plotting backend (name or Backend object, default is the default
        backend, see mcpl.plotting). Further keyword arguments are options for
        the backend (e.g. matplotlib_backend='agg'). Returns the list of
        created files when saving."""
        return _show_or_save([self.figure(logy = logy)],filename,backend,options)

    def to_text( self ):
        """Text table with the histogram contents."""
        labels = list(self.contents)
        lines = [ f'# histogram of: {self.expression}' ]
        if self.title:
            lines.append(f'# {self.title}')
        lines.append(f'# values: {self.ylabel}')
        cols = [ 'lower edge', 'upper edge' ] + [ str(lbl) if lbl is not None
                                                  else 'value' for lbl in labels ]
        lines.append('# ' + ' | '.join(cols))
        vals = [ self.values(lbl) for lbl in labels ]
        for i in range(len(self.edges)-1):
            lines.append(' '.join( f'{x:.8g}' for x in
                                   [ self.edges[i], self.edges[i+1] ]
                                   + [ v[i] for v in vals ] ))
        return '\n'.join(lines)

class Histogram2D:
    """2D histogram of the values of two expressions, created by the
    histogram2d() function. The contents (with shape (len(xedges)-1,
    len(yedges)-1)) are sums of weights, or numbers of particles if
    unweighted."""
    def __init__( self, xexpression, yexpression, xedges, yedges, weighted, title ):
        self.xexpression, self.yexpression = xexpression, yexpression
        self.xedges, self.yedges = xedges, yedges
        self.weighted = weighted
        self.title = title
        self.contents = np.zeros((len(xedges)-1,len(yedges)-1))

    def panel( self, logz = True ):
        """Panel (see mcpl.plotting) with the histogram."""
        p = Panel( title = self.title, xlabel = self.xexpression,
                   ylabel = self.yexpression )
        p.add(Hist2D(self.xedges,self.yedges,self.contents,logz = logz))
        return p

    def figure( self, logz = True ):
        """Figure (see mcpl.plotting) with the histogram."""
        return Figure( panels = [ self.panel(logz = logz) ] )

    def plot( self, filename = None, backend = None, logz = True, **options ):
        """Show the histogram (or save it in a file if filename is given) with
        the plotting backend (see Histogram.plot)."""
        return _show_or_save([self.figure(logz = logz)],filename,backend,options)

    def to_text( self ):
        lines = [ f'# 2D histogram of: {self.xexpression} : {self.yexpression}',
                  f'# values: {"weights" if self.weighted else "particles"} per bin',
                  '# x lower edge | x upper edge | y lower edge | y upper edge | value' ]
        for i in range(len(self.xedges)-1):
            for j in range(len(self.yedges)-1):
                lines.append(' '.join( f'{x:.8g}' for x in
                                       ( self.xedges[i], self.xedges[i+1],
                                         self.yedges[j], self.yedges[j+1],
                                         self.contents[i,j] ) ))
        return '\n'.join(lines)

def _show_or_save( figures, filename, backend, options ):
    if filename:
        return save(figures,filename,backend=backend,**options)
    show(figures,backend=backend,**options)
    return None

def _find_range( files, flt, vals, logx ):
    lo, hi = np.inf, -np.inf
    for _,src in files:
        for b in _blocks(src,flt):
            v = np.asarray(vals(b),dtype=float)
            v = v[np.isfinite(v)]
            if logx:
                v = v[v>0]
            if len(v):
                lo, hi = min(lo,v.min()), max(hi,v.max())
    if not lo <= hi:
        return None
    if lo == hi:
        return ( lo/2, lo*2 ) if logx else ( lo - 1.0, hi + 1.0 )
    return lo, hi

def _make_edges( rng, bins, logx ):
    lo, hi = rng
    if logx:
        if not lo > 0:
            raise MCPLError('Logarithmic binning requires a positive range')
        return np.geomspace(lo,hi,bins+1)
    return np.linspace(lo,hi,bins+1)

def histogram( files, expression, select = None, bins = 100, range = None,
               logx = False, weighted = True, split = None, lethargy = False,
               max_curves = 8 ):
    """Histogram of the values of an expression (see ParticleValue) for the
    particles in one or more files. Values with units must be divided by a
    unit, e.g. "ekin/MeV". For instance:

       h = mcpl.histogram( "myfile.mcpl", "ekin/eV", select = "pdgcode == neutron",
                           logx = True, lethargy = True )
       h.plot()

    Particles can be selected with the select expression (see
    ParticleFilter). The number of bins and their range (a tuple (low,high))
    can be given, otherwise the range covers all values. With logx, the bins
    are logarithmic. Unless weighted is False, the histogram contains the sum
    of weights in each bin rather than the number of particles. With lethargy
    (which implies logx), the plotted values are divided by the bin widths in
    lethargy (ln(E2/E1)), as is common for energy spectra.

    With split (an expression), there is a separate curve for each value of
    the expression (for at most max_curves values, any others are combined
    into a curve labelled "other"), for instance split="pdgcode" gives a curve
    for each particle type, and split="x > 0cm" one for each half. With more
    than one file, there is a curve for each file.
    """
    files = _as_files(files)
    flt = _as(ParticleFilter,select)
    vals = _as(ParticleValue,expression)
    spl = _SplitValue(split) if split is not None else None
    if lethargy:
        logx = True
    if range is None:
        range = _find_range(files,flt,vals,logx)
        if range is None:
            raise MCPLError('No values to histogram (no particles selected?)')
    edges = _make_edges(range,int(bins),logx)
    title = f'selection: {flt.expression}' if flt is not None else None
    h = Histogram(vals.expression,edges,logx,weighted,lethargy,title)
    acc = {}#(file label,split key) -> [contents,sumw2,underflow,overflow]
    for flabel,src in files:
        for b in _blocks(src,flt):
            v = np.asarray(vals(b),dtype=float)
            w = b.weight if weighted else np.ones(len(v))
            if spl is not None:
                sv = np.asarray(spl(b),dtype=float)
                if spl._is_bool is None and len(sv):
                    spl._is_bool = bool(np.all((sv==0)|(sv==1)))
                keys = np.unique(sv)
                if len(keys) > 1000:
                    raise MCPLError(f'Split expression "{spl.expression}" has'
                                    ' too many different values')
            else:
                sv, keys = None, [ None ]
            for k in keys:
                m = slice(None) if k is None else ( sv == k )
                vk, wk = v[m], w[m]
                a = acc.setdefault((flabel,k),[np.zeros(len(edges)-1),
                                                np.zeros(len(edges)-1),0.0,0.0])
                a[0] += np.histogram(vk,bins=edges,weights=wk)[0]
                a[1] += np.histogram(vk,bins=edges,weights=wk*wk)[0]
                a[2] += float(wk[vk<edges[0]].sum())
                a[3] += float(wk[vk>edges[-1]].sum())
    #Order curves by total weight (per file), and combine the smallest ones:
    multifile = len(files) > 1
    for flabel,_ in files:
        keys = sorted( ( k for (fl,k) in acc if fl == flabel ),
                       key = lambda k : ( -acc[(flabel,k)][0].sum(), str(k) ) )
        if not keys:
            keys = [ None ]
            acc[(flabel,None)] = [np.zeros(len(edges)-1),np.zeros(len(edges)-1),0.0,0.0]
        shown, rest = keys[:max_curves], keys[max_curves:]
        if rest:
            shown = keys[:max_curves-1]
            rest = keys[max_curves-1:]
        for k in shown + ( ['other'] if rest else [] ):
            if k == 'other':
                parts = [ acc[(flabel,r)] for r in rest ]
                a = [ sum(p[i] for p in parts) for i in (0,1,2,3) ]
                lbl = 'other'
            else:
                a = acc[(flabel,k)]
                lbl = _split_label(spl,k)
            if multifile:
                lbl = flabel if lbl is None else f'{flabel}: {lbl}'
            h.contents[lbl], h.sumw2[lbl] = a[0], a[1]
            h.underflow[lbl], h.overflow[lbl] = a[2], a[3]
    return h

def histogram2d( files, xexpression, yexpression, select = None, bins = 100,
                 xrange = None, yrange = None, weighted = True ):
    """2D histogram of the values of two expressions (see histogram()) for the
    particles in one or more files, for instance:

       mcpl.histogram2d( "myfile.mcpl", "x/cm", "y/cm" ).plot()
    """
    files = _as_files(files)
    flt = _as(ParticleFilter,select)
    xv, yv = _as(ParticleValue,xexpression), _as(ParticleValue,yexpression)
    if xrange is None:
        xrange = _find_range(files,flt,xv,False)
    if yrange is None:
        yrange = _find_range(files,flt,yv,False)
    if xrange is None or yrange is None:
        raise MCPLError('No values to histogram (no particles selected?)')
    xe, ye = _make_edges(xrange,int(bins),False), _make_edges(yrange,int(bins),False)
    title = f'selection: {flt.expression}' if flt is not None else None
    h = Histogram2D(xv.expression,yv.expression,xe,ye,weighted,title)
    for _,src in files:
        for b in _blocks(src,flt):
            w = b.weight if weighted else None
            h.contents += np.histogram2d(np.asarray(xv(b),dtype=float),
                                         np.asarray(yv(b),dtype=float),
                                         bins=(xe,ye),weights=w)[0]
    return h

def plot_histograms( histograms, filename = None, backend = None, logy = False,
                     overlay = False, labels = None, **options ):
    """Show histograms (or save them in a file if filename is given) with the
    plotting backend and options (see Histogram.plot). Each histogram is shown in a separate
    figure (e.g. on separate pages of a PDF file), or with overlay=True, all the
    (1D) histograms are drawn in the same plot with a legend, for instance to
    compare histograms of the same expression from different simulations. The
    legend shows the labels if given, and otherwise the titles (selections) or
    expressions of the histograms. Returns the list of created files when
    saving."""
    histograms = list(histograms)
    if not overlay:
        figs = []
        for h in histograms:
            figs.append( h.figure(logy = logy) if isinstance(h,Histogram)
                         else h.figure() )
        return _show_or_save(figs,filename,backend,options)
    if not histograms:
        raise MCPLError('No histograms to plot')
    if not all( isinstance(h,Histogram) for h in histograms ):
        raise MCPLError('Only 1D histograms can be overlaid')
    if labels is not None and len(labels) != len(histograms):
        raise MCPLError('The number of labels must be the number of histograms')
    first = histograms[0]
    exprs = sorted({ h.expression for h in histograms })
    p = Panel( xlabel = ', '.join(exprs), ylabel = first.ylabel,
               logx = first.logx, logy = logy,
               xlim = ( min( h.edges[0] for h in histograms ),
                        max( h.edges[-1] for h in histograms ) ) )
    color = 0
    for i,h in enumerate(histograms):
        name = labels[i] if labels is not None else ( h.title or h.expression )
        for curve in h.contents:
            label = name if curve is None else f'{name}: {curve}'
            p.add(StepHist(h.edges,h.values(curve),label = label,color = color))
            color += 1
    return _show_or_save([Figure(panels = [p])],filename,backend,options)
