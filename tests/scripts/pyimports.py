
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

# Test that the plotting backends, and the packages they use (matplotlib,
# plotly, ...), are only imported when plots are actually made, and not by
# "import mcpl" or when using the other functionality of the Python API or of
# pymcpltool. Each case runs in a new Python process, which reports the
# modules it imported.

import json
import os
import pathlib
import shutil
import subprocess
import sys

from MCPLTestUtils.dirs import test_data_dir

example_file = test_data_dir.parent.parent.joinpath('examples','example.mcpl')
shutil.copy(example_file, 'example.mcpl')
shutil.copy(example_file, 'example2.mcpl')
#File which looks like it was not properly closed (number of particles in the
#header is 0), for --repair:
data = bytearray(example_file.read_bytes())
data[8:16] = bytes(8)
pathlib.Path('torepair.mcpl').write_bytes(data)

#Modules which must not be imported unless plots are made:
plot_modules = ( 'matplotlib', 'plotly', 'kaleido', 'PIL' )

code_template = """
import contextlib, json, os, sys
import mcpldev as mcpl
with open(os.devnull,'w') as devnull, contextlib.redirect_stdout(devnull):
    try:
%s
    except SystemExit:
        pass
mods = sorted( m for m in sys.modules
               if m.split('.')[0] in %r or m.startswith('mcpldev._plotbackend_') )
print(json.dumps(mods))
"""

def tool(*args):
    return f"mcpl.app_pymcpltool(['pymcpltool',{','.join(repr(a) for a in args)}])"

cases = [
    ( 'import mcpl', 'pass' ),
    ( 'read with select and edit',
      ( "for b in mcpl.MCPLFile('example.mcpl', select='pdgcode == neutron',"
        " edit='rotate_z(90deg)').particle_blocks: pass" ) ),
    ( 'write and merge',
      ( "f = mcpl.MCPLOutFile('w1.mcpl'); f.add_particles(direction=(0,0,1.)); f.close()\n"
        "        mcpl.forcemerge_files('w2.mcpl', ['w1.mcpl','example.mcpl']).close()" ) ),
    ( 'statistics', "mcpl.dump_stats(mcpl.collect_stats('example.mcpl'))" ),
    ( 'histogram as text', "print(mcpl.histogram('example.mcpl','ekin/MeV',bins=4).to_text())" ),
    ( 'pymcpltool FILE', tool('example.mcpl') ),
    ( 'pymcpltool --select', tool('-l3','--select','pdgcode == gamma','example.mcpl') ),
    ( 'pymcpltool --stats', tool('--stats','example.mcpl') ),
    ( 'pymcpltool --hist --print', tool('--hist','ekin/MeV','--print','example.mcpl') ),
    ( 'pymcpltool --extract', tool('--extract','example.mcpl','e.mcpl','--edit','z += 1m') ),
    ( 'pymcpltool --merge', tool('--merge','m.mcpl','example.mcpl','example2.mcpl') ),
    ( 'pymcpltool --repair', tool('--repair','torepair.mcpl') ),
    ( 'pymcpltool --text', tool('--text','example.mcpl','t.txt') ),
    #Plotting with the test backend loads only that backend:
    ( 'plot with the test backend',
      "mcpl.histogram('example.mcpl','ekin/MeV',bins=4).plot(backend='test')" ),
    ( 'pymcpltool --hist with the test backend',
      tool('--hist','ekin/MeV','--backend','test','example.mcpl') ),
]

def main():
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(p for p in sys.path if p)
    for title, code in cases:
        rv = subprocess.run([sys.executable,'-c',code_template%('        '+code,plot_modules)],
                            capture_output=True, text=True, env=env, check=False)
        assert rv.returncode == 0, f'{title} failed:\n{rv.stderr}'
        mods = json.loads(rv.stdout.strip().splitlines()[-1])
        print(f'{title:<40}: {", ".join(mods) or "no plotting modules imported"}')
        if 'test backend' in title:
            assert mods == ['mcpldev._plotbackend_test'], mods
        else:
            assert not mods, mods

if __name__ == '__main__':
    main()
