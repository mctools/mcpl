#!/usr/bin/env python3
"""Python module for accessing MCPL files.

The MCPL (Monte Carlo Particle Lists) format is thoroughly documented on the
project homepage, from where it is also possible to download the entire MCPL
distribution:

     https://mctools.github.io/mcpl/

Specifically, more documentation about how to use the present python module to
access MCPL files can be found at:

     https://mctools.github.io/mcpl/usage_python/

This file can freely used as per the terms in the LICENSE file distributed with
MCPL, also available at https://github.com/mctools/mcpl/blob/master/LICENSE .

A substantial effort went into developing MCPL. If you use it for your work, we
would appreciate it if you would use the following reference in your work:

   T. Kittelmann, et al., Monte Carlo Particle Lists: MCPL, Computer Physics
   Communications 218, 17-42 (2017), https://doi.org/10.1016/j.cpc.2017.04.012

mcpl.py written by Thomas Kittelmann, 2017-2022. The work was supported by the
European Union's Horizon 2020 research and innovation programme under grant
agreement No 676548 (the BrightnESS project)
"""

from __future__ import division, print_function, absolute_import,unicode_literals#enable py3 behaviour in py2.6+

try:
    _str = lambda s : s.encode('ascii') if (hasattr(s,'encode') and bytes==str) else s
except SyntaxError:
    print('MCPL ERROR: Unsupported obsolete Python detected')
    raise SystemExit(1)

__license__ = _str('CC0 1.0 Universal')
__copyright__ = _str('Copyright 2017-2022')
__version__ = _str('1.6.2')
__status__ = _str('Production')
__author__ = _str('Thomas Kittelmann')
__maintainer__ = _str('Thomas Kittelmann')
__email__ = _str('thomas.kittelmann@ess.eu')
__all__ = [_str('MCPLFile'),
           _str('MCPLParticle'),
           _str('MCPLParticleBlock'),
           _str('MCPLError'),
           _str('dump_file'),
           _str('convert2ascii'),
           _str('app_pymcpltool'),
           _str('collect_stats'),
           _str('dump_stats'),
           _str('plot_stats'),
           _str('main')]

#Python version checks and workarounds:

import sys,os
pyversion = sys.version_info[0:3]
_minpy2=(2,6,6)
_minpy3=(3,3,2)
if pyversion < _minpy2 or (pyversion >= (3,0,0) and pyversion < _minpy3):
    print(('MCPL WARNING: Unsupported python version %s detected (needs at least python2'
           +' v%s+ or python3 v%s+).')%('.'.join(str(i) for i in pyversion),
                                        '.'.join(str(i) for i in _minpy2),
                                        '.'.join(str(i) for i in _minpy3)))

#Enable more py3 like behaviour in py2:
__metaclass__ = type  #classes are new-style without inheriting from "object"

if pyversion < (3,0,0):
    range = xrange #in py3, range is py2's xrange

#For raw output of byte-array contents to stdout, without any troubles depending
#on encoding or python versions:
def _output_bytearray_raw(b):
    sys.stdout.flush()
    getattr(sys.stdout,'buffer',sys.stdout).write(b)
    sys.stdout.flush()

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
if not NumpyVersion is None:
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
    print("MCPL WARNING: Unsupported numpy version (%s) detected"%(str(np.__version__)))

np_dtype=np.dtype
try:
    np.dtype('f8')
except TypeError:
    np_dtype = lambda x : np.dtype(x.encode('ascii') if hasattr(x,'encode') else x)

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
        shapes = set(arr.shape for arr in arrays)
        if len(shapes) != 1:
            raise ValueError('all input arrays must have the same shape')
        result_ndim = arrays[0].ndim + 1
        if not -result_ndim <= axis < result_ndim:
            msg = 'axis {0} out of bounds [-{1}, {1})'.format(axis, result_ndim)
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

try:
    import pathlib as _pathlib
except ImportError:
    _pathlib = None

class MCPLError(Exception):
    """Common exception class for all exceptions raised by module"""
    pass

class MCPLParticle:
    """Object representing a single particle"""

    def __init__(self,block,idx):
        """For internal use only - users should not normally create MCPLParticle objects themselves"""
        self._b = block#can we make it a weak ref, to make sure multiple blocks are not kept around?
        self._i = idx
    @property
    def position(self):
        """position as 3-dimensional array [cm]"""
        return self._b.position[self._i]
    @property
    def direction(self):
        """normalised momentum direction as 3-dimensional array"""
        return self._b.direction[self._i]
    @property
    def polarisation(self):
        """polarisation vector as 3-dimensional array"""
        return self._b.polarisation[self._i]
    @property
    def x(self):
        """x-coordinate of position [cm]"""
        return self._b.x[self._i]
    @property
    def y(self):
        """y-coordinate of position [cm]"""
        return self._b.y[self._i]
    @property
    def z(self):
        """z-coordinate of position [cm]"""
        return self._b.z[self._i]
    @property
    def ux(self):
        """x-coordinate of normalised momentum direction"""
        return self._b.ux[self._i]
    @property
    def uy(self):
        """y-coordinate of normalised momentum direction"""
        return self._b.uy[self._i]
    @property
    def uz(self):
        """z-coordinate of normalised momentum direction"""
        return self._b.uz[self._i]
    @property
    def polx(self):
        """x-coordinate of polarisation vector"""
        return self._b.polx[self._i]
    @property
    def poly(self):
        """y-coordinate of polarisation vector"""
        return self._b.poly[self._i]
    @property
    def polz(self):
        """z-coordinate of polarisation vector"""
        return self._b.polz[self._i]
    @property
    def ekin(self):
        """kinetic energy [MeV]"""
        return self._b.ekin[self._i]
    @property
    def time(self):
        """time-stamp [millisecond]"""
        return self._b.time[self._i]
    @property
    def weight(self):
        """weight or intensity"""
        return self._b.weight[self._i]
    @property
    def userflags(self):
        """custom per-particle flags"""
        return self._b.userflags[self._i]
    @property
    def pdgcode(self):
        """MC particle number from the Particle Data Group (2112=neutron, 22=gamma, ...)"""
        return self._b.pdgcode[self._i]
    @property
    def file_index(self):
        """Particle position in file (counting from 0)"""
        return self._b._offset + self._i

class MCPLParticleBlock:
    """Object representing a block of particle. Fields are arrays rather than single
    numbers, but otherwise have the same meaning as on the MCPLParticle class."""

    def __init__(self,opt_polarisation,opt_userflags,opt_globalw,opt_globalpdg,fmtversion):
        """For internal use only - users should not normally create MCPLParticle objects themselves"""
        #empty block (set offset to max int to ensure d<0 in contains_ipos and get_by_global:
        self._offset = 9223372036854775807
        #non-constant columns (never the same in all blocks):
        self._data = tuple()
        #potentially constant columns (first entry says whether non-constant, second is cache):
        self._polx = [opt_polarisation,None]
        self._poly = [opt_polarisation,None]
        self._polz = [opt_polarisation,None]
        self._uf = [bool(opt_userflags),None]
        self._w = [not opt_globalw,None]
        self._pdg = [not opt_globalpdg,None]
        self._opt_globalw = opt_globalw
        self._opt_globalpdg = opt_globalpdg
        self._fmtversion = fmtversion
        self._view_pos = None
        self._view_pol = None
        self._view_dir = None
        self._pos_cache,self._pol_cache = None,None#extra ndarrays for numpy 1.14 issue

    def _set_data(self,data,file_offset):
        #always present, but must unpack:
        self._ux,self._uy,self._uz,self._ekin = None,None,None,None
        self._view_dir = None

        #reset non-constant columns:
        for ncc in [self._polx,self._poly,self._polz,self._uf,self._w,self._pdg]:
            if ncc[0]:
                ncc[1]=None
        self._view_pos = None
        if self._polx[0]:
            self._view_pol = None

        if data is None:
            self._offset = 9223372036854775807
            self._data = tuple()
        else:
            self._data = data
            self._offset = file_offset

    def contains_ipos(self,ipos):
        d=ipos-self._offset
        return d>=0 and d<len(self._data)

    def __getitem__(self,ipos):
        """Access single particle in block by local position in block (not global position in file)"""
        if ipos>=0 and ipos<len(self._data):
            return MCPLParticle(self,ipos)
        return None

    def get_by_global(self,ipos):
        """Access single particle in block by global position in file"""
        d = ipos - self._offset
        if d>=0 and d<len(self._data):
            return MCPLParticle(self,d)
        return None

    @property
    def particles(self):
        """Use to iterate over all particles in block:

           for p in theblock.particles:
               print p.x,p.y,p.z
        """
        for i in range(len(self._data)):
            yield self[i]

    def __len__(self):
        return len(self._data)

    @property
    def file_offset(self):
        """Particle position in file of first particle in block (counting from 0)"""
        return self._offset

    @property
    def polx(self):
        x = self._polx
        if x[0]:
            if x[1] is None:
                x[1] = self._data['polx'].astype(float)
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = np.zeros(len(self._data),dtype=float)
        return x[1]

    @property
    def poly(self):
        x = self._poly
        if x[0]:
            if x[1] is None:
                x[1] = self._data['poly'].astype(float)
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = np.zeros(len(self._data),dtype=float)
        return x[1]

    @property
    def polz(self):
        x = self._polz
        if x[0]:
            if x[1] is None:
                x[1] = self._data['polz'].astype(float)
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = np.zeros(len(self._data),dtype=float)
        return x[1]

    @property
    def pdgcode(self):
        x = self._pdg
        if x[0]:
            if x[1] is None:
                x[1] = self._data['pdg']
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = self._opt_globalpdg * np.ones(len(self._data),dtype=int)
        return x[1]

    @property
    def weight(self):
        x = self._w
        if x[0]:
            if x[1] is None:
                x[1] = self._data['w'].astype(float)
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = self._opt_globalw * np.ones(len(self._data),dtype=float)
        return x[1]

    @property
    def userflags(self):
        x = self._uf
        if x[0]:
            if x[1] is None:
                x[1] = self._data['uf']
            return x[1]
        if x[1] is None or len(x[1]) != len(self._data):
            x[1] = np.zeros(len(self._data),dtype=np.uint32)
        return x[1]

    @property
    def position(self):
        if self._view_pos is None:
            self._view_pos = np_stack((self.x,self.y,self.z),axis=1)
        return self._view_pos

    @property
    def polarisation(self):
        if self._view_pol is None or len(self._view_pol) != len(self._data):
            self._view_pol = np_stack((self.polx,self.poly,self.polz),axis=1)
        return self._view_pol

    @property
    def direction(self):
        if self._view_dir is None:
            if self._ux is None:
                self._unpack()
            self._view_dir = np_stack((self._ux,self._uy,self._uz),axis=1)
        return self._view_dir

    @property
    def x(self):
        return self._data['x']
    @property
    def y(self):
        return self._data['y']
    @property
    def z(self):
        return self._data['z']
    @property
    def time(self):
        return self._data['t']
    @property
    def ux(self):
        if self._ux is None:
            self._unpack()
        return self._ux
    @property
    def uy(self):
        if self._uy is None:
            self._unpack()
        return self._uy
    @property
    def uz(self):
        if self._uz is None:
            self._unpack()
        return self._uz
    @property
    def ekin(self):
        if self._ekin is None:
           self._ekin = abs(self._data['uve3']).astype(float)
        return self._ekin

    def _unpack(self):
        #On demand unpacking of unit vector. We have to make a version of
        #mcpl.c's mcpl_unitvect_unpack_adaptproj which can be efficiently
        #delegated to the compiled numpy library:
        if self._fmtversion==2:
            return self._unpack_legacy()#old packing scheme
        in0 = self._data['uve1'].astype(float)
        in1 = self._data['uve2'].astype(float)
        #NB: numpy 1.3 does not have copysign fct, only signbit:
        in2 = np.where(np.signbit(self._data['uve3']),-1.0,1.0)
        #reciprocals without zero division (fallback value will never be used):
        in0inv = 1.0/np.where(in0!=0.0,in0,1.0)
        in1inv = 1.0/np.where(in1!=0.0,in1,1.0)
        conda = (np.abs(in0)>1.0)
        condb = np.logical_and(np.logical_not(conda),(np.abs(in1)>1.0))
        #nb, reuse intermediate results below:
        in0sq = np.square(in0)
        in1sq = np.square(in1)
        self._ux = np.where(conda,
                            in2 * np.sqrt(np.clip(1.0-(in1sq+np.square(in0inv)),0.0,1.0)),
                            in0)
        self._uy = np.where(condb,
                            in2 * np.sqrt(np.clip(1.0-(in0sq+np.square(in1inv)),0.0,1.0)),
                            in1)
        self._uz = np.where(conda,
                            in0inv,
                            np.where(condb,
                                     in1inv,
                                     in2 * np.sqrt(np.clip(1.0-(in0sq+in1sq),0.0,1.0))))

    def _unpack_legacy(self):
        in0 = self._data['uve1'].astype(float)
        in1 = self._data['uve2'].astype(float)
        abs_in0 = np.abs(in0)
        abs_in1 = np.abs(in1)
        self._uz = (1.0 - abs_in0) - abs_in1
        zneg = ( self._uz < 0.0 )
        not_zneg = np.logical_not(zneg)
        self._ux = not_zneg * in0 + zneg * ( 1.0 - abs_in1 ) * np.where(in0 >= 0.0,1.0,-1.0)
        self._uy = not_zneg * in1 + zneg * ( 1.0 - abs_in0 ) * np.where(in1 >= 0.0,1.0,-1.0)
        n = 1.0 / np.sqrt(np.square(self._ux)+np.square(self._uy)+np.square(self._uz))
        self._ux *= n
        self._uy *= n
        self._uz *= n
        self._uz = np.where(np.signbit(self._data['uve3']),0.0,self._uz)

class MCPLFile:
    """Python-only class for reading MCPL files, using numpy and internal caches to
    ensure good efficiency. File access is read-only, and the particles can only
    be read in consecutive and forward order, providing either single particles or
    blocks of particles as requested."""

    def __init__(self,filename,blocklength = 10000, raw_strings = False):
        """Open indicated mcpl file, which can either be uncompressed (.mcpl) or
        compressed (.mcpl.gz). The blocklength parameter can be used to control
        the number of particles read by each call to read_block(). The parameter
        raw_strings has no effect in python2. In python3, it will prevent utf-8
        decoding of string data loaded from the file."""

        self._py3_str_decode = (not raw_strings) if (pyversion >= (3,0,0)) else False

        if hasattr(os,'fspath') and hasattr(filename,'__fspath__'):
            #python >= 3.6, work with all pathlike objects (including str and pathlib.Path):
            filename = os.fspath(filename)
        elif _pathlib and hasattr(_pathlib,'PurePath') and isinstance(filename,_pathlib.PurePath):
            #work with pathlib.Path in python 3.4 and 3.5:
            filename = str(filename)

        #prepare file i/o (opens file):
        self._open_file(filename)
        #load info from mcpl header:
        self._loadhdr()
        #Check if empty files are actually broken (like in mcpl.c):
        if self.nparticles==0:
            if filename.endswith('.gz'):
                #compressed - can only detect and raise error
                try:
                    test_read=self._fileread(dtype='u1',count=1)
                except ValueError:
                    test_read=[]
                if len(test_read)>0:
                    raise MCPLError("Input file appears to not have been closed properly"
                                    +" and data recovery is disabled for gzipped files.")
            else:
                #not compressed - can use file size to recover file
                np_rec = (int(os.stat(filename).st_size)-self.headersize) // self.particlesize
                if np_rec:
                    self._np = np_rec
                    self._hdr['nparticles'] = np_rec
                    print ("MCPL WARNING: Input file appears to not have been closed"
                           +" properly. Recovered %i particles."%np_rec)
        #prepare dtype for reading 1 particle:
        fp = 'f4' if self.opt_singleprec else 'f8'
        fields = []
        if self.opt_polarisation:
            fields += [('polx',fp),('poly',fp),('polz',fp)]
        fields += [('x',fp),('y',fp),('z',fp),
                   ('uve1',fp),('uve2',fp),('uve3',fp),#packed unit vector and ekin

        ('t',fp)]
        if not self.opt_universalweight:
            fields += [('w',fp)]
        if not self.opt_universalpdgcode:
            fields += [('pdg','i4')]
        if self.opt_userflags:
            fields += [('uf','u4')]
        fields = [(str(f[0]),str(f[1])) for f in fields]#workaround for https://github.com/numpy/numpy/issues/2407
        self._pdt = np_dtype(fields).newbyteorder(self.endianness)

        #Init position and caches (don't read first block yet):
        self._ipos = 0
        self._blocklength = int(blocklength)
        assert(self._blocklength>0)
        self._iblock = 0
        self._nblocks = self.nparticles // self._blocklength + (1 if self.nparticles%self._blocklength else 0)
        #reuse same block object for whole file (to reuse fixed columns and internal caches)
        self._currentblock = MCPLParticleBlock(self.opt_polarisation,self.opt_userflags,
                                               self.opt_universalweight,self.opt_universalpdgcode,self.version)

    @property
    def blocklength(self):
        """Number of particles read by each call to read_block()"""
        return self._blocklength

    def _open_file(self,filename):
        self._fileclose = lambda : None

        if not hasattr(filename,'endswith'):
            raise MCPLError('Unsupported type of filename object (should be path-like, a string or similar)')
        #Try to mimic checks and capabilities of mcpl.c as closely as possible
        #here (including the ability of gzopen to open uncompressed files),
        #which is why the slightly odd order of some checks below.

        try:
            fh = open(filename,'rb')
        except (IOError,OSError) as e:
            if e.errno == 2:
                fh = None#file not found
            else:
                raise
        if not fh:
            raise MCPLError('Unable to open file!')

        is_gz = False
        if filename.endswith('.gz'):
            is_gz = True
            try:
                import gzip
            except ImportError:
                raise MCPLError('can not open compressed files since gzip module is absent')
            try:
                if (fh.read(4)==b'MCPL'):
                    #This is actually not a gzipped file, mimic gzopen in mcpl.c by
                    #magically being able to open .mcpl files that are mistakenly named
                    #as .mcpl.gz
                    is_gz = False
            except (IOError, OSError, EOFError):
                pass
            fh.seek(0)

        can_use_np_fromfile = not _numpy_oldfromfile
        if is_gz:
            can_use_np_fromfile = False
            fh = gzip.GzipFile(fileobj=fh)
            if not fh:
                raise MCPLError('failed to open compressed file')

        if can_use_np_fromfile:
            #modern numpy and not gzipped input - read bytes by passing filehandle to np.fromfile
            self._fileread = lambda dtype,count : np.fromfile(fh,dtype=np_dtype(dtype),count=np.squeeze(count))
        else:
            #old numpy or gzipped input - read bytes via filehandle and use np.frombuffer to decode

            #list of exception types that might indicate read errors (TypeError
            #and struct.error are in the list due to bugs in the python 3.3 gzip
            #module):
            read_errors=[ IOError, OSError, EOFError, TypeError]
            try:
                import struct
                read_errors += [struct.error]
            except:
                pass
            read_errors = tuple(read_errors)
            def fread_via_buffer(dtype,count):
                dtype,count=np_dtype(dtype),np.squeeze(count)
                assert count>0
                n = dtype.itemsize * count
                try:
                    x = fh.read( n )
                except read_errors:
                    x = tuple()
                if len(x)==n: return np.frombuffer(x,dtype=dtype, count=count)
                else: return np.ndarray(dtype=dtype,shape=0)#incomplete read => return empty array
            self._fileread = fread_via_buffer
        self._fileseek = lambda pos : fh.seek(pos)
        self._fileclose = lambda : fh.close()

    #two methods needed for usage in with-statements:

    def __enter__(self):
        return self

    def __exit__(self, ttype, value, traceback):
        self._fileclose()

    def read_block(self):
        """Read and return next block of particles (None when EOF). Similar to read(),
        but returned \"particle\" object actually represents a whole block of
        particles, and the fields on it are thus (numpy) arrays of numbers
        rather than single numbers.  See also the particle_blocks property for
        an iterator-based access to blocks."""

        if self._iblock>=self._nblocks:
            return None
        #read next block:
        to_read = self._blocklength
        if self._iblock+1==self._nblocks and self._np%self._blocklength:
            to_read = self.nparticles%self._blocklength#last block is shorter
        x = self._fileread(dtype=self._pdt,count=to_read)
        if len(x)!=to_read:
            raise MCPLError('Errors encountered while attempting to read particle data.')
        self._currentblock._set_data(x,self._iblock*self._blocklength)
        self._iblock += 1
        return self._currentblock

    def read(self):
        """Read and return next particle in file (None when EOF) as a particle object,
        with particle state information available on fields as seen in the following
        example:

          p = mcplfile.read()
          if p is not None:
               print p.x,p.y,p.z
               print p.ux,p.uy,p.uz
               print p.polx,p.poly,p.polz
               print p.ekin,p.time,p.weight,p.userflags

        See also the particles property for an iterator-based access to
        particles. Furthermore, note that the read_blocks() function and
        the particle_blocks property provides block-based access, which can
        improve performance dramatically."""
        if self._ipos >= self._np:
            return None#end of file
        p = self._currentblock.get_by_global(self._ipos)
        if p is None:
            self.read_block()
            p = self._currentblock.get_by_global(self._ipos)
        self._ipos += 1
        return p

    def skip_forward(self,n):

        """skip n positions forward in file. (returns False when there is no
           particle at the new position, otherwise True)"""
        inew = self._ipos + int(n)
        if inew <= self._ipos:
            if inew == self._ipos:
                return self._ipos < self._np
            raise MCPLError("Requested skip is not in the forward direction")
        if self._currentblock.contains_ipos(inew):
            #handle case of small skip within currently loaded block first:
            self._ipos = inew
            return True
        if inew >= self._np:
            self._ipos = self.nparticles
            self._iblock = self._nblocks
            return False#EOF
        #skip to a given block:
        self._iblock = inew // self._blocklength
        assert self._iblock < self._nblocks#should not be eof
        blockstart = self.headersize+self._iblock*self._blocklength*self.particlesize
        assert blockstart > self._ipos#seek should be *forward*
        self._fileseek(blockstart)
        self._ipos = inew
        if not self.read_block():
            raise MCPLError('Unexpected failure to load particle block')
        return True

    @property
    def particles(self):
        """Use to iterate over all particles in file:

           for p in thefile.particles:
               print p.x,p.y,p.z
        """
        self.rewind()
        while True:
            p=self.read()
            if p is None:
                break
            yield p

    @property
    def particle_blocks(self):
        """Use to iterate over all particles in file, returning a block of
           particles each time for efficiency:

           for p in thefile.particle_blocks:
               print p.x,p.y,p.z #NB: the "values" here are actually arrays
        """
        self.rewind()
        while True:
            p=self.read_block()
            if p is None:
                break
            yield p

    def rewind(self):
        """Rewind file, causing next calls to read() and read_blocks() to start again at
        the beginning of the file."""
        self._fileseek(self.headersize)
        self._ipos = 0
        self._iblock = 0
        self._currentblock._set_data(None,None)

    @property
    def version(self):
        """MCPL format version of the file"""
        return self._hdr['version']
    @property
    def nparticles(self):
        """Number of particles in file"""
        return self._hdr['nparticles']
    @property
    def particlesize(self):
        """Uncompressed per-particle storage size in file [bytes]"""
        return self._hdr['particlesize']
    @property
    def headersize(self):
        """Uncompressed size of the file header [bytes]"""
        return self._hdr['headersize']
    @property
    def endianness(self):
        """Endianness of numbers in file"""
        return self._hdr['endianness']
    @property
    def opt_userflags(self):
        """Whether or not userflags are enabled in file"""
        return self._hdr['opt_userflags']
    @property
    def opt_universalpdgcode(self):
        """Global PDG code for all particles in file (a value of 0 means that
        PDG codes are stored per-particle)"""
        return self._hdr['opt_universalpdgcode']
    @property
    def opt_polarisation(self):
        """Whether or not polarisation info is enabled in file"""
        return self._hdr['opt_polarisation']
    @property
    def opt_singleprec(self):
        """Whether or not floating point numbers in particle data are stored in
        single-precision (32bit) rather than double-precision (64bit)"""
        return self._hdr['opt_singleprec']
    @property
    def opt_universalweight(self):
        """Global weight for all particles in file (a value of 0.0 means that
        weights are stored per-particle)"""
        return self._hdr['opt_universalweight']
    @property
    def sourcename(self):
        """Name of application that wrote the MCPL file"""
        return self._hdr['sourcename']
    @property
    def comments(self):
        """List of custom comments (strings) embedded in the file header"""
        return self._hdr['comments']
    @property
    def blobs(self):
        """Dictionary of custom binary blobs (byte-arrays) embedded in the file
        header. Each such blob is associated with a key, which is also the key
        in the dictionary"""
        return self._hdr['blobs']
    @property
    def blob_storage_order(self):
        """In-file storage order of binary blobs (as list of keys)."""
        return self._hdr['blobkeys']

    def _loadhdr(self):
        self._hdr={}
        h=self._hdr
        x=self._fileread(dtype='u1',count=8)
        if len(x)!=8 or not all(x[0:4]==(77,67,80,76)):
            raise MCPLError('File is not an MCPL file!')
        x=list(map(chr,x[4:]))
        version = int(''.join(x[0:3]))
        if not version in (2,3):
            raise MCPLError('File is in an unsupported MCPL version!')
        h['version']=version
        endianness = x[3]
        if not endianness in ('L','B'):
            raise MCPLError('Unexpected value in endianness field!')
        h['endianness']=endianness
        dt= np_dtype("u8,5u4,i4,2u4").newbyteorder(endianness)
        y = self._fileread(dtype=dt,count=1)
        if len(y)!=1:
            raise MCPLError('Invalid header')
        (nparticles,(ncomments,nblobs,opt_userflags,opt_polarisation,opt_singleprec),
         opt_universalpdgcode,(particlesize,_tmp)) = y[0]
        #convert all int types to python 'int' (which is 64bit), to avoid
        #conversions like int+np.uint64->float, and flags to bool:
        nparticles = int(nparticles)
        self._np = nparticles#needs frequent access
        particlesize = int(particlesize)
        opt_universalpdgcode = int(opt_universalpdgcode)
        opt_userflags = bool(opt_userflags)
        opt_polarisation = bool(opt_polarisation)
        opt_singleprec = bool(opt_singleprec)
        opt_universalweight = float(self._fileread(dtype=np_dtype('f8').newbyteorder(endianness),count=1)[0] if _tmp else 0.0)
        h['nparticles']=nparticles
        h['particlesize']=particlesize
        h['opt_universalpdgcode']=opt_universalpdgcode
        h['opt_userflags'] = opt_userflags
        h['opt_polarisation'] = opt_polarisation
        h['opt_singleprec'] = opt_singleprec
        h['opt_universalweight'] = opt_universalweight

        def readarr():
            l = self._fileread(dtype=np_dtype('u4').newbyteorder(endianness),count=1)
            if len(l)!=1:
                raise MCPLError('Invalid header')
            if l==0:
                return b''
            cont = self._fileread(dtype='u1',count=l)
            if len(cont)!=l:
                raise MCPLError('Invalid header')
            return cont.tobytes() if hasattr(cont,'tobytes') else cont.tostring()

        sourcename = readarr()
        comments=[]
        for i in range(ncomments):
            comments += [readarr()]
        blobs={}
        blobs_user={}
        blobkeys = []#to keep order available to dump_hdr
        for i in range(nblobs):
            blobkeys += [readarr()]
        for i,bk in enumerate(blobkeys):
            blobs[bk] = readarr()
        headersize = ( 48 + 4 + len(sourcename)
                       + (8 if opt_universalweight else 0)
                       + sum(4+len(c) for c in comments)
                       + sum(8+len(bk)+len(bv) for bk,bv in blobs.items()) )
        h['headersize'] = headersize
        if self._py3_str_decode:
            #attributes return python strings since raw_strings was not set, so
            #we must decode these before returning to the user. But for output
            #compatibility with the C-mcpltool, dump_hdr() will use original ones above.
            h['sourcename_raw'] = sourcename
            h['comments_raw'] = comments
            h['blobs_raw'] = blobs
            h['blobkeys_raw'] = blobkeys
            h['sourcename'] = sourcename.decode('utf-8','replace')
            h['comments'] = [c.decode('utf-8','replace') for c in comments]
            h['blobkeys'] = [bk.decode('utf-8','replace') for bk in blobkeys]
            h['blobs'] = dict((k.decode('utf-8','replace'),v) for k,v in blobs.items())
        else:
            #raw bytes all the way
            h['sourcename'] = sourcename
            h['comments'] = comments
            h['blobs'] = blobs
            h['blobkeys'] = blobkeys

    def dump_hdr(self):
        """Dump file header to stdout (using a format identical to the one from
        the compiled mcpltool)"""
        h=self._hdr
        def print_datastring(prefix,s,postfix):
            print(prefix,end='')
            _output_bytearray_raw(s)
            print(postfix)
        print("\n  Basic info")
        print("    Format             : MCPL-%i"%h['version'])
        print("    No. of particles   : %i"%h['nparticles'])
        print("    Header storage     : %i bytes"%h['headersize'])
        print("    Data storage       : %i bytes"%(h['nparticles']*h['particlesize']))
        print("\n  Custom meta data")
        print_datastring('    Source             : "',
                         h.get('sourcename_raw',None) or h.get('sourcename'),
                         '"')
        comments = h.get('comments_raw',None) or h.get('comments')
        print("    Number of comments : %i"%len(comments))
        for i,c in enumerate(comments):
            print_datastring('          -> comment %i : "'%i,c,'"')
        blobs = h.get('blobs_raw',None) or h.get('blobs')
        blobkeys = h.get('blobkeys_raw',None) or h.get('blobkeys')
        print("    Number of blobs    : %i"%len(h['blobs']))
        for bk in blobkeys:
            print_datastring('          -> %i bytes of data with key "'%len(blobs[bk]),bk,'"')
        print("\n  Particle data format")
        print("    User flags         : %s"%("yes" if h['opt_userflags'] else "no"))
        print("    Polarisation info  : %s"%("yes" if h['opt_polarisation'] else "no"))
        s = "    Fixed part. type   : "
        if h['opt_universalpdgcode']:
            s += "yes (pdgcode %i)"%h['opt_universalpdgcode']
        else:
            s += "no"
        print(s)
        s = "    Fixed part. weight : "
        if h['opt_universalweight']:
            s += "yes (weight %g)"%h['opt_universalweight']
        else:
            s += "no"
        print(s)
        print("    FP precision       : %s"%("single" if h['opt_singleprec'] else "double"))
        print("    Endianness         : %s"%({'L':'little','B':'big'}[h['endianness']]))
        print("    Storage            : %i bytes/particle"%h['particlesize'])
        print()

    def dump_particles(self,limit=10,skip=0):
        """Dump a list of particles to stdout (using a format identical to the one from
        the compiled mcpltool). The limit and skip parameters can be used to
        respectively limit the number of particles printed and to skip past
        particles at the head of the file. Use limit=0 to disable the limit."""

        #1) update position
        self.rewind()
        self.skip_forward(skip)

        #2) print column titles:
        opt_pol,opt_uf,opt_uw = self.opt_polarisation,self.opt_userflags,self.opt_universalweight
        s = "index     pdgcode   ekin[MeV]       x[cm]       y[cm]       z[cm]          ux          uy          uz    time[ms]"
        if not opt_uw:
            s += "      weight"
        if opt_pol:
            s += "       pol-x       pol-y       pol-z"
        if opt_uf:
            s += "  userflags"
        print(s)

        #3) loop and print
        fmt1 = "%5i %11i %11.5g %11.5g %11.5g %11.5g %11.5g %11.5g %11.5g %11.5g"
        fmt2 = " %11.5g %11.5g %11.5g"
        for i in range(limit if limit!=0 else self.nparticles):
            p = self.read()
            if p is None:
                break
            s = fmt1%( p.file_index,p.pdgcode,p.ekin,p.x,p.y,p.z,
                       p.ux,p.uy,p.uz,p.time )
            if not opt_uw:
                s += " %11.5g"%p.weight
            if opt_pol:
                s+=fmt2%( p.polx, p.poly, p.polz )
            if opt_uf:
                s+=" 0x%08x"%p.userflags
            print(s)

def dump_file(filename,header=True,particles=True,limit=10,skip=0,**kwargs):
    """Python equivalent of mcpl_dump(..) function from mcpl.h, which can be used to
    dump both header and particle contents of a file to stdout."""
    f = MCPLFile(filename,**kwargs)
    print("Opened MCPL file %s:"%os.path.basename(filename))
    if header:
        f.dump_hdr()
    if particles:
        f.dump_particles(limit=limit,skip=skip)

def convert2ascii(mcplfile,outfile):
    """Read particle contents of mcplfile and write into outfile using a simple ASCII-based format"""
    fin = mcplfile if isinstance(mcplfile,MCPLFile) else MCPLFile(mcplfile)
    fout = outfile if hasattr(outfile,'write') else open(outfile,'w')
    fout.write("#MCPL-ASCII\n#ASCII-FORMAT: v1\n#NPARTICLES: %i\n#END-HEADER\n"%fin.nparticles)
    fout.write("index     pdgcode               ekin[MeV]                   x[cm]          "
               +"         y[cm]                   z[cm]                      ux                  "
               +"    uy                      uz                time[ms]                  weight  "
               +"                 pol-x                   pol-y                   pol-z  userflags\n")
    fmtstr="%5i %11i %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g 0x%08x\n"
    for idx,p in enumerate(fin.particles):
        fout.write(fmtstr%(idx,p.pdgcode,p.ekin,p.x,p.y,p.z,p.ux,p.uy,p.uz,p.time,p.weight,p.polx,p.poly,p.polz,p.userflags))

def _pymcpltool_usage(progname,errmsg=None):
    if errmsg:
        print("ERROR: %s\n"%errmsg)
        print("Run with -h or --help for usage information")
        sys.exit(1)
    helpmsg = """
Tool for inspecting Monte Carlo Particle List (.mcpl) files.

The default behaviour is to display the contents of the FILE in human readable
format (see Dump Options below for how to modify what is displayed).

This is the read-only python version of the tool, and as such a lot of
functionality is missing compared to the compiled C version of the tool.

This installation supports direct reading of gzipped files (.mcpl.gz).

Usage:
  PROGNAME [dump-options] FILE
  PROGNAME --stats [stat-options] FILE
  PROGNAME --version
  PROGNAME --help

Dump options:
  By default include the info in the FILE header plus the first ten contained
  particles. Modify with the following options:
  -j, --justhead  : Dump just header info and no particle info.
  -n, --nohead    : Dump just particle info and no header info.
  -lN             : Dump up to N particles from the file (default 10). You
                    can specify -l0 to disable this limit.
  -sN             : Skip past the first N particles in the file (default 0).
  -bKEY           : Dump binary blob stored under KEY to standard output.

Stat options:
  --stats FILE    : Print statistics summary of particle state data from FILE.
  --stats --pdf FILE
                  : Produce PDF file mcpl.pdf with histograms of particle state
                    data from FILE.
  --stats --gui FILE
                  : Like --pdf, but opens interactive histogram views directly.

Other options:
  -t, --text MCPLFILE OUTFILE
                    Read particle contents of MCPLFILE and write into OUTFILE
                    using a simple ASCII-based format.
  -v, --version   : Display version of MCPL installation.
  -h, --help      : Display this usage information (ignores all other options).
"""
    print(helpmsg.strip().replace('PROGNAME',progname))
    sys.exit(0)

def app_pymcpltool(argv=None):
    """Implements a python equivalent of the compiled MCPL tool. If no argv list is
    passed in, sys.argv will be used. In case of errors, MCPLError exceptions
    are raised."""
    if argv is None:
        argv = sys.argv

    progname,args = os.path.basename(argv[0]),argv[1:]

    #NB: We do not use standard python parsing modules, since we want to be
    #as strictly compatible with the compiled mcpltool as possible.

    if not args:
        print('ERROR: No input file specified\n\nRun with -h or --help for usage information')
        sys.exit(1)
    opt_justhead = False
    opt_nohead = False
    opt_limit = None
    opt_skip = None
    opt_blobkey = None
    opt_version = False
    opt_text = False
    opt_stats = False
    opt_pdf = False
    opt_gui = False
    filelist = []
    def bad(errmsg):
        _pymcpltool_usage(progname,errmsg)
    for a in args:
        if a.startswith(str('--')):
            if a==str('--justhead'): opt_justhead=True
            elif a==str('--nohead'): opt_nohead=True
            elif a==str('--version'): opt_version=True
            elif a==str('--stats'): opt_stats=True
            elif a==str('--pdf'): opt_pdf=True
            elif a==str('--gui'): opt_gui=True
            elif a==str('--text'): opt_text=True
            elif a==str('--help'): _pymcpltool_usage(progname)
            else: bad(str("Unrecognised option : %s")%a)
        elif a.startswith(str('-')):
            a=a[1:]
            while a:
                f,a=a[0],a[1:]
                if f=='b':
                    if not opt_blobkey is None:
                        bad("-b specified more than once")
                    if not a:
                        bad("Missing argument for -b")
                    opt_blobkey,a = a,''
                elif f=='l' or f=='s':
                    if not a: bad("Bad option: missing number")
                    if not a.isdigit(): bad("Bad option: expected number")
                    if f=='l':
                        if not opt_limit is None:
                            bad("-l specified more than once")
                        opt_limit = int(a)
                    else:
                        assert f=='s'
                        if not opt_skip is None:
                            bad("-s specified more than once")
                        opt_skip = int(a)
                    a=''
                elif f=='j': opt_justhead=True
                elif f=='n': opt_nohead=True
                elif f=='v': opt_version=True
                elif f=='t': opt_text=True
                elif f=='h': _pymcpltool_usage(progname)
                else: bad("Unrecognised option : -%s"%f)
        else:
            filelist += [a]
    number_dumpopts = sum(1 for e in (opt_justhead,opt_nohead,opt_limit is not None,opt_skip is not None,opt_blobkey) if e)
    numper_statopts = sum(1 for e in (opt_stats,opt_pdf,opt_gui) if e)
    if sum(1 for e in (opt_version,opt_text,number_dumpopts,numper_statopts) if e)>1:
        bad('Conflicting options specified.')
    if number_dumpopts>1 and opt_blobkey:
        bad("Do not specify other dump options with -b.")
    if opt_pdf and not opt_stats:
        bad("Do not specify --pdf without --stats")
    if opt_gui and not opt_stats:
        bad("Do not specify --gui without --stats")
    if opt_gui and opt_pdf:
        bad("Do not specify both --pdf and --gui")

    if opt_version:
        if filelist:
            bad("Unrecognised arguments for --version.")
        print("MCPL version %s"%__version__)
        sys.exit(0)

    if opt_text:
        if len(filelist)>2:
            bad("Too many arguments.")
        if len(filelist)!=2:
            bad("Must specify both input and output files with --text.")
        if (os.path.exists(filelist[1])):
            bad("Requested output file already exists.")
        try:
            fout = open(filelist[1],'w')
        except (IOError,OSError) as e:
            fout = None
        if not fout:
            raise MCPLError('Could not open output file.')
        convert2ascii(filelist[0],fout)
        sys.exit(0)

    #Dump or stats:
    if len(filelist)>1:
        bad("Too many arguments.")
    if not filelist:
        bad("No input file specified")

    if opt_stats:
        f=MCPLFile(filelist[0])
        if f.nparticles==0:
            bad("Can not calculate statistics for an empty file")
        if opt_pdf or opt_gui:
            plot_stats(f,
                       pdf=('mcpl.pdf' if opt_pdf else False),
                       set_backend=('agg' if opt_pdf else None))
            if opt_pdf:
                print("Created mcpl.pdf")
        else:
            dump_stats(f)
        sys.exit(0)

    #Dump
    if opt_blobkey:
        with MCPLFile(filelist[0]) as f:
            thedata = f.blobs.get(opt_blobkey,None)
            if thedata is None and 'blobs_raw' in f._hdr:
                #Under LANG=C and python3, utf-8 keys might be in trouble:
                thedata = f._hdr['blobs_raw'].get(os.fsencode(opt_blobkey),None)
            if thedata is None:
                sys.exit(1)
            if sys.platform == "win32":
                import msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            _output_bytearray_raw(thedata)
            sys.exit(0)
    if (opt_limit is not None or opt_skip is not None) and opt_justhead:
        bad("Do not specify -l or -s with --justhead")
    if opt_limit is None:
        opt_limit = 10
    if opt_skip is None:
        opt_skip = 0
    if opt_justhead and opt_nohead:
        bad("Do not supply both --justhead and --nohead.")
    dump_file(filelist[0],header=not opt_nohead,particles=not opt_justhead,limit=opt_limit,skip=opt_skip)
    sys.exit(0)

_db_pdg = None
_db_elem = None
def _pdg_database(pdgcode):
    global _db_pdg, _db_elem
    if _db_pdg is None:
        _db_pdg = { 12:'nu_e',14:'nu_mu',16:'nu_tau',-12:'nu_e-bar',-14:'nu_mu-bar',
                    -16:'nu_tau-bar',2112:'n',2212:'p',-2112:'n-bar',-2212:'p-bar',
                    22:'gamma',11:'e-',-11:'e+',13:'mu-',-13:'mu+',15:'tau-',-15:'tau+',
                    211:'pi+',-211:'pi-',111:'pi0',321:'K+',-321:'K-',130:'Klong',
                    310:'Kshort',-1000010020:'D-bar',-1000010030:'T-bar',1000010020:'D',
                    1000010030:'T',1000020040:'alpha',-1000020040:'alpha-bar' }
    r=_db_pdg.get(pdgcode,None)
    if r is not None:
        return r
    if _db_elem is None:
        _db_elem = ['H',  'He', 'Li', 'Be', 'B',  'C',  'N',  'O',  'F',  'Ne',
                    'Na', 'Mg', 'Al', 'Si', 'P' , 'S',  'Cl', 'Ar', 'K',  'Ca', 'Sc',
                    'Ti', 'V',  'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge',
                    'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y',  'Zr', 'Nb', 'Mo', 'Tc',
                    'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I',  'Xe',
                    'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb',
                    'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W',  'Re', 'Os',
                    'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr',
                    'Ra', 'Ac', 'Th', 'Pa', 'U',  'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf',
                    'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt',
                    'Ds', 'Rg']
    if pdgcode>0 and pdgcode//100000000==10:
        I = pdgcode % 10
        pdgcode //= 10
        AAA = pdgcode%1000
        pdgcode //= 1000
        ZZZ = pdgcode%1000
        pdgcode //= 1000
        L = pdgcode % 10
        pdgcode //= 10
        if pdgcode==10 and ZZZ>0 and AAA>0:
            if L==0 and I==0 and ZZZ < len(_db_elem)+1:
                return '%s%i'%(_db_elem[ZZZ-1],AAA)
            s = 'ion(Z=%i,A=%i'%(ZZZ,AAA)
            if L:
                s += ',L=%i'%L
            if I:
                s += ',I=%i'%I
            s += ')'
            return s
    return None

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
            print("%s : %s"%(k.ljust(8),'%g'%self.__statcalc[k]() if self.__sumw>0.0 or k=='integral' else 'n/a'))

    def summarise(self):
        return ', '.join("%s=%s"%(k,'%g'%self.__statcalc[k]() if self.__sumw>0.0 or k=='integral' else 'n/a') for k in self.__dumporder)

    def __getitem__(self,a):
        return self.__statcalc[a]()

    def as_dict(self):
        return dict((k,self.__statcalc[k]()) for k in self.__statcalc.keys())

_possible_std_stats = ['ekin','x','y','z','ux','uy','uz','time','weight','polx','poly','polz']
_possible_freq_stats = ['pdgcode','userflags']

def collect_stats(mcplfile,stats=_str('all'),bin_data=True):
    """Efficiently collect statistics from an entire file (or part of file, if limit
    or skip parameters are set). Returns dictionary with stat names as key and
    the collected statistics as values."""

    #Normal stats (will be used weighted, except for stats about the weight field itself):
    possible_std_stats = set(_possible_std_stats)
    #Stats for which distributions are less likely to be relevant, so unique
    #values and their frequency will be returned instead:
    possible_freq_stats = set(_possible_freq_stats)

    if _str(stats)==_str('all'):
        stats = possible_std_stats.union(possible_freq_stats)

    if not isinstance(stats,set):
        stats = set(stats)

    if not isinstance(mcplfile,MCPLFile):
        mcplfile = MCPLFile(mcplfile)
    if mcplfile.nparticles==0:
        print("MCPL WARNING: Can not calculate stats on an empty file")
        return {}

    unknown = stats.difference(possible_std_stats.union(possible_freq_stats))
    if unknown:
        raise MCPLError('Unknown stat names requested: "%s"'%('","'.join(unknown)))

    #Some stats might be constant for all particles in the file:
    constant_stats_available = set()
    if mcplfile.opt_universalpdgcode: constant_stats_available.add('pdgcode')
    if not mcplfile.opt_userflags: constant_stats_available.add('userflags')
    if mcplfile.opt_universalweight: constant_stats_available.add('weight')
    if not mcplfile.opt_polarisation: constant_stats_available |= set(['polx','poly','polz'])
    cnst_stats = constant_stats_available.intersection(stats)
    stats = stats.difference(cnst_stats)

    std_stats = sorted(list(stats.difference(constant_stats_available).intersection(possible_std_stats)))
    freq_stats = sorted(list(stats.difference(constant_stats_available).intersection(possible_freq_stats)))

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
    freq_uc=dict((s,(np.asarray([],dtype=int),np.asarray([],dtype=float))) for s in freq_stats)
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
                    print("MCPL WARNING: Too many unique values in %s field. Disabling %s statistics"%(s,s))
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

    assert not weight_sum is None

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

    for s in list(k for k in freq_uc.keys()):
        #sort by frequency:
        u,c=freq_uc[s]
        sortidx=np.argsort(u,kind='mergesort')#the indices that would sort u
        u,c=u[sortidx],c[sortidx]
        sortidx=np.argsort(c,kind='mergesort')[::-1]#the indices that would sort c, viewed in reverse order
        freq_uc[s] = u[sortidx],c[sortidx]

    results = { 'file':{'type':'fileinfo','integral':weight_sum,'nparticles':mcplfile.nparticles} }
    for s,uc in freq_uc.items():
        results[s] = { 'unique_values': uc[0], 'unique_values_counts' : uc[1], 'weighted' : True, 'type':'freq' }

    units=dict(ekin='MeV',x='cm',y='cm',z='cm',time='ms')

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
                    'userflags':lambda x : '0x%08x'%x}

def dump_stats(stats):
    """Format and print provided statistics object to stdout. The stats object is
    assumed to have been created by a call to collect_stats()"""

    if not isinstance(stats,dict):
        stats = collect_stats(stats,bin_data=False)
    print('------------------------------------------------------------------------------')
    print('nparticles   : %i'%stats['file']['nparticles'])
    print('sum(weights) : %g'%stats['file']['integral'])
    if set(stats).intersection(_possible_std_stats):
        print('------------------------------------------------------------------------------')
        print('             :            mean             rms             min             max')
        print('------------------------------------------------------------------------------')

    for statname in _possible_std_stats:
        if not statname in stats:
            continue
        s=stats[statname]
        assert s['type']=='hist'
        su = '%s %s'%(statname.ljust(6),('[%s]'%s['unit']).rjust(5)) if s['unit'] else statname
        print('%s : %15g %15g %15g %15g'%(su.ljust(12),s['mean'],s['rms'],s['min'],s['max']))
    for statname in _possible_freq_stats:
        if not statname in stats:
            continue
        print('------------------------------------------------------------------------------')
        s=stats[statname]
        assert s['type']=='freq'
        fct_alt_descr = _freq_alt_descr.get(statname,lambda x: '')
        #fmt_fct = freq_formats_fcts[statname]
        uv,uvc=s['unique_values'],s['unique_values_counts'].copy()
        percents=uvc*(100.0/uvc.sum())
        showmax=50
        print ('%s : '%(statname.ljust(12)),end='')
        for i,(u,p,c) in enumerate(zip(uv,percents,uvc)):
            txt='%i'%u
            if i+1==showmax:
                txt='other'
                alttxt=''
                p=percents[i:].sum()
                c=uvc[i:].sum()
            else:
                alttxt=fct_alt_descr(u)
            print('%s %s %12g (%5.2f%%)'%(txt.rjust(26 if i else 11),
                                       ('(%s)'%alttxt if alttxt else '').ljust(12),
                                       c,p))
            if i+1==showmax:
                break
        print ('                     [ values ]             [ weighted counts ]')
    print('------------------------------------------------------------------------------')

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
        raise MCPLError('PDF file %s already exists'%(pdf))

    try:
        import matplotlib
    except ImportError:
        print()
        print("ERROR: For plotting, this MCPL python module requires matplotlib (matplotlib.org) to be")
        print("ERROR: installed. You can perhaps install it using using your software manager and searching")
        print("ERROR: for \"matplotlib\" or \"python-matplotlib\", or it might come bundled with software")
        print("ERROR: such as scientific python or anaconda, depending on your platform. Alternatively, if")
        print("ERROR: you are using the pip package manager, you might be able to install it with the")
        print("ERROR: command \"pip install matplotlib\".")
        print()
        raise

    if set_backend:
        matplotlib.use(set_backend)

    if pdf:
        try:
            from matplotlib.backends.backend_pdf import PdfPages
        except ImportError:
            print()
            print("ERROR: matplotlib installation does not have required support for PDF output.")
            print()
            raise
        pdf_file = pdf
        pdf = PdfPages(pdf)

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print()
        print("ERROR: importing matplotlib succeeded, but importing matplotlib.pyplot failed.")
        print("ERROR: This is rather unusual, an is perhaps related to issues with your chosen")
        print("ERROR: matplotlib backend, which you might have set globally in a matplotlib")
        print("ERROR: configuration file.")
        print()
        raise

    if not isinstance(stats,dict):
        stats = collect_stats(stats,bin_data=True)

    showmax=10
    for s in _possible_freq_stats:
        if not s in stats:
            continue
        freq=stats[s]
        u,c=freq['unique_values'],freq['unique_values_counts']
        fct_alt_descr = _freq_alt_descr.get(s,lambda x: None)
        def fmt_fct_raw(x):
            alttxt = fct_alt_descr(x)
            return '%s\n(%s)'%(str(x),alttxt) if alttxt is not None else str(x)
        #fmt_fct_raw = freq_formats_fcts[s]
        fmt_fct = lambda i,x: fmt_fct_raw(x)
        if len(c)>showmax:
            sum_other = c[showmax-1:].sum()
            u,c = u[0:showmax].copy(), c[0:showmax].copy()
            c[showmax-1] = sum_other
            fmt_fct = lambda i,x: 'other' if i==showmax-1 else fmt_fct_raw(x)
        percents = c.astype(float)*100.0/sum(c)
        labels = ['%s\n%.2f%%'%(fmt_fct(i,e),percents[i]) for i,e in enumerate(u)]
        barcenters=list(range(len(c)))
        rects = plt.bar(barcenters, c, width=0.7,align='center',linewidth=0)
        ax=plt.gca()
        ax.set_xticks(barcenters)
        percents=c.astype(float)*100.0/sum(c)
        ax.set_xticklabels(labels,fontsize='small')
        ax.yaxis.grid(True,color='white',linestyle='-')
        ax.set_xlim(-0.5,len(c)-0.5)
        plt.title(s)
        plt.subplots_adjust(left=0.1, right=0.94, top=0.93, bottom=0.13)
        if pdf:
            pdf.savefig(plt.gcf())
            plt.close()
        else:
            plt.show()

    for s in _possible_std_stats:
        if not s in stats:
            continue
        h=stats[s]
        hist,bins = h['hist'],h['hist_bins']
        plt.bar(0.5*(bins[:-1] + bins[1:]), hist, align='center', width=(bins[1] - bins[0]),linewidth=0)
        plt.grid()
        plt.title('%s%s (%s)'%(s,
                               ' [%s]'%h['unit'] if h['unit'] is not None else '',
                               'weighted' if h['weighted'] else 'unweighted'))
        plt.xlabel(h['summary'],fontsize='small')
        plt.xlim(bins[0],bins[-1])
        plt.subplots_adjust(left=0.1, right=0.94, top=0.93, bottom=0.13)
        if pdf:
            pdf.savefig(plt.gcf())
            plt.close()
        else:
            plt.show()

    if pdf:
        if hasattr(pdf,'infodict'):
            d = pdf.infodict()
            d['Title'] = 'Plots made with mcpl.py version %s'%__version__
            d['Author'] = 'mcpl.py v%s'%__version__
            d['Subject'] = 'mcpl plots'
            d['Keywords'] = 'mcpl'
        pdf.close()

def main():
    """This function simply calls app_pymcpltool(), but any raised MCPLError
    exception will be caught and transformed into a corresponding error message
    followed by a call to sys.exit(1). Invoking the mcpl.py module as a script
    (for instance with "python -m") will result in a call to this function."""
    try:
        app_pymcpltool()
    except MCPLError as e:
        print('MCPL ERROR: %s'%str(e))
        sys.exit(1)

if __name__=='__main__':
    main()
