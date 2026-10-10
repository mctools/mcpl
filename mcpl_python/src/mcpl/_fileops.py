
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

"""Operations on whole MCPL files."""

__all__ = [
    'can_merge',
    'convert2ascii',
    'create_outfile_mpi',
    'dump_file',
    'forcemerge_files',
    'merge_files',
    'merge_inplace',
    'merge_outfiles_mpi',
    'name_helper',
    'repair',
]

import os

from ._common import MCPLError, _determine_version
from ._expressions import _as_filter
from ._messages import _info, _warning
from ._reader import MCPLFile
from ._statsum import _parse_statsum_comment, _statsum_syntax_error, encode_stat_sum
from ._writer import MCPLOutFile


def dump_file(filename,header=True,particles=True,limit=10,skip=0,select=None,**kwargs):
    """Python equivalent of mcpl_dump(..) function from mcpl.h, which can be used to
    dump both header and particle contents of a file to stdout. If select is
    given (an expression or a ParticleFilter), only the selected particles are
    shown."""
    f = MCPLFile(filename,**kwargs)
    print(f"Opened MCPL file {os.path.basename(filename)}:")
    if header:
        f.dump_hdr()
    if particles:
        if select is not None:
            print(f"Showing particles selected with: {_as_filter(select).expression}")
            print()
        f.dump_particles(limit=limit,skip=skip,select=select)

def convert2ascii(mcplfile,outfile):
    """Read particle contents of mcplfile and write into outfile using a simple ASCII-based format"""
    if not hasattr(outfile,'write'):
        with open(outfile,'w') as fh:
            convert2ascii(mcplfile,fh)
        return
    if not isinstance(mcplfile,MCPLFile):
        with MCPLFile(mcplfile) as mfh:
            convert2ascii(mfh,outfile)
        return

    fout = outfile
    fin = mcplfile
    fout.write(f"#MCPL-ASCII\n#ASCII-FORMAT: v1\n#NPARTICLES: {fin.nparticles}\n#END-HEADER\n")
    fout.write("index     pdgcode               ekin[MeV]                   x[cm]          "
               +"         y[cm]                   z[cm]                      ux                  "
               +"    uy                      uz                time[ms]                  weight  "
               +"                 pol-x                   pol-y                   pol-z  userflags\n")
    fmtstr="%5i %11i %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g %23.18g 0x%08x\n"
    for idx,p in enumerate(fin.particles):
        fout.write(fmtstr%(idx,p.pdgcode,p.ekin,p.x,p.y,p.z,p.ux,p.uy,p.uz,p.time,p.weight,p.polx,p.poly,p.polz,p.userflags))

def _open_raw(filename, **kw):
    return MCPLFile(filename, raw_strings = True, **kw)

def _comment_positions(f):
    """Positions in the file of the comment strings of MCPLFile f (pairs of
    position and comment)"""
    h = f._hdr
    pos = 8 + 8 + 32 + (8 if f.opt_universalweight else 0)
    pos += 4 + len(h['sourcename'])
    res = []
    for c in h['comments']:
        pos += 4
        res.append((pos,c))
        pos += len(c)
    return res

def _statsum_entries(f):
    """List of (comment index, key, value) for the stat:sum entries of MCPLFile f
    (value is -1.0 when not available)"""
    res = []
    for i,c in enumerate(f._hdr['comments']):
        if c.startswith(b'stat:sum:'):
            ok, (key, value) = _parse_statsum_comment(c)
            if not ok:
                raise MCPLError(_statsum_syntax_error(c))
            res.append((i, key, -1.0 if value is None else value))
    return res

def _actual_can_merge(f1, f2):
    #Very strict checking of everything except nparticles, like in mcpl.c:
    if f1.headersize != f2.headersize:
        return False
    if f1._hdr['sourcename'] != f2._hdr['sourcename']:
        return False
    if ( f1.opt_userflags != f2.opt_userflags
         or f1.opt_polarisation != f2.opt_polarisation
         or f1.opt_singleprec != f2.opt_singleprec
         or f1.opt_universalpdgcode != f2.opt_universalpdgcode
         or f1.opt_universalweight != f2.opt_universalweight
         or f1.endianness != f2.endianness
         or f1.particlesize != f2.particlesize ):
        return False
    if ( len(f1._hdr['comments']) != len(f2._hdr['comments'])
         or len(f1._hdr['blobkeys']) != len(f2._hdr['blobkeys']) ):
        return False
    for c1, c2 in zip(f1._hdr['comments'], f2._hdr['comments']):
        if c1 != c2:
            #incompatible, unless it represents the same stat:sum: entry.
            if not ( c1.startswith(b'stat:sum:') and c2.startswith(b'stat:sum:') ):
                return False
            ok1, (k1, _) = _parse_statsum_comment(c1)
            ok2, (k2, _) = _parse_statsum_comment(c2)
            if not ( ok1 and ok2 ) or k1 != k2:
                return False
    if f1._hdr['blobkeys'] != f2._hdr['blobkeys']:
        return False
    return all( f1._hdr['blobs'][k] == f2._hdr['blobs'][k]
                for k in f1._hdr['blobkeys'] )

def can_merge(file1, file2):
    """Check if two MCPL files can be merged (like mcpl_can_merge in the C
    API). This requires everything in the headers except the number of
    particles and the values of stat:sum entries to be identical."""
    with _open_raw(file1) as f1, _open_raw(file2) as f2:
        return _actual_can_merge(f1, f2)

def _file_certainly_exists(filename):
    import pathlib
    return pathlib.Path(filename).is_file()

def _is_same_file(f1, f2):
    import pathlib
    try:
        return pathlib.Path(f1).samefile(f2)
    except OSError:
        return False

def _error_on_dups(files):
    for i in range(len(files)):
        for j in range(i):
            if _is_same_file(files[i], files[j]):
                raise MCPLError('Merging file with itself')

def _stablesum_add(s, x):
    """Numerically stable summation (Neumaier's algorithm, like in mcpl.c). s is
    a list [naive sum, correction]."""
    import math
    t = s[0] + x
    if ( ( math.isinf(t) or math.isinf(s[0]) or math.isinf(x) )
         and ( s[0] >= 0.0 ) == ( x >= 0.0 ) ):
        #same sign infinities, avoid NaN by going directly to infinity:
        s[0], s[1] = math.inf, 0.0
        return
    s[1] += (s[0] - t) + x if abs(s[0]) >= abs(x) else (x - t) + s[0]
    s[0] = t

def merge_files(file_output, files):
    """Merge the particle contents of a list of compatible files into a new file
    (like mcpl_merge_files in the C API). Values of stat:sum entries are
    added up. Returns the new file as an open MCPLOutFile object, which must
    be closed with close() or closeandgzip()."""
    import math
    files = [ os.fspath(f) for f in files ]
    file_output = os.fspath(file_output)
    if not files:
        raise MCPLError('merge_files must be called with at least one input file')
    _error_on_dups(files)
    for f in files[1:]:
        if not can_merge(files[0], f):
            raise MCPLError('Attempting to merge incompatible files.')
    if _file_certainly_exists(file_output):
        raise MCPLError('requested output file of merge_files already exists')
    out = MCPLOutFile(file_output)
    warned_oldversion = False
    scinfo = None
    for ifile, fn in enumerate(files):
        with _open_raw(fn) as fi:
            if ifile == 0:
                out.transfer_metadata(fi)
                scinfo = []
                for _, key, value in _statsum_entries(fi):
                    s = [0.0, 0.0]
                    if value == -1.0:
                        s[0] = -1.0
                    else:
                        _stablesum_add(s, value)
                    scinfo.append((key, s))
                    if value != -1.0:
                        out.hdr_add_stat_sum(key, -1.0)
                out._write_header()
            else:
                for (key, s), (_, _, value) in zip(scinfo, _statsum_entries(fi)):
                    if s[0] == -1.0 and s[1] == 0.0:
                        continue
                    if value == -1.0:
                        s[0], s[1] = -1.0, 0.0
                    else:
                        _stablesum_add(s, value)
            if fi.version == 3:
                #Can transfer raw bytes:
                for b in fi.particle_blocks:
                    out._write_records(b._data)
            else:
                if not warned_oldversion:
                    warned_oldversion = True
                    _warning('Merging files from older MCPL'
                             ' format. Output will be in latest format.')
                for b in fi.particle_blocks:
                    out.add_particles(position=b.position, direction=b.direction,
                                      polarisation=b.polarisation, ekin=b.ekin,
                                      time=b.time, weight=b.weight,
                                      pdgcode=b.pdgcode, userflags=b.userflags)
    warned_statsuminf = False
    for key, s in scinfo:
        val = s[0] + s[1]
        if val == -1.0:
            continue
        if math.isinf(val):
            if not warned_statsuminf:
                warned_statsuminf = True
                _warning('Merging files results in one or more'
                         ' stat:sum: entries overflowing floating point'
                         ' range and producing infinity. Reverting value to -1'
                         ' to indicate that a precise result is not available.')
            continue
        out.hdr_add_stat_sum(key, val)
    return out

def forcemerge_files(file_output, files, keep_userflags = False):
    """Merge particle contents of a list of files, even if they are not
    compatible, at the price of discarding most meta-data like comments and
    blobs (like mcpl_forcemerge_files in the C API). Userflags are discarded
    unless keep_userflags is set. Returns the new file as an open MCPLOutFile
    object, which must be closed with close() or closeandgzip()."""
    files = [ os.fspath(f) for f in files ]
    file_output = os.fspath(file_output)
    if not files:
        raise MCPLError('forcemerge_files must be called with at least one input file')
    _error_on_dups(files)
    if _file_certainly_exists(file_output):
        raise MCPLError('requested output file of forcemerge_files already exists')
    if all( can_merge(files[0], f) for f in files[1:] ):
        _info(f'forcemerge_files called with {len(files)} files that are'
              ' compatible for a standard merge => falling back to'
              ' standard merge_files function', prefix = 'MCPL ')
        return merge_files(file_output, files)
    opt_dp = opt_pol = opt_uf = False
    lastseen_pdg, disallow_pdg = 0, False
    lastseen_w, disallow_w = 0.0, False
    for fn in files:
        with _open_raw(fn) as f:
            if not f.nparticles:
                continue
            opt_uf = opt_uf or bool(f.opt_userflags)
            opt_pol = opt_pol or bool(f.opt_polarisation)
            opt_dp = opt_dp or not f.opt_singleprec
            updg = f.opt_universalpdgcode
            if not updg or ( lastseen_pdg and lastseen_pdg != updg ):
                disallow_pdg = True
            else:
                lastseen_pdg = updg
            uw = f.opt_universalweight
            if not uw or ( lastseen_w and lastseen_w != uw ):
                disallow_w = True
            else:
                lastseen_w = uw
    out = MCPLOutFile( file_output,
                       sourcename = ( 'mcpl_forcemerge_files (from MCPL v'
                                      f'{_determine_version()})' ),
                       opt_userflags = opt_uf and keep_userflags,
                       opt_polarisation = opt_pol,
                       opt_singleprec = not opt_dp,
                       opt_universalpdgcode = 0 if disallow_pdg else lastseen_pdg,
                       opt_universalweight = 0.0 if disallow_w else lastseen_w )
    for fn in files:
        with _open_raw(fn) as f:
            np_ = f.nparticles
            _info(f'force-merge: Transferring {np_} particle'
                  f'{"" if np_==1 else "s"} from file {fn}', prefix = 'MCPL ')
            for b in f.particle_blocks:
                out.add_particles(b)
    np_ = out.nparticles
    _info(f'force-merge: Transferred a total of {np_} particle'
          f'{"" if np_==1 else "s"} to new file {file_output}', prefix = 'MCPL ')
    return out

def merge_inplace(file1, file2):
    """Append the particle contents of file2 to file1 (like mcpl_merge_inplace in
    the C API). The files must be compatible, and file1 must not be
    gzipped. Values of stat:sum entries are added up."""
    import math
    import struct
    file1, file2 = os.fspath(file1), os.fspath(file2)
    if _is_same_file(file1, file2):
        raise MCPLError('Merging file with itself')
    with _open_raw(file1) as f1, _open_raw(file2) as f2:
        if not _actual_can_merge(f1, f2):
            raise MCPLError('Attempting to merge incompatible files')
        if f1.version != f2.version:
            raise MCPLError('Attempting to merge incompatible files (can not'
                            ' mix MCPL format versions when merging inplace)')
        if f1._is_gz:
            raise MCPLError('direct modification of gzipped files is not supported.')
        np1, np2 = f1.nparticles, f2.nparticles
        if not np2:
            return
        psize, first_particle_pos = f1.particlesize, f1.headersize
        positions = { i: p for i,(p,_) in enumerate(_comment_positions(f1)) }
        updates = []
        sc2 = { k : v for _,k,v in _statsum_entries(f2) }
        for i, key, value in _statsum_entries(f1):
            newval = -1.0
            if value != -1.0 and sc2[key] != -1.0:
                newval = value + sc2[key]
                if math.isinf(newval):
                    _warning('Merging files results in one or more'
                             ' stat:sum: entries overflowing floating point'
                             ' range and producing infinity. Reverting value to -1'
                             ' to indicate that a precise result is not available.')
                    newval = -1.0
            updates.append((positions[i], key, newval))
        try:
            fh = open(file1,'r+b')  # noqa: SIM115
        except OSError:
            raise MCPLError('Unable to open file1 in update mode!')
        with fh:
            def write_at(pos, data):
                fh.seek(pos)
                fh.write(data)
            #While transferring, the file appears broken and in need of repair:
            write_at(8, struct.pack('=Q', 0))
            for pos, key, _ in updates:
                write_at(pos, encode_stat_sum(key, -1.0).encode('ascii'))
            fh.seek(first_particle_pos + psize * np1)
            fh.writelines(b._data.tobytes() for b in f2.particle_blocks)
            for pos, key, newval in updates:
                if newval != -1.0:
                    write_at(pos, encode_stat_sum(key, newval).encode('ascii'))
            write_at(8, struct.pack('=Q', np1 + np2))

def repair(filename):
    """Repair a file which was not properly closed, or which was truncated, by
    updating the number of particles in the header and removing any
    incomplete particle data at the end (like mcpl_repair in the C API)."""
    import pathlib
    import struct
    filename = os.fspath(filename)
    with _open_raw(filename, _recover = False) as f:
        nparticles = f.nparticles
        if f._is_gz:
            if nparticles == 0:
                if len(f._fileread(dtype='u1',count=1)):
                    raise MCPLError('Input file is indeed broken, but must be'
                                    ' gunzipped before it can be repaired.')
                raise MCPLError('File does not appear to be broken.')
            raise MCPLError('File must be gunzipped before it can be checked'
                            ' and possibly repaired.')
        ndata = pathlib.Path(filename).stat().st_size - f.headersize
        if ndata < 0:
            raise MCPLError('File does not appear to be broken.')
        np_ = ndata // f.particlesize
        if np_ == nparticles and not ndata % f.particlesize:
            raise MCPLError('File does not appear to be broken.')
        if nparticles > 0 and np_ > nparticles:
            raise MCPLError('Input file has invalid combination of meta-data & filesize.')
        positions = { i: p for i,(p,_) in enumerate(_comment_positions(f)) }
        statsums = [ (positions[i], key) for i, key, value in _statsum_entries(f)
                     if value != -1.0 ]
        headersize, psize = f.headersize, f.particlesize
    for _, key in statsums:
        _warning(f'Marking stat:sum:{key} entry as not available'
                 ' (-1) since file not closed properly.')
    with open(filename,'r+b') as fh:
        for pos, key in statsums:
            fh.seek(pos)
            fh.write(encode_stat_sum(key, -1.0).encode('ascii'))
        fh.truncate(headersize + np_ * psize)
        fh.seek(8)
        fh.write(struct.pack('=Q', np_))
    _info(f'Successfully repaired file with {np_} particles.')

def _absolute_path(path):
    #Like mctools_absolute_path in C. Not with pathlib, which would also
    #remove "." components (unlike the C code on non-Windows platforms):
    if os.name == 'nt':
        return os.path.abspath(path)
    return path if os.path.isabs(path) else os.path.join(os.getcwd(), path)

def _namehelper(filename, iproc, mode):
    fn = os.fspath(filename)
    for ending in ('.mcpl', '.mcpl.gz'):
        fn = fn.removesuffix(ending)
    fn = _absolute_path(fn)
    if mode in ('m', 'g'):
        fn += f'.mpiworker{iproc}'
        mode = mode.upper()
    if mode == 'M':
        return fn + '.mcpl'
    if mode == 'G':
        return fn + '.mcpl.gz'
    if mode == 'B':
        return fn
    raise MCPLError('internal namehelper: bad mode')

def name_helper(filename, mode):
    """Estimate the output name of a given filename (like mcpl_name_helper in the
    C API), which can be relative or absolute and with or without .mcpl or
    .mcpl.gz suffixes. The mode controls the returned name: "M" for
    /abs/path/base.mcpl, "G" for /abs/path/base.mcpl.gz, "B" for
    /abs/path/base, and "m", "g", "b" for the same without the directory."""
    if mode not in ('M', 'G', 'B', 'm', 'g', 'b'):
        raise MCPLError('name_helper: invalid mode')
    res = _namehelper(filename, 0, mode.upper())
    import pathlib
    return res if mode.isupper() else pathlib.PurePath(res).name

def create_outfile_mpi(filename, iproc, nproc, **kwargs):
    """Create output file for worker process iproc out of nproc (like
    mcpl_create_outfile_mpi in the C API). The worker files must be closed
    with closeandgzip(), after which merge_outfiles_mpi can be used to merge
    them into the final file. Keyword arguments are passed on to
    MCPLOutFile."""
    if nproc > 100000000:
        raise MCPLError('create_outfile_mpi: nproc too large')
    if nproc == 0:
        raise MCPLError('create_outfile_mpi: nproc must be larger than 0')
    if iproc >= nproc:
        raise MCPLError('create_outfile_mpi: iproc must be less than nproc')
    return MCPLOutFile(_namehelper(filename, iproc, 'm' if nproc > 1 else 'M'), **kwargs)

def merge_outfiles_mpi(filename, nproc):
    """Merge the gzipped worker files created with create_outfile_mpi into the
    final gzipped output file and remove them (like mcpl_merge_outfiles_mpi in
    the C API)."""
    if nproc > 100000000:
        raise MCPLError('merge_outfiles_mpi: nproc too large')
    if nproc == 0:
        raise MCPLError('merge_outfiles_mpi: nproc must be larger than 0')
    import pathlib
    if nproc == 1:
        fngz = _namehelper(filename, 0, 'G')
        if not pathlib.Path(fngz).is_file():
            raise MCPLError(f'merge_outfiles_mpi: expected output file "{fngz}"'
                            ' from iproc=0 not found.')
        return
    targetfn = _namehelper(filename, 0, 'M')
    fns = [ _namehelper(filename, iproc, 'g') for iproc in range(nproc) ]
    out = merge_files(targetfn, fns)
    for fn in fns:
        f = pathlib.Path(fn)
        f.unlink()
        _info(f'Removing file {f.name}')
    if not out.closeandgzip():
        raise MCPLError('merge_outfiles_mpi: problems gzipping final output')
