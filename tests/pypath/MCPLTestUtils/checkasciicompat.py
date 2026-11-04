
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

import pathlib


def _autodetect_nploadtxtargs(fn):
    #MCPL-ASCII
    #ASCII-FORMAT: v1
    #NPARTICLES: 123
    #END-HEADER
    import numpy
    mcplhdr_end = None
    mcpl_nparticles = None
    with pathlib.Path(fn).open('rt') as fh:
        for i,line in enumerate(fh):
            line = line.strip()
            if i==0:
                if line!='#MCPL-ASCII':
                    return None
                continue
            if line.startswith('#NPARTICLES:'):
                mcpl_nparticles = int( line[len('#NPARTICLES:'):].strip() )
                continue
            if line.startswith('#ASCII-FORMAT:'):
                if line[len('#ASCII-FORMAT:'):].strip()!='v1':
                    raise RuntimeError('Only supports MCPL-ASCII "v1" format')
                continue

            if line == '#END-HEADER':
                mcplhdr_end = i
                continue
            if mcplhdr_end is not None:
                if line.startswith('index'):
                    _int = numpy.dtype('int64')
                    _uint = numpy.dtype('uint64')
                    _fp = numpy.dtype('float64')
                    return {
                        'genfromtxt_args' : {
                            'skip_header':i+1,
                            'dtype' : [numpy.dtype(e) for e in
                                       (_uint,_int,_fp,_fp,_fp,_fp,_fp,_fp,_fp,
                                        _fp,_fp,_fp,_fp,_fp,_uint)],
                            'converters' : {14 : lambda s : int(s,16) }
                        },
                        'nparticles' : mcpl_nparticles
                    }
                else:
                    break
            if i==10000:
                break
    raise RuntimeError(f'Unexpected format of MCPL-ASCII file: {fn}')


def load_file( fn ):
    fn = pathlib.Path(fn)
    assert fn.is_file()
    det_res = _autodetect_nploadtxtargs(fn) or {}
    import numpy
    if det_res is None:
        return numpy.genfromtxt(fn).T
    if det_res['nparticles'] == 0:
        return None
    return numpy.genfromtxt(fn,**det_res['genfromtxt_args']).T
