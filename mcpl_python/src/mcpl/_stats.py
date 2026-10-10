
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

"""Statistics of the particles in MCPL files."""

__all__ = ['collect_stats', 'dump_stats', 'plot_stats']

import os

from ._common import MCPLError
from ._expressions import _as_filter
from ._messages import _warning
from ._numpy import _np_add_at, np, np_dtype, np_unique
from ._physics import _pdg_database
from ._reader import MCPLFile
from .plotting import Bars, Figure, Panel, StepHist, save, show


class _SelectedFile:
    """Read-only view of the particles in an MCPLFile selected by an
    expression (or ParticleFilter), for collect_stats. Also used for files
    opened with select or edit (in which case select can be None)."""
    def __init__(self,mcplfile,select):
        self._f = mcplfile
        self._flt = _as_filter(select)
        sels = [ e.expression for e in (getattr(mcplfile,'select',None),self._flt)
                 if e is not None ]
        self.selection = ' && '.join( f'({e})' if len(sels) > 1 else e for e in sels )
        if getattr(mcplfile,'edit',None) is not None:
            self.edit = mcplfile.edit.expression
        self.nparticles = sum( len(b) for b in self.particle_blocks )
    def __getattr__(self,name):
        return getattr(self._f,name)
    @property
    def particle_blocks(self):
        for b in self._f.particle_blocks:
            yield b[self._flt(b)] if self._flt is not None else b

def _unique_count(a,weights=None):
    """returns (unique,count) where unique is an array of sorted unique values in a, and count is the corresponding frequency counts"""
    unique, inverse = np_unique(a, return_inverse=True)
    count = np.zeros(len(unique), int if weights is None else np_dtype(type(weights[0])))
    _np_add_at(count, inverse, 1 if weights is None else weights)
    return (unique, count)

def _merge_unique_count(uc1,uc2):
    """merges the results of calling _unique_count on two separate data sets"""
    u = np.append(uc1[0],uc2[0])
    c = np.append(uc1[1],uc2[1])
    restype=(uc1[1][0] if len(uc1[1]) else 0) +(uc2[1][0] if len(uc2[1]) else 0)
    unique, inverse = np_unique(u, return_inverse=True)
    count = np.zeros(len(unique), np_dtype(type(restype)))
    _np_add_at(count, inverse, c)
    return (unique,count)

class _StatCollector:
    def __init__(self):
        #For numerical stability also when mean>>rms, rms state is calculated by
        #accumulation in T variable (as in "SimpleHists" by T. Kittelmann, 2014).
        #Here the variable T is stored in self.__rmsstate.
        self.clear()
        self.__dumporder = ['min','max','mean','rms','integral']
        self.__statcalc = { 'rms'      : (lambda : np.sqrt(self.__rmsstate/self.__sumw) if self.__sumw else None ),
                            'mean'     : (lambda : (self.__sumwx/self.__sumw) if self.__sumw else None ),
                            'min'      : (lambda : self.__min ),
                            'max'      : (lambda : self.__max ),
                            'integral' : (lambda : self.__sumw )
        }
        assert sorted(self.__dumporder)==sorted(self.__statcalc.keys())

    def clear(self):
        self.__sumw,self.__sumwx,self.__rmsstate = 0.0,0.0,0.0
        self.__min,self.__max = None,None

    def add_data(self,a,w = None):
        amin,amax = a.min(),a.max()
        assert w is None or len(w)==len(a)
        assert not np.isnan(amin),"input array has NaN's!"
        self.__min = min(amin,amin if self.__min is None else self.__min)
        self.__max = max(amax,amax if self.__max is None else self.__max)
        new_sumw = float(len(a)) if w is None else w.sum()
        if not new_sumw:
            return
        new_sumwx = a.sum() if w is None else (a*w).sum()
        a_shifted = a - new_sumwx/new_sumw#shift to mean for numerical stability
        sumwx_shifted = a_shifted.sum() if w is None else (a_shifted*w).sum()
        sumwxx_shifted = (a_shifted**2).sum() if w is None else ((a_shifted**2)*w).sum()
        new_T = sumwxx_shifted - sumwx_shifted**2/new_sumw
        if not self.__sumw:
            self.__rmsstate = new_T
        else:
            w1,w2 = self.__sumw,new_sumw
            self.__rmsstate += new_T + (w2*self.__sumwx-w1*new_sumwx)**2/(w1*w2*(w1+w2))
        self.__sumw  += new_sumw
        self.__sumwx += new_sumwx

    def dump(self):
        for k in self.__dumporder:
            print("{} : {}".format(k.ljust(8),f'{self.__statcalc[k]():g}' if self.__sumw>0.0 or k=='integral' else 'n/a'))

    def summarise(self):
        return ', '.join("{}={}".format(k,f'{self.__statcalc[k]():g}' if self.__sumw>0.0 or k=='integral' else 'n/a') for k in self.__dumporder)

    def __getitem__(self,a):
        return self.__statcalc[a]()

    def as_dict(self):
        return {k: self.__statcalc[k]() for k in self.__statcalc}

_possible_std_stats = ['ekin','x','y','z','ux','uy','uz','time','weight','polx','poly','polz']
_possible_freq_stats = ['pdgcode','userflags']

def collect_stats(mcplfile,stats='all',bin_data=True,select=None):
    """Efficiently collect statistics from an entire file. Returns dictionary
    with stat names as key and the collected statistics as values. If select
    is given (an expression or a ParticleFilter), only the selected particles
    are included."""

    #Normal stats (will be used weighted, except for stats about the weight field itself):
    possible_std_stats = set(_possible_std_stats)
    #Stats for which distributions are less likely to be relevant, so unique
    #values and their frequency will be returned instead:
    possible_freq_stats = set(_possible_freq_stats)

    if stats=='all':
        stats = possible_std_stats.union(possible_freq_stats)

    if not isinstance(stats,set):
        stats = set(stats)

    if not isinstance(mcplfile,(MCPLFile,_SelectedFile)):
        mcplfile = MCPLFile(mcplfile)
    if select is not None or ( isinstance(mcplfile,MCPLFile) and (
            mcplfile.select is not None or mcplfile.edit is not None ) ):
        mcplfile = _SelectedFile(mcplfile,select)
    if mcplfile.nparticles==0:
        _warning("Can not calculate stats on an empty file"
                 if select is None else
                 "Can not calculate stats when no particles are selected")
        return {}

    unknown = stats.difference(possible_std_stats.union(possible_freq_stats))
    if unknown:
        raise MCPLError('Unknown stat names requested: "{}"'.format('","'.join(unknown)))

    #Some stats might be constant for all particles in the file:
    constant_stats_available = set()
    if mcplfile.opt_universalpdgcode:
        constant_stats_available.add('pdgcode')
    if not mcplfile.opt_userflags:
        constant_stats_available.add('userflags')
    if mcplfile.opt_universalweight:
        constant_stats_available.add('weight')
    if not mcplfile.opt_polarisation:
        constant_stats_available |= {'polx','poly','polz'}
    cnst_stats = constant_stats_available.intersection(stats)
    stats = stats.difference(cnst_stats)

    std_stats = sorted(stats.difference(constant_stats_available).intersection(possible_std_stats))
    freq_stats = sorted(stats.difference(constant_stats_available).intersection(possible_freq_stats))

    if not std_stats and not freq_stats and not cnst_stats:
        raise MCPLError('No stats requested')

    weight_sum = mcplfile.nparticles * mcplfile.opt_universalweight if mcplfile.opt_universalweight else None

    nbins = 100 if mcplfile.nparticles < 1000 else 200

    if nbins%2==0:
        nbins += 1#ensure nbins is odd (makes some stuff below easier)

    collected_stats={}
    if std_stats:
        #Unfortunately we need a pass-through in order to collect
        #statistics for histogram ranges:
        for s in std_stats:
            collected_stats[s] = _StatCollector()
        for pb in mcplfile.particle_blocks:
            vals_weight=pb.weight
            for s,sc in collected_stats.items():
                if s=='weight':
                    sc.add_data(vals_weight)
                else:
                    sc.add_data(getattr(pb,s),vals_weight)
    ranges={}
    for s,sc in collected_stats.items():
        if weight_sum is None and s!='weight':
            weight_sum = sc['integral']
        ranges[s] = [max(sc['min'],sc['mean']-2*sc['rms']),
                     min(sc['max'],sc['mean']+2*sc['rms'])]
        if not ranges[s][0]<ranges[s][1]:
            ranges[s] = (ranges[s][0]-1.0,ranges[s][1]+1.0)

    hists={}
    freq_uc={s: (np.asarray([],dtype=int),np.asarray([],dtype=float)) for s in freq_stats}
    if (std_stats and bin_data) or freq_stats:
        #pass through and collect data:
        if weight_sum is None:
            sumw = 0.0
        for pb in mcplfile.particle_blocks:
            vals_weight = pb.weight
            disable=[]
            for s in freq_stats:
                uc_block = _unique_count(getattr(pb,s),vals_weight)
                freq_uc[s] = _merge_unique_count(freq_uc[s],uc_block)
                if len(freq_uc[s][0])>10000:
                    _warning(f"Too many unique values in {s} field. Disabling {s} statistics")
                    disable+=[s]
            for s in disable:
                del freq_uc[s]
                freq_stats.remove(s)
            for s in (std_stats if bin_data else []):
                vals = getattr(pb,s) if s!='weight' else vals_weight
                h,bins = np.histogram(vals, bins=nbins, range=ranges[s],
                                      weights=(None if s=='weight' else vals_weight))
                if s in hists:
                    hists[s][0] += h
                else:
                    hists[s] = [ h, bins ]
            if weight_sum is None:
                sumw += pb.weight.sum()
        if weight_sum is None:
            weight_sum = sumw

    if weight_sum is None:
        #apparently we need a run-through for the sole purpose of calculating this...
        assert not std_stats and not freq_stats
        weight_sum = 0.0
        for pb in mcplfile.particle_blocks:
            weight_sum += pb.weight.sum()

    assert weight_sum is not None

    if cnst_stats:
        if 'pdgcode' in cnst_stats:
            assert mcplfile.opt_universalpdgcode
            cnst_stats.remove('pdgcode')
            freq_uc['pdgcode'] = (np.asarray([mcplfile.opt_universalpdgcode]),np.asarray([weight_sum]))
        if 'userflags' in cnst_stats:
            assert not mcplfile.opt_userflags
            cnst_stats.remove('userflags')
            freq_uc['userflags'] = (np.asarray([0]),np.asarray([weight_sum]))
        if 'weight' in cnst_stats:
            uw=mcplfile.opt_universalweight
            assert uw
            cnst_stats.remove('weight')
            sc=_StatCollector()
            sc.add_data(np.asarray([uw],float),np.asarray([mcplfile.nparticles],float))
            collected_stats['weight']=sc
            if bin_data:
                bins = np.linspace(0.0,2.0*uw,nbins+1)
                h = np.zeros(nbins)
                assert nbins % 2 != 0#nbins is odd, value falls at bin center below:
                h[nbins//2] = uw * mcplfile.nparticles#unweighted!
                hists['weight'] = [ h, bins ]
        for spol in ('polx','poly','polz'):
            if spol in cnst_stats:
                cnst_stats.remove(spol)
                sc=_StatCollector()
                sc.add_data(np.asarray([0.0],float),np.asarray([weight_sum],float))
                collected_stats[spol] = sc
                if bin_data:
                    bins = np.linspace(-1.0,1.0,nbins+1)
                    h = np.zeros(nbins)
                    assert nbins % 2 != 0#nbins is odd, value 0.0 falls at bin center:
                    h[nbins//2] = weight_sum
                    hists[spol] = [ h, bins ]

    for s in list(freq_uc):
        #sort by frequency:
        u,c=freq_uc[s]
        sortidx=np.argsort(u,kind='mergesort')#the indices that would sort u
        u,c=u[sortidx],c[sortidx]
        sortidx=np.argsort(c,kind='mergesort')[::-1]#the indices that would sort c, viewed in reverse order
        freq_uc[s] = u[sortidx],c[sortidx]

    results = { 'file':{'type':'fileinfo','integral':weight_sum,'nparticles':mcplfile.nparticles,
                        'stat_sum':dict(mcplfile.stat_sum)} }
    if isinstance(mcplfile,_SelectedFile):
        if mcplfile.selection:
            results['file']['selection'] = mcplfile.selection
        if getattr(mcplfile,'edit',None):
            results['file']['edit'] = mcplfile.edit
    for s,uc in freq_uc.items():
        results[s] = { 'unique_values': uc[0], 'unique_values_counts' : uc[1], 'weighted' : True, 'type':'freq' }

    units={'ekin': 'MeV','x': 'cm','y': 'cm','z': 'cm','time': 'ms'}

    for s,sc in collected_stats.items():
        d=sc.as_dict()
        d.update({'summary':sc.summarise(),
                  'name':s,
                  'unit':units.get(s,None),
                  'weighted': s!='weight',
                  'type' : 'hist'})
        if bin_data:
            h,bins = hists[s]
            d.update({'hist_bins' : bins,
                      'hist' : h})
        results[s] = d

    return results

_freq_alt_descr =  {'pdgcode': _pdg_database,
                    'userflags':lambda x : f'0x{x:08x}'}

def dump_stats(stats):
    """Format and print provided statistics object to stdout. The stats object is
    assumed to have been created by a call to collect_stats()"""

    if not isinstance(stats,dict):
        stats = collect_stats(stats,bin_data=False)
    print('------------------------------------------------------------------------------')
    if 'selection' in stats['file']:
        print(f"selection    : {stats['file']['selection']}")
    if 'edit' in stats['file']:
        print(f"edit         : {stats['file']['edit']}")
    print(f"nparticles   : {stats['file']['nparticles']}")
    print('sum(weights) : {:g}'.format(stats['file']['integral']))
    for key, val in stats['file'].get('stat_sum',{}).items():
        print(f"stat:sum:{key} : {'n/a' if val is None else f'{val:.15g}'}")
    if set(stats).intersection(_possible_std_stats):
        print('------------------------------------------------------------------------------')
        print('             :            mean             rms             min             max')
        print('------------------------------------------------------------------------------')

    for statname in _possible_std_stats:
        if statname not in stats:
            continue
        s=stats[statname]
        assert s['type']=='hist'
        su = '{} {}'.format(statname.ljust(6),('[{}]'.format(s['unit'])).rjust(5)) if s['unit'] else statname
        print('{} : {:15g} {:15.5g} {:15g} {:15g}'.format(su.ljust(12),s['mean'],s['rms'],s['min'],s['max']))
    for statname in _possible_freq_stats:
        if statname not in stats:
            continue
        print('------------------------------------------------------------------------------')
        s=stats[statname]
        assert s['type']=='freq'
        fct_alt_descr = _freq_alt_descr.get(statname,lambda x: '')
        #fmt_fct = freq_formats_fcts[statname]
        uv,uvc=s['unique_values'],s['unique_values_counts'].copy()
        percents=uvc*(100.0/uvc.sum())
        showmax=50
        print (f'{statname.ljust(12)} : ',end='')
        for i,(u,p,c) in enumerate(zip(uv,percents,uvc)):
            txt=f'{u}'
            if i+1==showmax:
                txt='other'
                alttxt=''
                p=percents[i:].sum()
                c=uvc[i:].sum()
            else:
                alttxt=fct_alt_descr(u)
            print('{} {} {:12g} ({:5.2f}%)'.format(txt.rjust(26 if i else 11),
                                       (f'({alttxt})' if alttxt else '').ljust(12),
                                       c,p))
            if i+1==showmax:
                break
        print ('                     [ values ]             [ weighted counts ]')
    print('------------------------------------------------------------------------------')

def _stats_figures(stats):
    """Figures (see mcpl.plotting) with plots of the statistics collected with
    collect_stats() (or a file, for which collect_stats() is called)."""
    if not isinstance(stats,dict):
        stats = collect_stats(stats,bin_data=True)
    figures = []
    showmax=10
    for s in _possible_freq_stats:
        if s not in stats:
            continue
        freq=stats[s]
        u,c=freq['unique_values'],freq['unique_values_counts']
        fct_alt_descr = _freq_alt_descr.get(s,lambda x: None)
        def fmt_fct_raw(x, fct_alt_descr=fct_alt_descr):
            alttxt = fct_alt_descr(x)
            return f'{x!s}\n({alttxt})' if alttxt is not None else str(x)
        names = [ fmt_fct_raw(x) for x in u ]
        if len(c)>showmax:
            sum_other = c[showmax-1:].sum()
            names, c = names[0:showmax], c[0:showmax].copy()
            c[showmax-1] = sum_other
            names[showmax-1] = 'other'
        percents = c.astype(float)*100.0/sum(c)
        labels = [f'{e}\n{percents[i]:.2f}%' for i,e in enumerate(names)]
        figures.append(Figure( panels = [ Panel( title = s,
                                                 items = [ Bars(labels,c) ] ) ] ))
    for s in _possible_std_stats:
        if s not in stats:
            continue
        h=stats[s]
        hist,bins = h['hist'],h['hist_bins']
        title = '{}{} ({})'.format(s,
                                   ' [{}]'.format(h['unit']) if h['unit'] is not None else '',
                                   'weighted' if h['weighted'] else 'unweighted')
        figures.append(Figure( panels = [ Panel( title = title, xlabel = h['summary'],
                                                 xlim = ( bins[0], bins[-1] ),
                                                 items = [ StepHist(bins,hist) ] ) ] ))
    return figures

def plot_stats(stats,pdf=False,set_backend=None):
    """Produce plots of provided statistics object with matplotlib. The pdf
    parameter can be set to a filename and if so, the plots will be produced in
    that newly created PDF file, rather than being shown interactively. The
    set_backend parameter can be used to select a matplotlib backend. The stats
    object is assumed to have been created by a call to collect_stats()."""

    if pdf is True:
        raise MCPLError('If set, the pdf parameter should be a string'
                        +' containing the desired filename of the PDF file to be created')

    if pdf and os.path.exists(pdf):
        raise MCPLError(f'PDF file {pdf} already exists')

    figures = _stats_figures(stats)
    if pdf:
        save(figures,pdf,backend='matplotlib',mpl_backend=set_backend)
    else:
        show(figures,backend='matplotlib',mpl_backend=set_backend)
