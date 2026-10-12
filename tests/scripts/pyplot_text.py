
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

# Test the plotting backends drawing figures as text (unicode and ascii), with
# fixed sizes so the output does not depend on the terminal.

import contextlib
import io
import os
import pathlib
import subprocess
import sys

import mcpldev as mcpl
from mcpldev.plotting import Figure, Panel, Text
from MCPLTestUtils.dirs import test_data_dir

example_file = test_data_dir.parent.parent.joinpath('examples','example.mcpl')

def show(figs, backend, width=72, height=8):
    opts = { f'{backend}_width' : width, f'{backend}_height' : height }
    print(f'==> {backend} backend, width {width}, height {height}:')
    mcpl.plotting.show(figs, backend=backend, **opts)

def test_histograms():
    h = mcpl.histogram(example_file, 'ekin/MeV', logx=True, bins=50)
    for backend in ('unicode','ascii'):
        show(h.figure(), backend)
    #Several curves (markers and legend), and a logarithmic y axis:
    h = mcpl.histogram(example_file, 'ekin/MeV', logx=True, bins=50,
                       split='pdgcode', max_curves=3)
    show(h.figure(logy=True), 'unicode', height=10)
    h = mcpl.histogram(example_file, 'acos(uz)/deg', range=(0,180), bins=36,
                       split='x > 0cm')
    show(h.figure(), 'ascii')
    #2D histogram:
    h = mcpl.histogram2d(example_file, 'x/cm', 'y/cm', bins=30,
                         select='pdgcode == neutron')
    for backend in ('unicode','ascii'):
        show(h.figure(), backend, height=12)

def test_stats():
    figs = mcpl.stats_figures(example_file)
    show(figs[0], 'ascii')
    show(figs[1:3], 'unicode', height=6)
    show(Figure( title='Empty', panels=[ Panel( title='No data here',
                                               items=[ Text('No data') ] ) ] ), 'unicode')

def test_files_and_options():
    figs = mcpl.stats_figures(example_file)[:2]
    for backend in ('unicode','ascii'):
        files = mcpl.plotting.save(figs, f'stats_{backend}.txt', backend=backend,
                                   **{ f'{backend}_width' : 60 })
        data = pathlib.Path(files[0]).read_bytes()
        widths = { len(line) for line in data.decode('utf-8').splitlines() }
        print(f'{backend}: saved {files}, {len(data.splitlines())} lines, max width'
              f' {max(widths)}, ascii only: {data.isascii()}')
    for bad in ( { 'backend' : 'ascii', 'unicode_width' : 50 },
                 { 'backend' : 'unicode', 'filename' : 'x.pdf' } ):
        try:
            fn = bad.pop('filename', None)
            if fn:
                mcpl.plotting.save(figs, fn, **bad)
            else:
                mcpl.plotting.show(figs, **bad)
        except mcpl.MCPLError as e:
            print(f'{bad}: MCPLError: {e}')
    #(the other backends depend on the installed packages):
    avail = mcpl.plotting.available_backends()
    print(f'unicode and ascii backends always available, as the last ones:'
          f' {avail[-2:] == ["unicode","ascii"]}')
    #In terminals which can not show its characters, the unicode backend uses
    #the ASCII characters:
    env = dict(os.environ, PYTHONIOENCODING='ascii',
               PYTHONPATH=os.pathsep.join(p for p in sys.path if p))
    code = ( f'import mcpldev; mcpldev.histogram({str(example_file)!r},"ekin/MeV",'
             'bins=10).plot(backend="unicode",unicode_width=40,unicode_height=5)' )
    rv = subprocess.run([sys.executable,'-c',code], capture_output=True, env=env, check=True)
    print(f'unicode backend with PYTHONIOENCODING=ascii prints only ASCII: {rv.stdout.isascii()}')
    #(splitlines, since the output has \r\n line endings on Windows):
    print('\n'.join(rv.stdout.decode().splitlines()).rstrip())

def test_tool():
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.suppress(SystemExit):
        mcpl.app_pymcpltool(['pymcpltool','--hist','time/ms','--logx','--bins','20',
                             '--backend','ascii',str(example_file)])
    lines = out.getvalue().splitlines()
    print(f'pymcpltool --hist --backend ascii: {len(lines)} lines, first and last:')
    print(lines[0])
    print(lines[-1])

test_histograms()
test_stats()
test_files_and_options()
test_tool()
