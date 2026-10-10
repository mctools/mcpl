
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

# Check that the public names of the Python API in released versions of MCPL
# are still available, both in the mcpl package and in the mcpl.mcpl module
# (which was a single-file module containing everything until MCPL 2.2.8), and
# that using them from mcpl.mcpl gives deprecation warnings.

import warnings

#__all__ of mcpl and mcpl.mcpl in MCPL 2.2.8:
released_names = [ 'MCPLError', 'MCPLFile', 'MCPLParticle', 'MCPLParticleBlock',
                   'app_pymcpltool', 'collect_stats', 'convert2ascii', 'dump_file',
                   'dump_stats', 'encode_stat_sum', 'is_valid_stat_sum_key',
                   'plot_stats' ]
released_module_only_names = [ 'main' ]

def show_warnings(wlist):
    for w in wlist:
        print(f'    {w.category.__name__}: {w.message}')
    if not wlist:
        print('    (no warnings)')

def main():
    import mcpldev
    for n in released_names:
        assert hasattr(mcpldev, n), f'mcpl.{n} missing'
        assert n in mcpldev.__all__, f'{n} missing in mcpl.__all__'
    for n in mcpldev.__all__:
        assert hasattr(mcpldev, n), f'mcpl.{n} in __all__ but missing'
    print(f'All {len(released_names)} released names are available in mcpl')

    with warnings.catch_warnings(record=True) as wlist:
        warnings.simplefilter('always')
        import mcpldev.mcpl
        from mcpldev.mcpl import main as _  # noqa: F401
    print('Importing mcpl.mcpl and mcpl.mcpl.main:')
    show_warnings(wlist)

    assert set(mcpldev.mcpl.__all__) == set(released_names
                                            + released_module_only_names)
    print('Using each name in mcpl.mcpl the first time:')
    for n in mcpldev.mcpl.__all__:
        with warnings.catch_warnings(record=True) as wlist:
            warnings.simplefilter('always')
            obj = getattr(mcpldev.mcpl, n)
        assert obj is getattr(mcpldev, n, getattr(mcpldev.mcpl, n))
        print(f'  {n}:')
        show_warnings(wlist)
        assert all(w.filename == __file__ for w in wlist)

    print('Using them again:')
    with warnings.catch_warnings(record=True) as wlist:
        warnings.simplefilter('always')
        for n in mcpldev.mcpl.__all__:
            getattr(mcpldev.mcpl, n)
        d = {}
        exec('from mcpldev.mcpl import *', d)  # noqa: S102
        assert all( n in d for n in mcpldev.mcpl.__all__ )
        assert mcpldev.mcpl.__version__ == mcpldev.__version__
    show_warnings(wlist)

    try:
        mcpldev.mcpl.nosuchname  # noqa: B018
    except AttributeError as e:
        print(f'Unknown name gives AttributeError: {e}')

if __name__ == '__main__':
    main()
