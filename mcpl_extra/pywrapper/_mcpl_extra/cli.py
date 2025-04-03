
################################################################################
##                                                                            ##
##  This file is part of MCPL (see https://mctools.github.io/mcpl/)           ##
##                                                                            ##
##  Copyright 2015-2025 MCPL developers.                                      ##
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

# Module which expose the actual binary cmdline scripts.

def cli_wrapper_mcpl2ssw():
    _run('mcpl2ssw')

def cli_wrapper_ssw2mcpl():
    _run('ssw2mcpl')

def cli_wrapper_mcpl2phits():
    _run('mcpl2phits')

def cli_wrapper_phits2mcpl():
    _run('phits2mcpl')

def _get_mcpl_shlibdir_unix():
    import subprocess
    rv = subprocess.run( ['mcpl-config','--show','shlibdir'],
                         check = True, capture_output = True )
    if rv.returncode or rv.stderr:
        raise RuntimeError('Problems invoking mcpl-config for shlibdir')
    import pathlib
    return pathlib.Path(rv.stdout.decode().strip()).absolute().resolve()

def _run(toolname):
    import subprocess
    import pathlib
    import sys
    import platform
    a = sys.argv[:]
    a[0] = pathlib.Path(__file__).parent.joinpath('data','bin',toolname)
    sysname = platform.system()
    if sysname != 'Windows':
        #Inject libmcpl.so in (DY)LD_LIBRARY_PATH, just in case:
        import os
        env = os.environ.copy()
        d = _get_mcpl_shlibdir_unix()
        n = 'DYLD_LIBRARY_PATH' if sysname == 'Darwin' else 'LD_LIBRARY_PATH'
        v = env.get(n)
        if v:
            env[n] = '%s:%s'%(d,v)
        else:
            env[n] = str(d)
    else:
        #On windows MCPL.dll should already be in PATH:
        env = None
    rv = subprocess.run( a, env = env )
    raise SystemExit(rv.returncode)
