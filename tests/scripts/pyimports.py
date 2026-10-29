
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

# Test exactly which modules of the mcpl package are imported by "import mcpl"
# and by each use of the Python API or of mcpltool, so that parts like the
# expressions, statistics, histograms, plotting and the mcpltool command are
# only imported when they are used, and packages like matplotlib not at all
# (unless plots are shown). Each case runs in a new Python process, which
# reports all modules it imported.

import gzip
import json
import os
import pathlib
import shutil
import subprocess
import sys

from MCPLTestUtils.dirs import test_data_dir

example_file = test_data_dir.joinpath('example.mcpl')
shutil.copy(example_file, 'example.mcpl')
shutil.copy(example_file, 'example2.mcpl')
#File which looks like it was not properly closed (number of particles in the
#header is 0), for --repair:
data = bytearray(example_file.read_bytes())
data[8:16] = bytes(8)
pathlib.Path('torepair.mcpl').write_bytes(data)
pathlib.Path('torepair2.mcpl').write_bytes(data)

pathlib.Path('example.mcpl.gz').write_bytes(gzip.compress(example_file.read_bytes()))

#Packages which must not be imported unless plots are shown:
plot_modules = ( 'matplotlib', 'PIL', 'tkinter', 'curses', 'scipp', 'IPython',
                 'ipywidgets' )

code_template = """
import contextlib, json, os, sys
import mcpldev as mcpl
with open(os.devnull,'w') as devnull, contextlib.redirect_stdout(devnull):
    try:
%s
    except SystemExit:
        pass
mods = sorted( m for m in sys.modules
               if m.split('.')[0] in %r or m.startswith('mcpldev.') )
print(json.dumps(mods))
"""

#All modules of the mcpl package imported by "import mcpl" (the expected
#modules of the cases below are those imported in addition to these):
core_modules = ( '_blocks _common _fileops _messages _numpy _physics _reader'
                 ' _statsum _writer constants' )

def tool(*args):
    return f"mcpl.app_mcpltool(['mcpltool',{','.join(repr(a) for a in args)}])"

cases = [
    #Core functionality, which must not import any other modules:
    ( 'import mcpl', '', 'pass' ),
    ( 'read blocks and single particles', '',
      ( "f = mcpl.MCPLFile('example.mcpl'); [ b.ekin.sum() for b in f.particle_blocks ]\n"
        "        [ p.ux for p in mcpl.MCPLFile('example.mcpl').particles ]" ) ),
    ( 'read gzipped file', '',
      "[ b.x for b in mcpl.MCPLFile('example.mcpl.gz').particle_blocks ]" ),
    ( 'write blocks and single particles', '',
      ( "f = mcpl.MCPLOutFile('w1.mcpl'); f.add_particles(direction=(0,0,1.))\n"
        "        f.add_particle(direction=(0,1.,0), ekin=2.0, pdgcode=22); f.close()" ) ),
    ( 'copy blocks with numpy mask', '',
      ( "fin = mcpl.MCPLFile('example.mcpl'); fout = mcpl.MCPLOutFile('w2.mcpl')\n"
        "        fout.transfer_metadata(fin)\n"
        "        [ fout.add_particles(b[b.pdgcode == 2112]) for b in fin.particle_blocks ]\n"
        "        fout.close()" ) ),
    ( 'merge files', '',
      ( "mcpl.merge_files('w3.mcpl', ['example.mcpl','example2.mcpl']).close()\n"
        "        mcpl.forcemerge_files('w4.mcpl', ['w3.mcpl','example.mcpl']).close()\n"
        "        mcpl.merge_inplace('w3.mcpl', 'example.mcpl')" ) ),
    ( 'repair', '', "mcpl.repair('torepair.mcpl')" ),
    #Optional functionality, which must only import what it needs:
    ( 'read with pick and edit', '_expressions',
      ( "for b in mcpl.MCPLFile('example.mcpl', pick='pdgcode == neutron',"
        " edit='rotate_z(90deg)').particle_blocks: pass" ) ),
    ( 'statistics', '_stats', "mcpl.dump_stats(mcpl.collect_stats('example.mcpl'))" ),
    ( 'statistics with pick', '_expressions _stats',
      "mcpl.dump_stats(mcpl.collect_stats('example.mcpl', pick='x > 0cm'))" ),
    ( 'histogram as text', '_expressions _histogram',
      "print(mcpl.histogram('example.mcpl','ekin/MeV',bins=4).to_text())" ),
    ( 'mcpltool FILE', '_cli', tool('example.mcpl') ),
    ( 'mcpltool --pick', '_cli _expressions',
      tool('-l3','--pick','pdgcode == gamma','example.mcpl') ),
    ( 'mcpltool --stats', '_cli _clistats _stats', tool('--stats','example.mcpl') ),
    ( 'mcpltool --hist with print', '_cli _clistats _expressions _histogram',
      tool('--hist','ekin/MeV;print','example.mcpl') ),
    ( 'mcpltool --extract', '_cli', tool('--extract','example.mcpl','e1.mcpl') ),
    ( 'mcpltool --extract --edit', '_cli _expressions',
      tool('--extract','example.mcpl','e2.mcpl','--edit','z += 1m') ),
    ( 'mcpltool --merge', '_cli', tool('--merge','m.mcpl','example.mcpl','example2.mcpl') ),
    ( 'mcpltool --repair', '_cli', tool('--repair','torepair2.mcpl') ),
    ( 'mcpltool --text', '_cli', tool('--text','example.mcpl','t.txt') ),
    #Plotting with the test backend loads only that backend:
    ( 'plot with the test backend',
      '_expressions _histogram plotting _plotbackend _plotbackend_test',
      "mcpl.histogram('example.mcpl','ekin/MeV',bins=4).plot(backend='test')" ),
    ( 'mcpltool --hist with the test backend',
      '_cli _clistats _expressions _histogram plotting _plotbackend _plotbackend_test',
      tool('--hist','ekin/MeV','--backend','test','example.mcpl') ),
]

def main():
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(p for p in sys.path if p)
    core = set(core_modules.split())
    for title, expected, code in cases:
        rv = subprocess.run([sys.executable,'-c',
                             code_template%('        '+code,plot_modules)],
                            capture_output=True, text=True, env=env, check=False)
        assert rv.returncode == 0, f'{title} failed:\n{rv.stderr}'
        mods = json.loads(rv.stdout.strip().splitlines()[-1])
        #Plotting packages must not be imported at all, and exactly the
        #expected modules of the mcpl package:
        assert not any( m.split('.')[0] in plot_modules for m in mods ), mods
        got = { m.split('.',1)[1] for m in mods if m.startswith('mcpldev.') }
        missing = sorted( core - got )
        extra = sorted( got - core )
        print(f'{title:<40}: {" ".join(extra) or "no other modules"}'
              + ( f' (but not {" ".join(missing)})' if missing else '' ))
        assert not missing and extra == sorted(expected.split()), (title, missing, extra)

if __name__ == '__main__':
    main()
