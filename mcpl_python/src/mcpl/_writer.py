
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


"""Writing of MCPL files."""

__all__ = ['MCPLOutFile', 'gzip_file']

import os

from ._blocks import MCPLParticle, MCPLParticleBlock
from ._common import MCPLError, _native_endianness
from ._messages import _error, _info, _warning
from ._numpy import np, np_dtype
from ._physics import ekin_from_wavelength
from ._reader import MCPLFile
from ._statsum import (
    _parse_statsum,
    _parse_statsum_comment,
    _statsum_syntax_error,
    encode_stat_sum,
)


class MCPLOutFile:
    """Python-only class for writing MCPL files, using numpy to process blocks of
    particles efficiently. The produced files are identical to those written by
    the C library (MCPL format version 3).

    The header is configured with methods named like the corresponding
    functions in the C API (hdr_set_srcname, hdr_add_comment, hdr_add_data,
    hdr_add_stat_sum, enable_userflags, enable_polarisation,
    enable_doubleprec, enable_universal_pdgcode, enable_universal_weight),
    and/or by passing keyword arguments to the constructor, named like the
    corresponding attributes of MCPLFile (sourcename, comments, blobs,
    stat_sum, opt_userflags, opt_polarisation, opt_singleprec,
    opt_universalpdgcode, opt_universalweight). The two can be mixed freely,
    since the keyword arguments are simply passed on to the methods. As in
    the C API, the header must be completely configured before the first
    particle is added, except for stat:sum values which can be updated until
    the file is closed (if a value was registered before the first particle,
    for instance the special value -1).

    Particles are added in blocks with add_particles(..), or one at a time
    with add_particle(..). The file must be closed with close() or
    closeandgzip(), which happens automatically (with close()) at the end of
    a with-statement:

       with MCPLOutFile('myfile.mcpl', sourcename='MySimulation',
                        opt_universalpdgcode=2112) as f:
           f.hdr_add_comment('Some comment')
           f.add_particles( position = pos, direction = dirs, ekin = ekin,
                            time = t, weight = w )

    Particles read from an existing file with MCPLFile (blocks or single
    particles) can be passed directly to add_particles(..) and
    add_particle(..), in which case the packed particle data is transferred
    exactly when possible (like mcpl_transfer_last_read_particle in the C
    API). The header settings of an existing file can be copied with
    transfer_metadata(..).
    """

    _fields_vector = ( ('position', ('x','y','z')),
                       ('direction', ('ux','uy','uz')),
                       ('polarisation', ('polx','poly','polz')) )
    _fields_scalar = ('ekin','wavelength','time','weight','pdgcode','userflags')
    _fields_all = frozenset( [ v for v,_ in _fields_vector ]
                             + [ c for _,cs in _fields_vector for c in cs ]
                             + list(_fields_scalar) )

    def __init__( self, filename, *, sourcename = None, comments = None,
                  blobs = None, stat_sum = None, opt_userflags = False,
                  opt_polarisation = False, opt_singleprec = True,
                  opt_universalpdgcode = 0, opt_universalweight = 0.0,
                  blocklength = 10000 ):
        """Create new file (overwriting any existing file). Like in the C API,
        ".mcpl" is appended to the filename if it does not already end with
        it. The keyword arguments correspond to calling the methods
        hdr_set_srcname, hdr_add_comment (for each comment), hdr_add_data (for
        each key,value in blobs), hdr_add_stat_sum (for each key,value in
        stat_sum), enable_userflags, enable_polarisation, enable_doubleprec
        (if opt_singleprec is False), enable_universal_pdgcode and
        enable_universal_weight. The blocklength parameter controls how many
        particles added with add_particle(..) are buffered before being
        written.
        """
        self._fh = None
        if hasattr(filename,'__fspath__'):
            filename = os.fspath(filename)
        if isinstance(filename,bytes):
            filename = filename.decode()
        if not isinstance(filename,str):
            raise MCPLError('Unsupported type of filename object'
                            ' (should be path-like, a string or similar)')
        if not filename:
            raise MCPLError('MCPLOutFile called with empty string.')
        if len(filename) > 4096:
            raise MCPLError('MCPLOutFile called with too long string.')
        lastdot = filename.rfind('.')
        if lastdot == 0 and len(filename) == 5:
            raise MCPLError('MCPLOutFile called with string with no'
                            ' basename part (".mcpl").')
        if lastdot == -1 or filename[lastdot:] != '.mcpl':
            filename += '.mcpl'
        self._filename = filename
        self._blocklength = int(blocklength)
        if self._blocklength < 1:
            raise MCPLError('blocklength must be at least 1')
        self._hdr_notwritten = True
        self._srcname = None
        self._comments = []
        self._blobkeys = []
        self._blobs = {}
        self._opt_userflags = False
        self._opt_polarisation = False
        self._opt_singleprec = True
        self._opt_universalpdgcode = 0
        self._opt_universalweight = 0.0
        self._nparticles = 0
        self._statsuminfo = {}#key -> [position of comment data in file, value]
        self._pending = []
        self._pdt = None
        self._fh = open(filename,'wb')  # noqa: SIM115
        if sourcename is not None:
            self.hdr_set_srcname(sourcename)
        for c in (comments or []):
            self.hdr_add_comment(c)
        for k,v in (blobs.items() if hasattr(blobs,'items') else (blobs or [])):
            self.hdr_add_data(k,v)
        for k,v in (stat_sum or {}).items():
            self.hdr_add_stat_sum(k,v)
        if opt_userflags:
            self.enable_userflags()
        if opt_polarisation:
            self.enable_polarisation()
        if not opt_singleprec:
            self.enable_doubleprec()
        if opt_universalpdgcode:
            self.enable_universal_pdgcode(opt_universalpdgcode)
        if opt_universalweight:
            self.enable_universal_weight(opt_universalweight)

    def __enter__(self):
        return self

    def __exit__(self, ttype, value, traceback):
        if self._fh is not None:
            self.close()

    def __del__(self):
        if getattr(self,'_fh',None) is not None:
            self.close()

    @property
    def filename(self):
        """Name of file being written to (might have had .mcpl appended)"""
        return self._filename

    @property
    def nparticles(self):
        """Number of particles added so far"""
        return self._nparticles + len(self._pending)

    @property
    def sourcename(self):
        """Name of the generating application (None if not set)"""
        return self._srcname

    @property
    def comments(self):
        """List of comments added so far (as bytes)"""
        return list(self._comments)

    @property
    def blobs(self):
        """Dictionary of binary blobs added so far (keys as bytes)"""
        return dict(self._blobs)

    @property
    def stat_sum(self):
        """Dictionary of stat:sum entries, like MCPLFile.stat_sum"""
        if self._hdr_notwritten:
            return _parse_statsum(self._comments)
        return { k : (None if v[1]==-1.0 else v[1])
                 for k,v in self._statsuminfo.items() }

    @property
    def opt_userflags(self):
        return self._opt_userflags

    @property
    def opt_polarisation(self):
        return self._opt_polarisation

    @property
    def opt_singleprec(self):
        return self._opt_singleprec

    @property
    def opt_universalpdgcode(self):
        """Universal pdgcode (0 if not set)"""
        return self._opt_universalpdgcode

    @property
    def opt_universalweight(self):
        """Universal weight (0.0 if not set)"""
        return self._opt_universalweight

    @property
    def particlesize(self):
        """Bytes per particle in the file"""
        fp = 4 if self._opt_singleprec else 8
        n = 7 * fp
        if self._opt_polarisation:
            n += 3 * fp
        if not self._opt_universalpdgcode:
            n += 4
        if not self._opt_universalweight:
            n += fp
        if self._opt_userflags:
            n += 4
        return n

    @staticmethod
    def _to_bytes(s, what):
        if isinstance(s,str):
            s = s.encode('utf-8')
        else:
            s = bytes(s)
        if b'\0' in s:
            raise MCPLError(f'{what} must not contain null characters.')
        return s

    def _check_open(self):
        if self._fh is None:
            raise MCPLError('Output file has already been closed.')

    def _check_hdr_notwritten(self,fctname):
        self._check_open()
        if not self._hdr_notwritten:
            raise MCPLError(f'{fctname} called too late.')

    def hdr_set_srcname(self, srcname):
        """Name of the generating application"""
        self._check_hdr_notwritten('hdr_set_srcname')
        self._srcname = self._to_bytes(srcname,'Source name')

    def hdr_add_comment(self, comment):
        """Add human-readable comment"""
        self._check_hdr_notwritten('hdr_add_comment')
        comment = self._to_bytes(comment,'Comments')
        if comment.startswith(b'stat:sum:'):
            ok, (key, _) = _parse_statsum_comment(comment)
            if not ok:
                raise MCPLError(_statsum_syntax_error(comment))
            if key in _parse_statsum(self._comments):
                raise MCPLError(f'Duplicate stat:sum: key. The key "{key}"'
                                ' appears more than once.')
        elif comment.startswith(b'stat:'):
            raise MCPLError('Refusing to create file with comments starting'
                            ' with "stat:" unless starting with "stat:sum:",'
                            ' as such syntax is reserved for future usage.')
        self._comments.append(comment)

    def hdr_add_data(self, key, data):
        """Add binary blob (bytes-like object) by key"""
        self._check_hdr_notwritten('hdr_add_data')
        key = self._to_bytes(key,'Blob keys')
        if key in self._blobs:
            raise MCPLError('hdr_add_data got duplicate key')
        data = bytes(data)
        if len(data) >= 4294967295:
            raise MCPLError('hdr_add_data got too large data')
        self._blobkeys.append(key)
        self._blobs[key] = data

    def enable_userflags(self):
        """Write the userflags info"""
        if self._opt_userflags:
            return
        self._check_hdr_notwritten('enable_userflags')
        self._opt_userflags = True

    def enable_polarisation(self):
        """Write the polarisation info"""
        if self._opt_polarisation:
            return
        self._check_hdr_notwritten('enable_polarisation')
        self._opt_polarisation = True

    def enable_doubleprec(self):
        """Use double precision floating point numbers in storage"""
        if not self._opt_singleprec:
            return
        self._check_hdr_notwritten('enable_doubleprec')
        self._opt_singleprec = False

    def enable_universal_pdgcode(self, pdgcode):
        """All particles are of the same type"""
        pdgcode = int(pdgcode)
        if pdgcode == 0:
            raise MCPLError('enable_universal_pdgcode must be called with'
                            ' non-zero pdgcode.')
        if not ( -2147483648 <= pdgcode <= 2147483647 ):
            raise MCPLError('enable_universal_pdgcode must be called with'
                            ' a 32 bit integer.')
        if self._opt_universalpdgcode:
            if self._opt_universalpdgcode != pdgcode:
                raise MCPLError('enable_universal_pdgcode called multiple times')
            return
        self._check_hdr_notwritten('enable_universal_pdgcode')
        self._opt_universalpdgcode = pdgcode

    def enable_universal_weight(self, weight):
        """All particles have the same weight"""
        import math
        weight = float(weight)
        if weight <= 0.0 or math.isinf(weight) or math.isnan(weight):
            raise MCPLError('enable_universal_weight must be called with'
                            ' positive but finite weight.')
        if self._opt_universalweight:
            if self._opt_universalweight != weight:
                raise MCPLError('enable_universal_weight called multiple times')
            return
        self._check_hdr_notwritten('enable_universal_weight')
        self._opt_universalweight = weight

    def hdr_add_stat_sum(self, key, value):
        """Add or update named statistics "sum", encoded in a special comment
        (see the C API for details). Use value=-1 (or None) to register a
        value which will be updated later (at the latest before closing the
        file)."""
        self._check_open()
        comment = encode_stat_sum(key,value).encode('ascii')
        if hasattr(key,'decode'):
            key = key.decode('ascii')
        value = -1.0 if value is None else float(value)
        if self._hdr_notwritten:
            for i,c in enumerate(self._comments):
                if c.startswith(b'stat:sum:') and _parse_statsum_comment(c)[1][0] == key:
                    self._comments[i] = comment
                    return
            self.hdr_add_comment(comment)
            return
        if key not in self._statsuminfo:
            raise MCPLError('hdr_add_stat_sum called after first particle was'
                            ' added to file, but without first registering a'
                            ' value for the same key earlier (the special'
                            ' value -1 can be used for this)')
        self._update_statsum_on_disk(key,comment,value)

    def hdr_scale_stat_sums(self, scale):
        """Scale all stat:sum values with a given factor which must be a finite
        number >0.0 or -1 (see the C API for details)."""
        import math
        scale = float(scale)
        if math.isnan(scale):
            raise MCPLError('hdr_scale_stat_sums called with NaN (not-a-number) scale')
        if scale < 0.0 and scale != -1.0:
            raise MCPLError('hdr_scale_stat_sums called with negative scale')
        if math.isinf(scale):
            raise MCPLError('hdr_scale_stat_sums called with infinite scale')
        if scale == 0.0:
            raise MCPLError('hdr_scale_stat_sums called with zero scale')
        self._check_open()
        if self._hdr_notwritten:
            items = [ (k,(-1.0 if v is None else v))
                      for k,v in _parse_statsum(self._comments).items() ]
        else:
            items = [ (k,v[1]) for k,v in self._statsuminfo.items() ]
        any_inf = False
        for key, value in items:
            new_value = -1.0 if ( scale == -1.0 or value == -1.0 ) else value * scale
            if math.isinf(new_value):
                any_inf = True
                new_value = -1.0
            if new_value != value:
                self.hdr_add_stat_sum(key,new_value)
        if any_inf:
            _warning('The call to hdr_scale_stat_sums resulted in'
                     ' one or more stat:sum: entries overflowing floating point'
                     ' range and producing infinity. Reverting value to -1'
                     ' to indicate that a precise result is not available.')

    def transfer_metadata(self, source):
        """Transfer all settings, blobs and comments from an MCPLFile object (or
        the file with the given name). Note that if splitting files rather
        than filtering them, hdr_scale_stat_sums should be called afterwards
        (see the C API for details)."""
        if not isinstance(source,MCPLFile):
            with MCPLFile(source) as f:
                return self.transfer_metadata(f)
        h = source._hdr
        if source.endianness != _native_endianness():
            raise MCPLError('transfer_metadata can only work on files with'
                            ' same endianness as current platform.')
        self.hdr_set_srcname(h.get('sourcename_raw',h['sourcename']))
        for c in h.get('comments_raw',h['comments']):
            self.hdr_add_comment(c)
        blobs = h.get('blobs_raw',h['blobs'])
        for k in h.get('blobkeys_raw',h['blobkeys']):
            self.hdr_add_data(k,blobs[k])
        if source.opt_userflags:
            self.enable_userflags()
        if source.opt_polarisation:
            self.enable_polarisation()
        if not source.opt_singleprec:
            self.enable_doubleprec()
        if source.opt_universalpdgcode:
            self.enable_universal_pdgcode(source.opt_universalpdgcode)
        if source.opt_universalweight:
            self.enable_universal_weight(source.opt_universalweight)

    def _particle_dtype(self):
        if self._pdt is None:
            fp = 'f4' if self._opt_singleprec else 'f8'
            fields = []
            if self._opt_polarisation:
                fields += [('polx',fp),('poly',fp),('polz',fp)]
            fields += [('x',fp),('y',fp),('z',fp),
                       ('uve1',fp),('uve2',fp),('uve3',fp),
                       ('t',fp)]
            if not self._opt_universalweight:
                fields += [('w',fp)]
            if not self._opt_universalpdgcode:
                fields += [('pdg','i4')]
            if self._opt_userflags:
                fields += [('uf','u4')]
            self._pdt = np_dtype(fields)
            assert self._pdt.itemsize == self.particlesize
        return self._pdt

    def _write_header(self):
        import struct
        assert self._hdr_notwritten
        out = bytearray()
        out += b'MCPL003' + _native_endianness().encode('ascii')
        out += struct.pack('=Q',0)
        out += struct.pack('=8I',
                           len(self._comments),
                           len(self._blobkeys),
                           int(self._opt_userflags),
                           int(self._opt_polarisation),
                           int(self._opt_singleprec),
                           self._opt_universalpdgcode & 0xFFFFFFFF,
                           self.particlesize,
                           1 if self._opt_universalweight else 0)
        if self._opt_universalweight:
            out += struct.pack('=d',self._opt_universalweight)
        def add_buffer(b):
            nonlocal out
            out += struct.pack('=I',len(b))
            pos = len(out)
            out += b
            return pos
        add_buffer(self._srcname if self._srcname is not None else b'unknown')
        statsuminfo = {}
        for c in self._comments:
            pos = add_buffer(c)
            if c.startswith(b'stat:sum:'):
                key, value = _parse_statsum_comment(c)[1]
                statsuminfo[key] = [pos,-1.0 if value is None else value]
        for k in self._blobkeys:
            add_buffer(k)
        for k in self._blobkeys:
            add_buffer(self._blobs[k])
        self._fh.write(out)
        self._fh.flush()
        self._statsuminfo = statsuminfo
        self._hdr_notwritten = False
        self._particle_dtype()

    def _update_statsum_on_disk(self, key, comment, value):
        pos = self._statsuminfo[key][0]
        self._fh.flush()
        savedpos = self._fh.tell()
        self._fh.seek(pos)
        self._fh.write(comment)
        self._fh.seek(savedpos)
        self._statsuminfo[key][1] = value

    def _write_records(self, arr):
        if self._hdr_notwritten:
            self._write_header()
        if len(arr):
            self._fh.write(arr.tobytes())
            self._nparticles += len(arr)

    def _flush_pending(self):
        if not self._pending:
            return
        pending, self._pending = self._pending, []
        cols = list(zip(*pending))
        self._write_records( self._pack( len(pending),
                                         dict(zip(self._pending_keys,cols)),
                                         validate = False ) )

    _pending_keys = ('x','y','z','ux','uy','uz','polx','poly','polz',
                     'ekin','time','weight','pdgcode','userflags')

    def _collect_fields(self, fields):
        unknown = set(fields) - MCPLOutFile._fields_all
        if unknown:
            raise TypeError('Unknown particle field(s): '
                            + ', '.join(sorted(unknown)))
        cols = {}
        for vecname, compnames in MCPLOutFile._fields_vector:
            if vecname in fields:
                if any( c in fields for c in compnames ):
                    raise MCPLError(f'Do not specify both {vecname} and any'
                                    ' of ' + ', '.join(compnames))
                v = np.asarray(fields[vecname],dtype=float)
                if v.shape[-1:] != (3,) or v.ndim > 2:
                    raise MCPLError(f'{vecname} must have shape (3,) or (N,3)')
                for i,c in enumerate(compnames):
                    cols[c] = v[...,i]
            else:
                for c in compnames:
                    if c in fields:
                        cols[c] = np.asarray(fields[c],dtype=float)
        for c in ('ekin','wavelength','time','weight'):
            if c in fields:
                cols[c] = np.asarray(fields[c],dtype=float)
        for c,lo,hi in (('pdgcode',-2147483648,2147483647),
                        ('userflags',0,4294967295)):
            if c in fields:
                v = np.asarray(fields[c])
                if v.dtype.kind not in 'iub':
                    vi = v.astype(np.int64)
                    if not np.array_equal(vi,v):
                        raise MCPLError(f'{c} must be integers')
                    v = vi
                if v.size and ( v.min() < lo or v.max() > hi ):
                    raise MCPLError(f'{c} out of range')
                cols[c] = v.astype(np.int64)
        for c,v in cols.items():
            if v.ndim > 1:
                raise MCPLError(f'{c} must be a scalar or a 1D array')
        lengths = { len(v) for v in cols.values() if v.ndim == 1 }
        lengths.discard(1)
        if len(lengths) > 1:
            raise MCPLError('Inconsistent lengths of particle field arrays')
        return cols, (lengths.pop() if lengths else 1)

    def _pack(self, n, cols, validate = True, packed_ekindir = None):
        """Serialise particle data (dictionary of scalars or arrays of length n)
        into structured array, exactly like the C library."""
        def col(name,default=0.0):
            v = cols.get(name)
            if v is None:
                return np.full(n,default)
            return np.broadcast_to(np.asarray(v,dtype=float),(n,))
        ux, uy, uz = col('ux'), col('uy'), col('uz')
        ekin = col('ekin')
        if validate:
            dirsq = ux * ux + uy * uy + uz * uz
            if np.any( np.abs( dirsq - 1.0 ) > 1.0e-5 ):
                raise MCPLError('attempting to add particle with non-unit'
                                ' direction vector')
            if np.any( ekin < 0.0 ):
                raise MCPLError('attempting to add particle with negative'
                                ' kinetic energy')
        arr = np.empty(n,dtype=self._particle_dtype())
        if packed_ekindir is not None:
            arr['uve1'], arr['uve2'], arr['uve3'] = packed_ekindir
        else:
            #Adaptive Projection Packing (see mcpl_unitvect_pack_adaptproj):
            absx, absy = np.abs(ux), np.abs(uy)
            project = np.abs(uz) < np.fmax(absx,absy)
            with np.errstate(divide='ignore'):
                invz = np.where(uz != 0.0, 1.0 / np.where(uz != 0.0, uz, 1.0), np.inf)
            proj_x = project & (absx >= absy)
            proj_y = project & ~(absx >= absy)
            arr['uve1'] = np.where(proj_x, invz, ux)
            arr['uve2'] = np.where(proj_y, invz, uy)
            arr['uve3'] = np.copysign( ekin,
                                       np.where(proj_x, ux,
                                                np.where(proj_y, uy, uz)) )
        if self._opt_polarisation:
            arr['polx'], arr['poly'], arr['polz'] = col('polx'), col('poly'), col('polz')
        arr['x'], arr['y'], arr['z'] = col('x'), col('y'), col('z')
        arr['t'] = col('time')
        if not self._opt_universalweight:
            arr['w'] = col('weight')
        if not self._opt_universalpdgcode:
            v = cols.get('pdgcode')
            arr['pdg'] = 0 if v is None else np.broadcast_to(v,(n,))
        if self._opt_userflags:
            v = cols.get('userflags')
            arr['uf'] = 0 if v is None else np.broadcast_to(v,(n,))
        return arr

    def add_particles(self, particles = None, **fields):
        """Add block of particles. Particle data is specified with keyword
        arguments using the field names of MCPLParticleBlock: position (as
        array with shape (N,3)) or x, y, z; direction or ux, uy, uz;
        polarisation or polx, poly, polz; ekin, time, weight, pdgcode,
        userflags. Values can be numpy arrays of length N or scalars (which
        apply to all particles), and missing fields default to 0. Like in the
        C API, fields not enabled in the file are ignored (e.g. polarisation
        unless enable_polarisation() was called) as are the weight and
        pdgcode fields in files with universal weight or pdgcode.

        Instead of ekin, the wavelength [Aa] can be specified for neutrons and
        gammas.

        Alternatively, an MCPLParticleBlock (or an MCPLParticle) read with
        MCPLFile can be passed, in which case its packed data is transferred
        exactly whenever possible. Combined with keyword arguments, the given
        fields replace those of the passed particles (e.g. to edit positions
        or weights), for instance: f.add_particles( block, weight = 2 *
        block.weight ).
        """
        self._check_open()
        if particles is not None:
            if isinstance(particles,MCPLParticle):
                b, sel = particles._b, slice(particles._i,particles._i+1)
            elif isinstance(particles,MCPLParticleBlock):
                b, sel = particles, slice(None)
            else:
                raise MCPLError('Unsupported type of particles object (should'
                                ' be MCPLParticleBlock or MCPLParticle)')
            self._transfer(b,sel,fields)
            return
        cols, n = self._collect_fields(fields)
        self._resolve_wavelength(cols, cols.get('pdgcode'))
        if self._hdr_notwritten:
            self._write_header()
        arr = self._pack(n,cols)
        self._flush_pending()
        self._write_records(arr)

    def add_particle(self, particle = None, **fields):
        """Add single particle. Takes the same arguments as add_particles(..),
        but with scalar values (or vectors of length 3), or a single
        MCPLParticle read with MCPLFile. Particles are internally buffered and
        written in blocks for efficiency."""
        self._check_open()
        if particle is not None:
            if fields:
                raise MCPLError('Do not specify particle fields together with'
                                ' a particle object')
            if not isinstance(particle,MCPLParticle):
                raise MCPLError('Unsupported type of particle object (should'
                                ' be MCPLParticle)')
            self.add_particles(particle)
            return
        if self._hdr_notwritten:
            self._write_header()
        unknown = set(fields) - MCPLOutFile._fields_all
        if unknown:
            raise TypeError('Unknown particle field(s): '
                            + ', '.join(sorted(unknown)))
        vals = []
        for vecname, compnames in MCPLOutFile._fields_vector:
            if vecname in fields:
                if any( c in fields for c in compnames ):
                    raise MCPLError(f'Do not specify both {vecname} and any'
                                    ' of ' + ', '.join(compnames))
                v = fields[vecname]
                if len(v) != 3:
                    raise MCPLError(f'{vecname} must have length 3')
                vals += [ float(v[0]), float(v[1]), float(v[2]) ]
            else:
                vals += [ float(fields.get(c,0.0)) for c in compnames ]
        pdgcode = int(fields.get('pdgcode',0))
        if 'wavelength' in fields:
            cols = { 'wavelength' : float(fields['wavelength']) }
            if 'ekin' in fields:
                cols['ekin'] = fields['ekin']
            self._resolve_wavelength(cols, pdgcode if 'pdgcode' in fields else None)
            ekin = float(cols['ekin'])
        else:
            ekin = float(fields.get('ekin',0.0))
        dirsq = vals[3] * vals[3] + vals[4] * vals[4] + vals[5] * vals[5]
        if abs( dirsq - 1.0 ) > 1.0e-5:
            raise MCPLError('attempting to add particle with non-unit'
                            ' direction vector')
        if ekin < 0.0:
            raise MCPLError('attempting to add particle with negative'
                            ' kinetic energy')
        userflags = int(fields.get('userflags',0))
        if not ( -2147483648 <= pdgcode <= 2147483647 ):
            raise MCPLError('pdgcode out of range')
        if not ( 0 <= userflags <= 4294967295 ):
            raise MCPLError('userflags out of range')
        vals += [ ekin, float(fields.get('time',0.0)),
                  float(fields.get('weight',0.0)), pdgcode, userflags ]
        self._pending.append(vals)
        if len(self._pending) >= self._blocklength:
            self._flush_pending()

    def _resolve_wavelength(self, cols, pdgcode):
        if 'wavelength' not in cols:
            return
        if 'ekin' in cols:
            raise MCPLError('Do not specify both ekin and wavelength')
        if pdgcode is None:
            pdgcode = self._opt_universalpdgcode
        if not np.all( np.isin( pdgcode, (2112,22) ) ):
            raise MCPLError('wavelength can only be specified for neutrons'
                            ' (pdgcode 2112) and gammas (pdgcode 22)')
        cols['ekin'] = ekin_from_wavelength( cols.pop('wavelength'), pdgcode )

    def _transfer(self, block, sel, overrides = None):
        data = block._data[sel]
        n = len(data)
        if not n:
            return
        ocols = {}
        if overrides:
            ocols, no = self._collect_fields(overrides)
            if no not in (1,n):
                raise MCPLError('Inconsistent lengths of particle field arrays')
            ocols = { k : np.broadcast_to(v,(n,)) for k,v in ocols.items() }
        if self._hdr_notwritten:
            self._write_header()
        pdgcode = ocols['pdgcode'] if 'pdgcode' in ocols else block.pdgcode[sel]
        weight = ocols['weight'] if 'weight' in ocols else block.weight[sel]
        self._resolve_wavelength(ocols, pdgcode)
        if self._opt_universalpdgcode and np.any( pdgcode != self._opt_universalpdgcode ):
            bad = pdgcode[ pdgcode != self._opt_universalpdgcode ][0]
            raise MCPLError(f'add_particles asked to transfer particle with pdgcode {bad}'
                            ' into a file with universal pdgcode of'
                            f' {self._opt_universalpdgcode}')
        if self._opt_universalweight and np.any( weight != self._opt_universalweight ):
            bad = weight[ weight != self._opt_universalweight ][0]
            raise MCPLError(f'add_particles asked to transfer particle with weight {bad:g}'
                            ' into a file with universal weight of'
                            f' {self._opt_universalweight:g}')
        src_singleprec = ( data.dtype['x'].itemsize == 4 )
        if not ocols and block._fmtversion != 2 and data.dtype == self._particle_dtype():
            #Particle data is encoded in exactly the same manner in source and
            #target, so simply transfer the bytes:
            arr = data
        else:
            cols = { 'x' : block.x[sel], 'y' : block.y[sel], 'z' : block.z[sel],
                     'ux' : block.ux[sel], 'uy' : block.uy[sel], 'uz' : block.uz[sel],
                     'polx' : block.polx[sel], 'poly' : block.poly[sel],
                     'polz' : block.polz[sel], 'ekin' : block.ekin[sel],
                     'time' : block.time[sel], 'weight' : weight,
                     'pdgcode' : pdgcode, 'userflags' : block.userflags[sel] }
            cols.update(ocols)
            packed = None
            if ( block._fmtversion != 2 and ( self._opt_singleprec or not src_singleprec )
                 and not set(ocols).intersection(('ux','uy','uz','ekin')) ):
                #Reuse packed ekin+direction from the source, to avoid
                #potentially lossy unpacking+packing:
                packed = ( data['uve1'], data['uve2'], data['uve3'] )
            arr = self._pack(n,cols,packed_ekindir = packed)
        self._flush_pending()
        self._write_records(arr)

    def close(self):
        """Close the file (writing all pending particles and updating the
        header)."""
        if self._fh is None:
            return
        try:
            self._flush_pending()
            if self._hdr_notwritten:
                self._write_header()
            if self._nparticles:
                import struct
                self._fh.seek(8)
                self._fh.write(struct.pack('=Q',self._nparticles))
        finally:
            fh, self._fh = self._fh, None
            fh.close()

    def closeandgzip(self):
        """Close the file and gzip it (which will append .gz to the filename).
        Returns True if gzipping was successful."""
        self.close()
        return gzip_file(self._filename)

def gzip_file(filename):
    """Compress file with gzip, replacing it with a file with .gz appended to its
    name (like mcpl_gzip_file in the C API). Returns True if successful."""
    import gzip
    import pathlib
    import shutil
    f = pathlib.Path(filename)
    bn = f.name
    _info(f'Compressing file {bn}')
    try:
        with f.open('rb') as fi, gzip.open(f.parent / (bn + '.gz'),'wb') as fo:
            shutil.copyfileobj(fi, fo)
        f.unlink()
    except OSError:
        _error(f'Problems encountered while compressing file {bn}.')
        return False
    _info(f'Compressed file into {bn}.gz')
    return True
