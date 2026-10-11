
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
# the figures of plot_stats, and pymcpltool --hist, using the plotting backend
# for tests (which prints descriptions of the figures).

import contextlib
import io
import pathlib
import shutil

import mcpldev as mcpl
import numpy as np
from MCPLTestUtils.dirs import test_data_dir

#Use local copies of the files, for printouts without full paths:
shutil.copy(test_data_dir.parent.parent.joinpath('examples','example.mcpl'),'example.mcpl')
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
    h = mcpl.histogram(example_file, 'ekin/eV', select='pdgcode == neutron',
                       lethargy=True, bins=20)
    show(h)
    ref = np.histogram(b.ekin[b.pdgcode==2112]*1e6, bins=h.edges)[0]
    assert np.allclose(h.contents[None], ref)
    assert np.allclose(h.values(), ref/np.log(h.edges[1:]/h.edges[:-1]))
    print(h.to_text())
    h = mcpl.histogram(example_file, 'acos(uz)/deg', range=(0,90), bins=9,
                       split='x > 0cm', weighted=False)
    show(h)
    print(h.to_text())
    h = mcpl.histogram([example_file, ref1], 'x/cm', range=(-20,20), bins=8)
    show(h)
    print('underflow:', h.underflow, 'overflow:', h.overflow)
    h = mcpl.histogram(example_file, 'pdgcode', split='pdgcode', max_curves=3,
                       range=(-300,2300), bins=26)
    show(h)
    h = mcpl.histogram2d(example_file, 'x/cm', 'y/cm', bins=10,
                         select=mcpl.ParticleFilter('pdgcode == gamma'))
    show(h)
    assert np.isclose(h.contents.sum(), np.count_nonzero(b.pdgcode==22))
    #No selected particles, but a range (so an empty histogram), with splits:
    for split in ('pdgcode', 'x > 0cm'):
        h = mcpl.histogram(example_file, 'ekin/MeV', select='x > 1km',
                           range=(0,10), bins=2, split=split)
        print(f'empty histogram with split={split!r}:', h.to_text())
    for args, kwargs in ( (('ekin',),{}), (('ekin/MeV',),{'select':'x > 1km'}),
                          (('x/cm',),{'logx':True,'range':(-1,1)}),
                          (('wavelength',),{}), (('x/cm',),{'split':'x'}) ):
        try:
            mcpl.histogram(example_file, *args, **kwargs)
            print(f'histogram{args} {kwargs}: no error')
        except mcpl.MCPLError as e:
            print(f'histogram{args} {kwargs}: {e}')

def test_stats_figures():
    show(mcpl.stats_figures(mcpl.collect_stats(example_file)))
    show(mcpl.stats_figures(mcpl.collect_stats(example_file,select='pdgcode == electron')))

def test_overlay():
    hn = mcpl.histogram(example_file, 'ekin/MeV', select='pdgcode == neutron',
                        logx=True, bins=10)
    hg = mcpl.histogram(example_file, 'ekin/MeV', select='pdgcode == gamma',
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

def tool(*args):
    out = io.StringIO()
    rc = 0
    with contextlib.redirect_stdout(out):
        try:
            mcpl.app_pymcpltool(['pymcpltool',*args])
        except SystemExit as e:
            rc = e.code
    print(f'pymcpltool {" ".join(args)}: exit code {rc}')
    for line in out.getvalue().splitlines():
        print(f'   | {line}')

def test_cmdline():
    ex = str(example_file)
    tool('--hist','ekin/MeV','--logx','--split','pdgcode','--backend','test',ex)
    tool('--hist','ekin/eV','--lethargy','-pneutron','--bins','5','--print',ex)
    tool('--hist','x/cm : y/cm','--bins','4','--select','pdgcode == gamma','--print',ex)
    tool('--hist','x/cm : y/cm','--bins','2','--range','-10:10,0:5','--print',ex)
    tool('--hist','x/cm','--range','-10:10','--bins','4','--backend','test',ex,str(ref1))
    tool('--hist','time/ms','--logx','--logy','--unweighted','--backend','test',ex)
    tool('--hist','ekin/MeV','--split','pdgcode','--range','0:10','--bins','2',
         '--select','x > 1km','--print',ex)
    for bad in ( ['--hist','ekin',ex], ['--hist','ekin/MeV','--bins','0',ex],
                 ['--hist','ekin/MeV','--range','1',ex], ['--hist','ekin/MeV','--range','2:1',ex],
                 ['--hist','ekin/MeV','--range','1:2,3:4',ex],
                 ['--hist','x/cm : y/cm','--logx',ex], ['--hist','x/cm : y/cm : z/cm',ex],
                 ['--hist','x/cm','--backend','foo',ex], ['--logx',ex], ['--bins','10',ex],
                 ['--output','a.pdf',ex], ['--hist','x/cm','--extract',ex,'out.mcpl'],
                 ['--hist','x/cm'] ):
        tool(*bad)

test_histograms()
test_stats_figures()
test_overlay()
test_cmdline()
