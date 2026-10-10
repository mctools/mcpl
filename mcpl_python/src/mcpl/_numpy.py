
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

"""numpy, with workarounds for old versions of numpy."""

__all__ = []

#numpy version checks (unfortunately NumpyVersion doesn't even exist in all
#releases of numpy back to 1.3.0 so needs workarounds):
try:
    import numpy as np
except ImportError:
    print()
    print("ERROR: For reasons of efficiency, this MCPL python module requires numpy (www.numpy.org)")
    print("ERROR: to be installed. You can perhaps install it using using your software manager and")
    print("ERROR: searching for \"numpy\" or \"python-numpy\", or it might come bundled with software")
    print("ERROR: such as scientific python or anaconda, depending on your platform. Alternatively,")
    print("ERROR: if you are using the pip package manager, you should be able to install it with")
    print("ERROR: the command \"pip install numpy\".")
    print()
    raise

_numpyok=True
_numpy_oldfromfile=False
try:
    from numpy.lib import NumpyVersion
except ImportError:
    NumpyVersion = None
if NumpyVersion is not None:
    if NumpyVersion(np.__version__) < '1.3.0':
        _numpyok = False
    if NumpyVersion(np.__version__) < '1.5.0':
        _numpy_oldfromfile = True
else:
    try:
        vtuple=tuple(int(v) for v in str(np.__version__).strip().split('.')[0:2])
        if vtuple<(1,3):
            _numpyok = False
        if vtuple<(1,5):
            _numpy_oldfromfile = True
    except ValueError:
        _numpyok = False

if not _numpyok:
    print(f"MCPL WARNING: Unsupported numpy version ({np.__version__!s}) detected")

np_dtype = np.dtype
try:
    np.dtype('f8')
except TypeError:
    def np_dtype( x ):
        return np.dtype(x.encode('ascii') if hasattr(x,'encode') else x)

#old np.unique does not understand return_inverse and unique1d must be used
#instead:
np_unique = np.unique if hasattr(np,'unique') else np.unique1d
try:
    np.unique(np.asarray([1]),return_inverse=True)
except TypeError:
    np_unique = np.unique1d

if hasattr(np,'stack'):
    np_stack = np.stack
else:
    #np.stack only added in numpy 1.10. Using the following code snippet from
    #numpy to get the functionality for older releases:
    def np_stack(arrays, axis=0):
        arrays = [np.asanyarray(arr) for arr in arrays]
        if not arrays:
            raise ValueError('need at least one array to stack')
        shapes = {arr.shape for arr in arrays}
        if len(shapes) != 1:
            raise ValueError('all input arrays must have the same shape')
        result_ndim = arrays[0].ndim + 1
        if not -result_ndim <= axis < result_ndim:
            msg = f'axis {axis} out of bounds [-{result_ndim}, {result_ndim})'
            raise IndexError(msg)
        if axis < 0:
            axis += result_ndim
        sl = (slice(None),) * axis + (np.newaxis,)
        expanded_arrays = [arr[sl] for arr in arrays]
        return np.concatenate(expanded_arrays, axis=axis)

if hasattr(np.add,'at'):
    _np_add_at = np.add.at
else:
    #Slow fallback for ancient numpy:
    def _np_add_at(a,indices,b):
        for ib,i in enumerate(indices):
            a[i] += b[ib]
