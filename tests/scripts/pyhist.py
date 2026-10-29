
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


# NEEDS: numpy

# Test histograms (mcpl.histogram, mcpl.histogram2d, mcpl.plot_histograms),
# the figures of plot_stats, and mcpltool --hist, using the plotting backend
# for tests (which prints descriptions of the figures).

import contextlib
import io
import pathlib
import shutil

import mcpldev as mcpl
import numpy as np
from MCPLTestUtils.dirs import test_data_dir

#Use local copies of the files, for printouts without full paths:
shutil.copy(test_data_dir.joinpath('example.mcpl'),'example.mcpl')
shutil.copy(test_data_dir.joinpath('ref','reffile_1.mcpl'),'reffile_1.mcpl')
example_file = pathlib.Path('example.mcpl')
ref1 = pathlib.Path('reffile_1.mcpl')
def show(obj):
    figs = obj if isinstance(obj,list) else [ obj.figure() ]
    mcpl.plotting.show(figs, backend='test')

def test_histograms():
    with mcpl.MCPLFile(example_file) as f:
        b = f.read_block()
    h = mcpl.histogram(example_file, 'ekin/MeV', logx=True, split='pdgcode')
    show(h)
    assert np.isclose(sum(c.sum() for c in h.contents.values()), b.weight.sum())
    h = mcpl.histogram(example_file, 'ekin/eV', pick='pdgcode == neutron',
                       lethargy=True, bins=20)
    show(h)
    ref = np.histogram(b.ekin[b.pdgcode==2112]*1e6, bins=h.edges)[0]
    assert np.allclose(h.contents[None], ref)
    assert np.allclose(h.values(), ref/np.log(h.edges[1:]/h.edges[:-1]))
    print(h.to_text())
    h = mcpl.histogram(example_file, 'acos(uz)/deg', range=(0,90), bins=9,
                       split='x > 0cm', unweighted=True)
    show(h)
    print(h.to_text())
    h = mcpl.histogram([example_file, ref1], 'x/cm', range=(-20,20), bins=8)
    show(h)
    print('underflow:', h.underflow, 'overflow:', h.overflow)
    h = mcpl.histogram(example_file, 'pdgcode', split='pdgcode', max_curves=3,
                       range=(-300,2300), bins=26)
    show(h)
    h = mcpl.histogram2d(example_file, 'x/cm', 'y/cm', bins=10,
                         pick=mcpl.ParticleFilter('pdgcode == gamma'))
    show(h)
    assert np.isclose(h.contents.sum(), np.count_nonzero(b.pdgcode==22))
    #No selected particles, but a range (so an empty histogram), with splits:
    for split in ('pdgcode', 'x > 0cm'):
        h = mcpl.histogram(example_file, 'ekin/MeV', pick='x > 1km',
                           range=(0,10), bins=2, split=split)
        print(f'empty histogram with split={split!r}:', h.to_text())
    #Labels of split values, which are conditions only if all values in all
    #blocks are 0 or 1 (here only the first block has just zeros):
    with mcpl.MCPLFile('reffile_1.mcpl',blocklength=2) as f:
        h = mcpl.histogram(f, 'x/cm', split='fileidx // 2', bins=1)
    print('labels of split=fileidx // 2:', sorted(h.contents))
    with mcpl.MCPLFile('reffile_1.mcpl',blocklength=2) as f:
        h = mcpl.histogram(f, 'x/cm', split='fileidx > 1', bins=1)
    print('labels of split=fileidx > 1:', sorted(h.contents))
    for args, kwargs in ( (('ekin',),{}), (('ekin/MeV',),{'pick':'x > 1km'}),
                          (('x/cm',),{'logx':True,'range':(-1,1)}),
                          (('wavelength',),{}), (('x/cm',),{'split':'x'}),
                          #(the arguments bins and range):
                          (('x/cm',),{'bins':0}), (('x/cm',),{'bins':-3}), (('x/cm',),{'bins':2.5}),
                          (('x/cm',),{'bins':'x'}), (('x/cm',),{'bins':True}),
                          (('x/cm',),{'range':(5,1)}), (('x/cm',),{'range':(1,1)}),
                          (('x/cm',),{'range':(0,float('inf'))}), (('x/cm',),{'range':'a'}),
                          (('x/cm',),{'range':(1,2,3)}) ):
        try:
            mcpl.histogram(example_file, *args, **kwargs)
            print(f'histogram{args} {kwargs}: no error')
        except mcpl.MCPLError as e:
            print(f'histogram{args} {kwargs}: {e}')
    for kwargs in ( {'bins':(5,0)}, {'bins':[3]}, {'xrange':(1,0)}, {'yrange':'a'} ):
        try:
            mcpl.histogram2d(example_file, 'x/cm', 'y/cm', **kwargs)
            print(f'histogram2d {kwargs}: no error')
        except mcpl.MCPLError as e:
            print(f'histogram2d {kwargs}: {e}')
    h = mcpl.histogram(example_file, 'x/cm', bins=np.int64(4), range=[-1,1])
    print('bins as a numpy integer, and range as a list:', len(h.edges)-1, h.edges[[0,-1]].tolist())

def test_stats_figures():
    show(mcpl.stats_figures(mcpl.collect_stats(example_file)))
    show(mcpl.stats_figures(mcpl.collect_stats(example_file,pick='pdgcode == electron')))

def test_overlay():
    hn = mcpl.histogram(example_file, 'ekin/MeV', pick='pdgcode == neutron',
                        logx=True, bins=10)
    hg = mcpl.histogram(example_file, 'ekin/MeV', pick='pdgcode == gamma',
                        logx=True, bins=10)
    mcpl.plot_histograms([hn,hg], overlay=True, backend='test', logy=True)
    mcpl.plot_histograms([hn,hg], overlay=True, labels=['n','g'], backend='test')
    files = mcpl.plot_histograms([hn,hg], filename='hists.txt', backend='test')
    print(f'plot_histograms without overlay created {files}')
    h2 = mcpl.histogram([example_file, ref1], 'x/cm', range=(-20,20), bins=4)
    mcpl.plot_histograms([h2,hn], overlay=True, backend='test')
    for args, kwargs in ( ( [], {} ),
                          ( [hn, mcpl.histogram2d(example_file,'x/cm','y/cm')], {} ),
                          ( [hn, hg], {'labels':['a']} ) ):
        try:
            mcpl.plot_histograms(args, overlay=True, backend='test', **kwargs)
        except mcpl.MCPLError as e:
            print(f'plot_histograms(overlay=True) with {len(args)} histograms {kwargs}: {e}')

def test_autobins():
    #Without bins, the number of bins follows from the effective number of
    #entries (square root, clamped to [10,400]), after histogramming with many
    #bins which are then merged exactly:
    from mcpldev._histogram import _auto_nbins, _nice_nbins
    print('nice numbers of bins:',[ (m,_nice_nbins(m)) for m in (1200,400,239,83,37,15,8) ])
    for neff in (1, 100, 1000, 1e4, 1e5, 1e6):
        print(f'neff={neff:g}: bins of 1080 -> {_auto_nbins(neff,1080)},'
              f' of 216 -> {_auto_nbins(neff,216)}, 2D of 216 -> {_auto_nbins(neff,216,2)}')
    #Sanity of the choices for all plot widths and a range of statistics: the
    #bins merge exactly, few columns are unused, and the number of bins is
    #close to the target unless the plot is too narrow for it:
    import math
    stats, nbad = [], 0
    for ncols in [None] + list(range(29,240)):
        nb = _nice_nbins(1200 if ncols is None else ncols)
        for neff in (1,3,10,30,100,300,1e3,3e3,1e4,3e4,1e5,1e6,1e8):
            n = _auto_nbins(neff,nb)
            target = max(10,min(400,round(math.sqrt(neff))))
            unused = 0.0 if ncols is None else ( ncols - nb ) / ncols
            capped = ( n == nb )#(every column used, narrow plot)
            ratio = n / target
            ok = ( nb % n == 0 and ( ncols is None or nb <= ncols ) and unused <= 0.15
                   and ( capped or 0.6 <= ratio <= 1.5 ) )
            nbad += ( not ok )
            stats.append((ratio,unused,capped))
    print(f'{len(stats)} (ncols,neff) cases, {nbad} bad, ratio to target'
          f' {min(r for r,_,c in stats if not c):.2f}..{max(r for r,_,c in stats if not c):.2f}'
          f' when not capped, {sum(c for _,_,c in stats)} capped by narrow plots,'
          f' at most {100*max(u for _,u,_ in stats):.0f}% unused columns')
    h = mcpl.histogram(example_file, 'x/cm')
    hf = mcpl.histogram(example_file, 'x/cm', bins=1080)
    v, vf = h.values(), hf.values()
    print(f'auto: {len(h.edges)-1} bins, sum {v.sum():g} (1080 bins: {vf.sum():g}),'
          f' merged exactly: {np.allclose(v,vf.reshape(len(v),-1).sum(axis=1))},'
          f' same edges: {np.allclose(h.edges,hf.edges[::1080//len(v)])},'
          f' for display: {h._display_bins}')
    h = mcpl.histogram(example_file, 'x/cm', pick='pdgcode == 2212')
    print(f'auto with few particles: {len(h.edges)-1} bins, sum {h.values().sum():g}')
    h = mcpl.histogram(example_file, 'x/cm', _maxbins=83)
    print(f'auto with at most 83 bins: {len(h.edges)-1} bins, for display: {h._display_bins}')
    h = mcpl.histogram2d(example_file, 'x/cm', 'y/cm')
    print(f'auto 2D: {h.contents.shape} bins, sum {h.contents.sum():g},'
          f' for display: {h._display_bins}')
    h = mcpl.histogram2d(example_file, 'x/cm', 'y/cm', _maxbins=(69,15))
    print(f'auto 2D with at most (69,15) bins: {h.contents.shape} bins,'
          f' sum {h.contents.sum():g}, for display: {h._display_bins}')
    h = mcpl.histogram2d(example_file, 'x/cm', 'y/cm', bins=(8,4))
    print(f'2D with bins=(8,4): {h.contents.shape} bins, for display: {h._display_bins}')

def tool(*args):
    out = io.StringIO()
    rc = 0
    with contextlib.redirect_stdout(out):
        try:
            mcpl.app_mcpltool(['mcpltool',*args])
        except SystemExit as e:
            rc = e.code
    print(f'mcpltool {" ".join(args)}: exit code {rc}')
    for line in out.getvalue().splitlines():
        print(f'   | {line}')

def test_cmdline():
    ex = str(example_file)
    tool('-H','ekin/MeV;logx;split=pdgcode','-B','test',ex)
    tool('-H','ekin/eV;lethargy;bins=5;print','-p','pdgcode == neutron',ex)
    tool('-H','x/cm : y/cm;bins=4;print','-p','pdgcode == gamma',ex)
    tool('-H','x/cm:y/cm;bins=2;xrange=-10:10;yrange=0:5;print',ex)
    tool('-H','x/cm : y/cm;bins=2;xrange=-10:10;print',ex)
    tool('-H','x/cm : y/cm;bins=3,2;print',ex)
    tool('-H','x/cm;range=-10:10;bins=4','-B','test',ex,str(ref1))
    tool('-H','time/ms;logx;logy;unweighted','-B','test',ex)
    tool('-H','ekin/MeV;split=pdgcode;range=0:10;bins=2;print',
         '-p','x > 1km',ex)
    #-l, -s and -E (the particles are picked before they are edited):
    tool('-H','z/cm;bins=2;range=0:100;print','-s1000',ex)
    tool('-H','z/cm;bins=2;range=0:100;print','-l3','-E','z += 50cm',ex)
    tool('-H','z/cm;bins=2;range=0:100;print','--pick=z < 25cm',
         '--edit=z += 50cm',ex)
    tool('-Hekin/MeV;print;bins=2','-ppdgcode==22',ex)
    for bad in ( ['-H','ekin',ex], ['-H','ekin/MeV;bins=0',ex],
                 ['-H','ekin/MeV;range=1',ex], ['-H','ekin/MeV;range=2:1',ex],
                 ['-H','ekin/MeV;range=1:2,3:4',ex], ['-H','ekin/MeV;xrange=1:2',ex],
                 ['-H','x/cm : y/cm;range=1:2',ex],
                 ['-H','x/cm : y/cm;logx',ex], ['-H','x/cm : y/cm : z/cm',ex],
                 ['-H','x/cm;bins',ex], ['-H','x/cm;logx=1',ex],
                 ['-H','x/cm;logx;logx',ex], ['-H','x/cm;foo',ex],
                 ['-H','x/cm','-B','foo',ex], ['--logx',ex], ['--bins','10',ex],
                 ['-o','a.pdf',ex], ['-H','x/cm','-e',ex,'out.mcpl'],
                 ['-H','x/cm'], ['-H','x/cm;print','-t',ex],
                 ['-H','x/cm','-t','-o','a.txt',ex] ):
        tool(*bad)

def test_cmdline_more():
    #Plots of statistics, and saving files, with the test backend (which
    #describes the figures), and argument errors:
    ex = str(example_file)
    tool('-S','-o','stats.txt','-B','test','-p','pdgcode == gamma',ex)
    tool('-S','-s1000','-E','x = 1cm',ex)
    tool('-H','x/cm;bins=3','-o','hist.txt','-B','test',ex)
    for bad in ( ['-p','neutron',ex], ['-p2112',ex], ['-p',' gamma ',ex],
                 ['-p'], ['-lX',ex], ['-l',ex],
                 ['-p','x > 0','-p','x < 1cm',ex], ['--pdf',ex], ['--gui',ex],
                 ['--select','x > 0',ex], ['-S','-B','test',ex], ['-S','-t',ex],
                 ['-S','-H','x/cm',ex], [ex,ex,ex],
                 ['--text',ex], ['--text',ex,'hist.txt'],
                 ['-t',ex], ['-j','-H','x/cm',ex], ['--no-comment','-S',ex],
                 ['-H','x/cm : y/cm;split=pdgcode',ex],
                 ['-H','x/cm','-o','hist.txt','-B','test',ex],
                 ['-H','x/cm','-o','hist',ex], ['-H','x/cm','-o','hist.jpg',ex],
                 ['-H','x/cm','-o','hist.png','-d',ex],
                 ['-p','x > "1"',ex], ['-E','z = 1cm, x = 0',ex] ):
        tool(*bad)

def test_help_topics():
    #Only the start of each topic (the rest are tables of all names):
    for args in ( ['-p','help'], ['--edit=help'], ['-H','help',str(example_file)] ):
        out = io.StringIO()
        rc = 0
        with contextlib.redirect_stdout(out):
            try:
                mcpl.app_mcpltool(['mcpltool',*args])
            except SystemExit as e:
                rc = e.code
        lines = out.getvalue().splitlines()
        print(f'mcpltool {" ".join(args)}: exit code {rc}, {len(lines)} lines,'
              ' starting with:')
        for line in lines[:3]:
            print(f'   | {line}')

test_histograms()
test_stats_figures()
test_overlay()
test_cmdline()
test_cmdline_more()
test_help_topics()
test_autobins()
