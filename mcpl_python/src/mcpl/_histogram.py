
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


def _is_file( s ):
    """Whether s is an opened file (an MCPLFile, or a view of one)"""
    return hasattr(s,'particle_blocks') and hasattr(s,'_filename')

def _as_files( sources ):
    """List of (label,source) for a file or a list of files"""
    if isinstance(sources,(str,bytes,os.PathLike)) or _is_file(sources):
        sources = [ sources ]
    res = []
    for s in sources:
        name = s._filename if _is_file(s) else s
        res.append( (os.path.basename(os.fsdecode(name)),s) )
    if not res:
        raise MCPLError('No files given')
    return res

def _blocks( source, flt ):
    """Iterate over (picked) particle blocks in a file"""
    f = source if _is_file(source) else MCPLFile(source)
    for b in f.particle_blocks:
        yield b[flt(b)] if flt is not None else b

#Options of histogram strings ("EXPR;logx;bins=50"), with whether they take a
#value:
_hist_options = { 'bins' : True, 'range' : True, 'xrange' : True,
                  'yrange' : True, 'logx' : False, 'logy' : False,
                  'lethargy' : False, 'split' : True, 'unweighted' : False,
                  'print' : False }

def _parse_hist( text ):
    """Parse a histogram string: an expression (or two separated by ":" for 2D
    histograms), followed by options separated by ";", like
    "ekin/MeV;logx;bins=50" or "x/cm : y/cm;xrange=-10:10". Returns a
    dict with the expressions (a list of one or two), and the options (with
    defaults for those not given)."""
    from ._expressions import _check_chars
    _check_chars(text,'histogram')
    parts = [ e.strip() for e in text.split(';') ]
    exprs = [ e.strip() for e in parts[0].split(':') ]
    if len(exprs) > 2 or not all(exprs):
        raise MCPLError(f'Histograms are of an expression, or two expressions'
                        f' separated by ":" for 2D histograms, in "{text}"')
    res = { 'exprs' : exprs, 'bins' : None, 'range' : None, 'xrange' : None,
            'yrange' : None, 'logx' : False,
            'logy' : False, 'lethargy' : False, 'split' : None,
            'unweighted' : False, 'print' : False }
    seen = set()
    for opt in parts[1:]:
        if not opt:
            continue
        name, eq, value = ( e.strip() for e in opt.partition('=') )
        if name not in _hist_options:
            raise MCPLError(f'Unknown histogram option "{name}" in "{text}"'
                            ' (the options are: ' + ', '.join(_hist_options) + ')')
        if name in seen:
            raise MCPLError(f'Histogram option "{name}" given more than once'
                            f' in "{text}"')
        seen.add(name)
        if _hist_options[name] and not ( eq and value ):
            raise MCPLError(f'Histogram option "{name}" needs a value (like'
                            f' {name}=...) in "{text}"')
        if not _hist_options[name] and eq:
            raise MCPLError(f'Histogram option "{name}" takes no value in "{text}"')
        if name == 'bins':
            nb = [ e.strip() for e in value.split(',') ]
            if ( len(nb) > len(exprs) or not all( e.isdigit() and int(e) > 0
                                                  for e in nb ) ):
                raise MCPLError(f'bins must be a positive integer (or two'
                                f' for 2D histograms, like bins=50,40) in "{text}"')
            res['bins'] = int(nb[0]) if len(nb) == 1 else tuple( int(e) for e in nb )
        elif name in ('range','xrange','yrange'):
            if ( name == 'range' ) != ( len(exprs) == 1 ):
                use = 'range' if len(exprs) == 1 else 'xrange and yrange'
                raise MCPLError(f'Histogram option "{name}" can only be used for'
                                f' {"2D" if len(exprs) == 1 else "1D"} histograms'
                                f' (use {use}), in "{text}"')
            try:
                lo, hi = ( float(e) for e in value.split(':') )
            except ValueError:
                lo = hi = None
            if lo is None or not lo < hi:
                raise MCPLError(f'{name} must be given as {name}=LOW:HIGH, with'
                                ' numbers in the units of the expression, in'
                                f' "{text}"')
            res[name] = (lo,hi)
        elif name == 'split':
            res['split'] = value
        else:
            res[name] = True
    if len(exprs) == 2:
        for name in ('logx','logy','lethargy','split'):
            if res[name]:
                raise MCPLError(f'Histogram option "{name}" can not be used'
                                f' for 2D histograms, in "{text}"')
    return res

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
        return split.expression if key else f'not ({split.expression})'
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
        self._logy = False
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
        """Label of the values (e.g. "weights per bin")"""
        what = 'weights' if self.weighted else 'particles'
        if self.lethargy:
            return f'{what} per unit lethargy'
        return f'{what} per bin'

    def panel( self, logy = False ):
        """Panel (see mcpl.plotting) with the histogram."""
        from .plotting import Panel, StepHist
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
        from .plotting import Figure
        return Figure( panels = [ self.panel(logy = logy) ] )

    def plot( self, filename = None, backend = None, logy = None,
              terminal = False, **options ):
        """Show the histogram (or save it in a file if filename is given) with
        the plotting backend (name or Backend object, default is chosen as
        described in mcpl.plotting, in the terminal if terminal is True). The
        y axis is logarithmic with logy=True (default is the logy option of the
        histogram expression, see histogram()). Further keyword arguments are
        options for the backend (e.g. matplotlib_backend='agg'). Returns the
        list of created files when saving."""
        if logy is None:
            logy = self._logy
        return _show_or_save([self.figure(logy = logy)],filename,backend,
                             options,terminal)

    def to_text( self ):
        """Text table with the histogram contents."""
        labels = list(self.contents)
        lines = [ f'# histogram of: {self.expression}' ]
        if self.title:
            lines += [ f'# {t}' for t in self.title.splitlines() ]
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
        from .plotting import Hist2D, Panel
        p = Panel( title = self.title, xlabel = self.xexpression,
                   ylabel = self.yexpression )
        p.add(Hist2D(self.xedges,self.yedges,self.contents,logz = logz))
        return p

    def figure( self, logz = True ):
        """Figure (see mcpl.plotting) with the histogram."""
        from .plotting import Figure
        return Figure( panels = [ self.panel(logz = logz) ] )

    def plot( self, filename = None, backend = None, logz = True,
              terminal = False, **options ):
        """Show the histogram (or save it in a file if filename is given) with
        the plotting backend (see Histogram.plot)."""
        return _show_or_save([self.figure(logz = logz)],filename,backend,
                             options,terminal)

    def to_text( self ):
        """Text table with the histogram contents."""
        lines = [ f'# 2D histogram of: {self.xexpression} : {self.yexpression}' ]
        if self.title:
            lines += [ f'# {t}' for t in self.title.splitlines() ]
        lines += [ f'# values: {"weights" if self.weighted else "particles"} per bin',
                   '# x lower edge | x upper edge | y lower edge | y upper edge | value' ]
        for i in range(len(self.xedges)-1):
            for j in range(len(self.yedges)-1):
                lines.append(' '.join( f'{x:.8g}' for x in
                                       ( self.xedges[i], self.xedges[i+1],
                                         self.yedges[j], self.yedges[j+1],
                                         self.contents[i,j] ) ))
        return '\n'.join(lines)

def _show_or_save( figures, filename, backend, options, terminal = False ):
    from .plotting import save, show
    if filename:
        return save(figures,filename,backend=backend,**options)
    show(figures,backend=backend,terminal=terminal,**options)
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

def _nice_nbins( maxbins ):
    """A number of bins which is at most maxbins and has many divisors (the
    largest number of divisors among the numbers of the form 2^a*3^b*5^c
    between 85% of maxbins and maxbins), so a histogram with that many bins
    can later be merged into fewer bins in many ways. Below 10 bins, maxbins
    itself is returned."""
    maxbins = int(maxbins)
    if maxbins < 10:
        return max(1,maxbins)
    best = None
    for a in _range(0,8):
        for b in _range(0,6):
            for c in _range(0,5):
                n = 2**a * 3**b * 5**c
                if 0.85 * maxbins < n <= maxbins:
                    ndiv = (a+1)*(b+1)*(c+1)
                    if best is None or (ndiv,n) > best:
                        best = (ndiv,n)
    return best[1] if best else maxbins

def _auto_nbins( neff, nbins, ndim = 1 ):
    """Number of bins for showing a histogram made with nbins bins of data with
    an effective number of entries neff: the square-root rule (per axis for
    ndim=2), clamped to [10,400], and then the closest divisor of nbins (in
    log distance, so the bins can be merged exactly)."""
    import math
    target = max( 1.0, neff ) ** ( 0.5 / ndim )
    target = max( 10, min( 400, round(target) ) )
    divs = [ d for d in _range(1,nbins+1) if nbins % d == 0 ]
    return min( divs, key = lambda d : abs(math.log(d/target)) )

def _neff( sumw, sumw2 ):
    """Effective number of entries (sum of weights squared over sum of squared
    weights, which is the number of entries for unit weights)"""
    return sumw * sumw / sumw2 if sumw2 > 0.0 else 0.0

_range = range#(the name range is shadowed by arguments below)

def histogram( files, expression, pick = None, bins = 'auto', range = None,
               logx = False, unweighted = False, split = None, lethargy = False,
               max_curves = 8, _maxbins = None ):
    """Histogram of the values of an expression (see ParticleValue) for the
    particles in one or more files. Values with units must be divided by a
    unit, e.g. "ekin/MeV". For instance:

       h = mcpl.histogram( "myfile.mcpl", "ekin/eV",
                           pick = "pdgcode == neutron",
                           logx = True, lethargy = True )
       h.plot()

    Particles can be picked with the pick expression (see
    ParticleFilter). The number of bins and their range (a tuple (low,high))
    can be given, otherwise the range covers all values, and the number of
    bins is chosen from the effective number of entries N (the square root
    of N, between 10 and 400; the data is histogrammed once with many bins,
    which are then merged). With logx, the bins are logarithmic. The
    histogram contains the sum of weights in each bin, or the number of
    particles if unweighted is True. With lethargy (which implies logx), the
    plotted values are divided by the bin widths in lethargy (ln(E2/E1)), as
    is common for energy spectra.

    With split (an expression), there is a separate curve for each value of
    the expression (for at most max_curves values, any others are combined
    into a curve labelled "other"), for instance split="pdgcode" gives a curve
    for each particle type, and split="x > 0cm" one for each half. With more
    than one file, there is a curve for each file.

    The options can also be given after the expression, separated by ";", as
    in the histogram strings of "mcpltool -H" (see "mcpltool -H help"), e.g.
    "ekin/eV;logx;lethargy;bins=50;range=1e-3:1e7;split=pdgcode;unweighted;logy"
    (logy is used when plotting the histogram). With two expressions
    separated by ":", e.g. "x/cm : y/cm;xrange=-10:10;yrange=-5:5", the
    result is a 2D histogram (see histogram2d()).
    """
    logy = False
    if isinstance(expression,str) and ( ';' in expression or ':' in expression ):
        o = _parse_hist(expression)
        given = { 'bins' : bins != 'auto', 'range' : range is not None,
                  'logx' : logx, 'unweighted' : unweighted, 'split' : split
                  is not None, 'lethargy' : lethargy }
        for name, g in given.items():
            if g and o[name] not in ( None, False ):
                raise MCPLError(f'The histogram option {name} can not be given'
                                ' both as an argument and in the expression'
                                f' "{expression}"')
        if o['print']:
            raise MCPLError('The histogram option print is only for the mcpltool'
                            ' command (use the to_text() method of the histogram'
                            ' instead)')
        unweighted = unweighted or o['unweighted']
        if len(o['exprs']) == 2:
            h = histogram2d( files, o['exprs'][0], o['exprs'][1], pick = pick,
                             bins = o['bins'] or bins, xrange = o['xrange'],
                             yrange = o['yrange'], unweighted = unweighted,
                             _maxbins = _maxbins )
            return h
        expression = o['exprs'][0]
        bins = o['bins'] or bins
        range = o['range'] if o['range'] else range
        logx = logx or o['logx']
        lethargy = lethargy or o['lethargy']
        split = o['split'] if o['split'] is not None else split
        logy = o['logy']
    files = _as_files(files)
    flt = _as(ParticleFilter,pick)
    vals = _as(ParticleValue,expression)
    spl = _SplitValue(split) if split is not None else None
    if lethargy:
        logx = True
    weighted = not unweighted
    if range is None:
        range = _find_range(files,flt,vals,logx)
        if range is None:
            raise MCPLError('No values to histogram (no particles picked?)')
    auto = ( bins == 'auto' )
    nbins = _nice_nbins(_maxbins or 1200) if auto else int(bins)
    edges = _make_edges(range,nbins,logx)
    title = f'pick: {flt.expression}' if flt is not None else None
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
    #With automatic binning, merge the bins according to the effective number
    #of entries:
    k = 1
    if auto:
        sumw = sum( a[0].sum() for a in acc.values() )
        sumw2 = sum( a[1].sum() for a in acc.values() )
        k = nbins // _auto_nbins(_neff(sumw,sumw2),nbins)
        if k > 1:
            edges = edges[::k]
            for a in acc.values():
                a[0] = a[0].reshape(-1,k).sum(axis=1)
                a[1] = a[1].reshape(-1,k).sum(axis=1)
    h = Histogram(vals.expression,edges,logx,weighted,lethargy,title)
    h._logy = logy
    #(number of columns needed to draw the bins exactly, see mcpltool):
    h._display_bins = nbins if auto else None
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

def histogram2d( files, xexpression, yexpression, pick = None, bins = 'auto',
                 xrange = None, yrange = None, unweighted = False,
                 _maxbins = None ):
    """2D histogram of the values of two expressions (see histogram()) for the
    particles in one or more files, for instance:

       h = mcpl.histogram2d( "myfile.mcpl",
                             "x/cm", "y/cm" )
       h.plot()

    The number of bins can be given for both axes, or as a tuple (nx,ny), and
    is otherwise chosen from the effective number of entries N (the fourth
    root of N per axis, between 10 and 400). The ranges of the axes can be
    given as tuples (low,high) with xrange and yrange, otherwise they cover
    all values. The histogram contains the sum of weights in each bin, or the
    number of particles if unweighted is True.
    """
    weighted = not unweighted
    files = _as_files(files)
    flt = _as(ParticleFilter,pick)
    xv, yv = _as(ParticleValue,xexpression), _as(ParticleValue,yexpression)
    if xrange is None:
        xrange = _find_range(files,flt,xv,False)
    if yrange is None:
        yrange = _find_range(files,flt,yv,False)
    if xrange is None or yrange is None:
        raise MCPLError('No values to histogram (no particles picked?)')
    auto = ( isinstance(bins,str) and bins == 'auto' )
    if auto:
        mx, my = _maxbins if _maxbins else ( 400, 400 )
        bx, by = _nice_nbins(mx), _nice_nbins(my)
    else:
        bx, by = bins if isinstance(bins,(tuple,list)) else ( bins, bins )
        bx, by = int(bx), int(by)
    xe, ye = _make_edges(xrange,bx,False), _make_edges(yrange,by,False)
    title = f'pick: {flt.expression}' if flt is not None else None
    contents = np.zeros((bx,by))
    sumw, sumw2 = 0.0, 0.0
    for _,src in files:
        for b in _blocks(src,flt):
            w = b.weight if weighted else None
            x, y = np.asarray(xv(b),dtype=float), np.asarray(yv(b),dtype=float)
            contents += np.histogram2d(x,y,bins=(xe,ye),weights=w)[0]
            inside = ( x >= xe[0] ) & ( x <= xe[-1] ) & ( y >= ye[0] ) & ( y <= ye[-1] )
            wi = np.ones(len(x))[inside] if w is None else np.asarray(w)[inside]
            sumw += float(wi.sum())
            sumw2 += float((wi*wi).sum())
    if auto:
        neff = _neff(sumw,sumw2)
        kx, ky = bx // _auto_nbins(neff,bx,2), by // _auto_nbins(neff,by,2)
        if kx > 1 or ky > 1:
            xe, ye = xe[::kx], ye[::ky]
            contents = contents.reshape(bx//kx,kx,by//ky,ky).sum(axis=(1,3))
    h = Histogram2D(xv.expression,yv.expression,xe,ye,weighted,title)
    h.contents += contents
    h._display_bins = ( bx, by ) if auto else None
    return h

def plot_histograms( histograms, filename = None, backend = None, logy = False,
                     overlay = False, labels = None, **options ):
    """Show histograms (or save them in a file if filename is given) with the
    plotting backend and options (see Histogram.plot). Each histogram is
    shown in a separate figure (e.g. on separate pages of a PDF file), or
    with overlay=True, all the (1D) histograms are drawn in the same plot
    with a legend, for instance to compare histograms of the same expression
    from different simulations. The legend shows the labels if given, and otherwise the titles (picks) or
    expressions of the histograms. Returns the list of created files when
    saving."""
    from .plotting import Figure, Panel, StepHist
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
