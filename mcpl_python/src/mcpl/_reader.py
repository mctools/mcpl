
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

"""Reading of MCPL files."""

__all__ = ['MCPLFile']

import os

from ._blocks import MCPLParticleBlock
from ._common import MCPLError, _output_bytearray_raw
from ._messages import _warning
from ._numpy import _numpy_oldfromfile, np, np_dtype
from ._statsum import _parse_statsum, _parse_statsum_comment, encode_stat_sum


class MCPLFile:
    """Python-only class for reading MCPL files, using numpy and internal caches to
    ensure good efficiency. File access is read-only, and the particles can only
    be read in consecutive and forward order, providing either single particles or
    blocks of particles as requested."""

    def __del__(self):
        self._fileclose()
        self._fileclose = lambda : None

    def __init__(self,filename,blocklength = 10000, raw_strings = False,
                 _recover = True):
        """Open indicated mcpl file, which can either be uncompressed (.mcpl) or
        compressed (.mcpl.gz). The blocklength parameter can be used to control
        the number of particles read by each call to read_block(). The parameter
        raw_strings will prevent UTF-8 decoding of string data loaded from the
        file.
        """

        self._fileclose = lambda : None
        self._str_decode = (not raw_strings)

        if hasattr(filename,'__fspath__'):
            #work with all pathlike objects:
            filename = os.fspath(filename)
        else:
            if not isinstance(filename,bytes) and not isinstance(filename,str):
                raise MCPLError('Unsupported type of filename object'
                                ' (should be path-like, a string or similar)')

        #prepare file i/o (opens file):
        self._open_file(filename)
        #load info from mcpl header:
        self._loadhdr()
        #Check if empty files are actually broken (like in mcpl.c):
        if self.nparticles==0 and _recover:
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
                ndata = int(os.stat(filename).st_size)-self.headersize
                np_rec = ndata // self.particlesize
                if np_rec or ndata % self.particlesize:
                    self._np = np_rec
                    self._hdr['nparticles'] = np_rec
                    _warning("Input file appears to not have been closed"
                             f" properly. Recovered {np_rec} particles.")

                    comments = ( self._hdr.get('comments_raw')
                                 or self._hdr['comments'] )[:]
                    for ic in range(len(comments)):
                        c = comments[ic]
                        if not c.startswith(b'stat:sum:'):
                            continue
                        ok, (key,val) = _parse_statsum_comment( c)
                        if not ok:
                            raise MCPLError('Unexpected problems decoding'
                                            'stat:sum: comment second time')
                        if val != -1.0:
                            newc = encode_stat_sum( key, -1.0 ).encode('ascii')
                            if len(c) != len(newc):
                                raise MCPLError("Unexpected statsum encoding"
                                                " length")
                            comments[ic] = newc
                            _warning(f"Marking stat:sum:{key} "
                                     "entry as not available (-1) since file"
                                     " not closed properly.")
                    if 'comments_raw' in self._hdr:
                        self._hdr['comments_raw'] = comments
                        self._hdr['comments'] = [c.decode('utf-8','replace')
                                                 for c in comments]
                    else:
                        self._hdr['comments'] = comments
                    #Invalidate any already loaded stat sum dict:
                    if 'stat_sum' in self._hdr:
                        del self._hdr['stat_sum']

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
        assert isinstance(filename,(bytes,str))

        self._fileclose()
        self._fileclose = lambda : None

        #Try to mimic checks and capabilities of mcpl.c as closely as possible
        #here (including the ability of gzopen to open uncompressed files),
        #which is why the slightly odd order of some checks below.

        try:
            fh = open(filename,'rb')  # noqa: SIM115
        except OSError as e:
            if e.errno == 2:
                fh = None#file not found
            else:
                raise
        if not fh:
            raise MCPLError('Unable to open file!')

        self._fileclose()
        self._fileclose = lambda : fh.close()

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
            except (OSError, EOFError):
                pass
            fh.seek(0)

        self._is_gz = is_gz
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
            import struct
            if hasattr(struct,'error'):
                read_errors += [struct.error]
            read_errors = tuple(read_errors)
            def fread_via_buffer(dtype,count):
                dtype,count=np_dtype(dtype),np.squeeze(count)
                assert count>0
                n = dtype.itemsize * count
                try:
                    x = fh.read( n )
                except read_errors:
                    x = ()
                if len(x)==n:
                    return np.frombuffer(x,dtype=dtype, count=count)
                else:
                    return np.ndarray(dtype=dtype,shape=0)#incomplete read => return empty array
            self._fileread = fread_via_buffer
        self._fileseek = lambda pos : fh.seek(pos)

    #two methods needed for usage in with-statements:

    def __enter__(self):
        return self

    def __exit__(self, ttype, value, traceback):
        self._fileclose()
        self._fileclose = lambda : None

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

    @property
    def stat_sum(self):
        """Access "stat:sum:..." data from file comments as a convenient
        key->value dictionary. Note that any key present with a value of -1 in
        the file will get the value None here in the Python interface.
        """
        h = self._hdr
        d = h.get('stat_sum')
        if d is not None:
            return d
        from types import MappingProxyType  # read-only view of dict
        d = MappingProxyType(
            _parse_statsum( h.get('comments_raw',None) or h.get('comments') )
        )
        h['stat_sum'] = d
        return d

    def _loadhdr(self):
        self._hdr={}
        h=self._hdr
        x=self._fileread(dtype='u1',count=8)
        if len(x)!=8 or not all(x[0:4]==(77,67,80,76)):
            raise MCPLError('File is not an MCPL file!')
        x=list(map(chr,x[4:]))
        version = int(''.join(x[0:3]))
        if version not in (2,3):
            raise MCPLError('File is in an unsupported MCPL version!')
        h['version']=version
        endianness = x[3]
        if endianness not in ('L','B'):
            raise MCPLError('Unexpected value in endianness field!')
        h['endianness']=endianness
        dt= np_dtype("u8,5u4,i4,2u4").newbyteorder(endianness)
        y = self._fileread(dtype=dt,count=1)
        if len(y)!=1:
            raise MCPLError('Errors encountered while attempting to read header')
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
            ll = self._fileread(dtype=np_dtype('u4').newbyteorder(endianness),
                               count=1)
            if len(ll)!=1:
                raise MCPLError('Errors encountered while attempting to read header')
            if ll==0:
                return b''
            cont = self._fileread(dtype='u1',count=ll)
            if len(cont)!=ll:
                raise MCPLError('Errors encountered while attempting to read header')
            return cont.tobytes() if hasattr(cont,'tobytes') else cont.tostring()

        sourcename = readarr()
        comments=[]
        for i in range(ncomments):
            comments += [readarr()]
        blobs={}
        #blobs_user={}
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

        saw_any_statsum = False
        saw_any_unsupportedstat = False
        for c in comments:
            if not c.startswith(b'stat:'):
                continue
            if c.startswith(b'stat:sum:'):
                saw_any_statsum = True
            else:
                saw_any_unsupportedstat = True

        if self._str_decode:
            #attributes return python strings since raw_strings was not set, so
            #we must decode these before returning to the user. But for output
            #compatibility with the C-mcpltool, dump_hdr() will use original
            #ones above.
            h['sourcename_raw'] = sourcename
            h['comments_raw'] = comments
            h['blobs_raw'] = blobs
            h['blobkeys_raw'] = blobkeys
            h['sourcename'] = sourcename.decode('utf-8','replace')
            h['comments'] = [c.decode('utf-8','replace') for c in comments]
            h['blobkeys'] = [bk.decode('utf-8','replace') for bk in blobkeys]
            h['blobs'] = {k.decode('utf-8','replace'): v for k,v in blobs.items()}
        else:
            #raw bytes all the way
            h['sourcename'] = sourcename
            h['comments'] = comments
            h['blobs'] = blobs
            h['blobkeys'] = blobkeys

        if saw_any_statsum:
            #Trigger loading of stat:sum:'s already, to emit errors in case of
            #detected issues.
            _ = self.stat_sum
        if saw_any_unsupportedstat:
            _warning("Opened file with unknown \"stat:...\" "
                     "syntax in comments. The present installation only has"
                     " special support for \"stat:sum:...\" comments. It"
                     " might be a sign that your installation of MCPL is"
                     " too old.")

    def dump_hdr(self):
        """Dump file header to stdout (using a format identical to the one from
        the compiled mcpltool)"""
        h=self._hdr
        def print_datastring(prefix,s,postfix):
            print(prefix,end='')
            _output_bytearray_raw(s)
            print(postfix)
        print("\n  Basic info")
        print(f"    Format             : MCPL-{h['version']}")
        print(f"    No. of particles   : {h['nparticles']}")
        print(f"    Header storage     : {h['headersize']} bytes")
        print(f"    Data storage       : {h['nparticles']*h['particlesize']} bytes")
        print("\n  Custom meta data")
        print_datastring('    Source             : "',
                         h.get('sourcename_raw',None) or h.get('sourcename'),
                         '"')
        comments = h.get('comments_raw',None) or h.get('comments')
        print(f"    Number of comments : {len(comments)}")
        for i,c in enumerate(comments):
            print_datastring(f'          -> comment {i} : "',c,'"')
        blobs = h.get('blobs_raw',None) or h.get('blobs')
        blobkeys = h.get('blobkeys_raw',None) or h.get('blobkeys')
        print(f"    Number of blobs    : {len(h['blobs'])}")
        for bk in blobkeys:
            print_datastring(f'          -> {len(blobs[bk])} bytes of data with key "',bk,'"')
        print("\n  Particle data format")
        print("    User flags         : %s"%("yes" if h['opt_userflags'] else "no"))
        print("    Polarisation info  : %s"%("yes" if h['opt_polarisation'] else "no"))
        s = "    Fixed part. type   : "
        if h['opt_universalpdgcode']:
            s += f"yes (pdgcode {h['opt_universalpdgcode']})"
        else:
            s += "no"
        print(s)
        s = "    Fixed part. weight : "
        if h['opt_universalweight']:
            s += "yes (weight {:g})".format(h['opt_universalweight'])
        else:
            s += "no"
        print(s)
        print("    FP precision       : %s"%("single" if h['opt_singleprec'] else "double"))
        print("    Endianness         : {}".format({'L':'little','B':'big'}[h['endianness']]))
        print(f"    Storage            : {h['particlesize']} bytes/particle")
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
                s += f" {p.weight:11.5g}"
            if opt_pol:
                s+=fmt2%( p.polx, p.poly, p.polz )
            if opt_uf:
                s+=f" 0x{p.userflags:08x}"
            print(s)
