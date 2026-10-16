
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

"""The --stats and --hist modes of mcpltool, separate from _cli so that the
other modes do not load the code for statistics, histograms and plots."""

__all__ = []

import os

from ._common import MCPLError
from ._reader import MCPLFile


def mcpltool_stats(filename,opt_select,opt_pdf,opt_gui,vopts,bad):
    from ._stats import _SelectedFile, dump_stats
    f=MCPLFile(filename)
    if f.nparticles==0:
        bad("Can not calculate statistics for an empty file")
    if opt_select is not None:
        f = _SelectedFile(f,opt_select)
        if f.nparticles==0:
            bad("Can not calculate statistics when no particles are selected")
    outfn = vopts.get('--output') or ( 'mcpl.pdf' if opt_pdf else None )
    if outfn or opt_gui or '--backend' in vopts:
        from ._statsplot import plot_stats
        try:
            files = plot_stats(f,filename=outfn,backend=vopts.get('--backend'),
                               **_save_options(outfn,vopts.get('--backend')))
        except MCPLError as e:
            bad(str(e))
        if files:
            print('Created ' + ', '.join(files))
    else:
        dump_stats(f)

def mcpltool_hist(filelist,expr,select,vopts,hflags,bad):
    from ._histogram import histogram, histogram2d
    if not filelist:
        bad("No input file specified")
    bins = vopts.get('--bins')
    if bins is not None and ( not bins.isdigit() or not int(bins) > 0 ):
        bad("--bins must be a positive integer")
    exprs = expr.split(' : ')
    outfn = vopts.get('--output')
    #Unless the number of bins is given, it is chosen automatically, with at
    #most the resolution of the plot (if the backend has one, like the text
    #backends, whose plots are then fitted to the bins):
    backend, maxbins = None, None
    if bins is not None:
        bins = int(bins)
    else:
        bins = 'auto'
        if '--print' not in hflags:
            from ._plotbackend import _create_backend
            try:
                backend = _create_backend(vopts.get('--backend'),
                                          **_save_options(outfn,vopts.get('--backend')))
            except MCPLError as e:
                bad(str(e))
            res = backend.resolution()
            if res is not None:
                maxbins = tuple(res) if len(exprs) == 2 else res[0]
    rngs = [ None, None ]
    if '--range' in vopts:
        parts = vopts['--range'].split(',')
        if len(parts) > len(exprs):
            parts = []
        for i,r in enumerate(parts):
            try:
                lo, hi = ( float(e) for e in r.split(':') )
            except ValueError:
                lo, hi = None, None
            if lo is None or not lo < hi:
                parts = []
                break
            rngs[i] = ( lo, hi )
        if not parts:
            bad("--range must be given as LOW:HIGH (or XLOW:XHIGH,YLOW:YHIGH for 2D"
                " histograms), with numbers in the units of the expression")
    rng = rngs[0]
    if len(exprs) > 2 or not all(e.strip() for e in exprs):
        bad('--hist takes an expression, or two expressions separated by'
            ' " : " (with spaces) for 2D histograms')
    try:
        if len(exprs) == 2:
            for o in ('--logx','--lethargy'):
                if o in hflags:
                    bad(f"{o} can not be used with 2D histograms")
            if '--split' in vopts:
                bad("--split can not be used with 2D histograms")
            h = histogram2d(filelist,exprs[0].strip(),exprs[1].strip(),
                            select=select,bins=bins,xrange=rng,yrange=rngs[1],
                            weighted='--unweighted' not in hflags,
                            _maxbins=maxbins)
        else:
            h = histogram(filelist,expr,select=select,bins=bins,range=rng,
                          _maxbins=maxbins,
                          logx='--logx' in hflags,
                          weighted='--unweighted' not in hflags,
                          split=vopts.get('--split'),
                          lethargy='--lethargy' in hflags)
    except MCPLError as e:
        bad(str(e))
    if '--print' in hflags:
        print(h.to_text())
        return
    if outfn and os.path.exists(outfn):
        bad("Requested output file already exists.")
    kw = {} if len(exprs) == 2 else { 'logy' : '--logy' in hflags }
    try:
        if backend is not None:
            if maxbins is not None and hasattr(backend,'_fit_resolution'):
                #(draw the bins exactly, with a whole number of columns each):
                backend._fit_resolution(h._display_bins)
            files = h.plot(filename=outfn,backend=backend,**kw)
        else:
            files = h.plot(filename=outfn,backend=vopts.get('--backend'),**kw,
                           **_save_options(outfn,vopts.get('--backend')))
    except MCPLError as e:
        bad(str(e))
    if files:
        print('Created ' + ', '.join(files))


def _save_options(outfn, backend):
    """Options for the plotting backend: when saving files with matplotlib, its
    agg backend is used (which does not need a display)."""
    from ._plotbackend import _backend_name
    if outfn and _backend_name(backend) == 'matplotlib':
        return { 'matplotlib_backend' : 'agg' }
    return {}

