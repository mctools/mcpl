
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

"""The pymcpltool command."""

__all__ = ['app_pymcpltool']

import os
import pathlib
import re
import sys

from ._common import MCPLError, _determine_version, _output_bytearray_raw
from ._expressions import ParticleEdit, ParticleFilter
from ._fileops import (
    can_merge,
    convert2ascii,
    dump_file,
    forcemerge_files,
    merge_files,
    merge_inplace,
    repair,
)
from ._messages import _ForcePrinting, _info, _warning
from ._physics import _particle_names
from ._reader import MCPLFile
from ._stats import _SelectedFile, dump_stats, plot_stats
from ._writer import MCPLOutFile


def _pymcpltool_usage(progname,errmsg=None):
    if errmsg:
        print(f"ERROR: {errmsg}\n")
        print("Run with -h or --help for usage information")
        sys.exit(1)
    helpmsg = """
Tool for inspecting or modifying Monte Carlo Particle List (.mcpl) files.

The default behaviour is to display the contents of the FILE in human readable
format (see Dump Options below for how to modify what is displayed).

This is the python version of the tool, which in addition to the features of
the compiled mcpltool can show statistics, and select or edit particles based
on expressions.

This installation supports direct reading of gzipped files (.mcpl.gz).

Usage:
  PROGNAME [dump-options] FILE
  PROGNAME --merge [merge-options] FILE1 FILE2
  PROGNAME --extract [extract-options] FILE1 FILE2
  PROGNAME --repair FILE
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
  -pPDGCODE       : Only show particles of the type given by PDGCODE (or name,
                    see Extract options below).
  --select EXPR   : Only show particles for which the expression EXPR is true
                    (-l and -s then apply to the selected particles).

Merge options:
  -m, --merge FILEOUT FILE1 FILE2 ... FILEN
                    Creates new FILEOUT with combined particle contents from
                    specified list of N existing and compatible files.
                    FILEOUT will be gzipped if its name ends with .mcpl.gz.
  -m, --merge --inplace FILE1 FILE2 ... FILEN
                    Appends the particle contents in FILE2 ... FILEN into
                    FILE1. Note that this action modifies FILE1!
  --forcemerge [--keepuserflags] FILEOUT FILE1 FILE2 ... FILEN
               Like --merge but works with incompatible files as well, at the
               heavy price of discarding most metadata like comments and blobs.
               Userflags will be discarded unless --keepuserflags is specified.

Extract options:
  -e, --extract FILE1 FILE2
                    Extracts particles from FILE1 into a new FILE2.
                    FILE2 will be gzipped if its name ends with .mcpl.gz.
  -lN, -sN        : Select range of particles in FILE1 (as above).
  -pPDGCODE       : Select particles of type given by PDGCODE. Instead of the
                    PDGCODE, one of the following names can be used: neutron,
                    antineutron, proton, antiproton, electron, positron (or
                    antielectron), muon, antimuon, gamma (or photon).
  --no-comment    : Do not add comments to the header of FILE2 about how the
                    particles were extracted.
  --select EXPR   : Select particles for which the expression EXPR is true,
                    e.g. --select "pdgcode == neutron && ekin < 25meV".
  --edit EXPR     : Modify particles with the assignments in EXPR, e.g.
                    --edit "z += 1cm, weight *= 0.5, wavelength = 1.8Aa".
                    Editing weights marks stat:sum entries as not available
                    (-1), as does selecting particles with -l or -s.
  --keep-statsum  : Keep stat:sum entries when --edit modifies weights (if
                    the edit is known to be compatible with them).

Expressions:
  Expressions can use the particle fields x, y, z, ux, uy, uz, polx, poly,
  polz, ekin, time, weight, pdgcode, userflags, and wavelength (which is only
  defined for neutrons and gammas, which must be selected before using it,
  e.g. "pdgcode == neutron && wavelength > 1.8Aa"). Operators are as in C (+ -
  * / % == != < <= > >= && || !), with ^ or ** for powers, and functions like
  sqrt, abs, sin, cos, atan2, hypot, min, max and clamp are available, as are
  the particle names listed for -p above as pdgcode values. Values with units
  must have units (meV, eV, keV, MeV, GeV, TeV, ns, us, ms, s, Aa, nm, um, mm,
  cm, m, km), e.g. "ekin < 25meV", "wavelength > 0.18nm" or "x^2 + y^2 <
  4cm^2", except for a plain 0 (e.g. "x > 0"), and deg can be used for angles,
  e.g. "acos(uz) < 10deg". Bit masks can be used for userflags, e.g.
  "userflags & 0x10". In --edit, statements are separated by commas and
  executed in order. Besides assignments to fields (e.g. "z += 1cm"), they can
  be assignments to variables (e.g. "tmp = x, x = y, y = tmp"), swap(a,b), and
  rotate_x(angle), rotate_y(angle) or rotate_z(angle).

Stat options:
  --stats FILE    : Print statistics summary of particle state data from FILE.
  --stats --pdf FILE
                  : Produce PDF file mcpl.pdf with histograms of particle state
                    data from FILE.
  --stats --gui FILE
                  : Like --pdf, but opens interactive histogram views directly.
  -pPDGCODE       : Only include particles of the type given by PDGCODE (or
                    name, see Extract options above) in the statistics.
  --select EXPR   : Only include particles for which the expression EXPR is
                    true in the statistics.

Other options:
  -r, --repair FILE
                    Attempt to repair FILE which was not properly closed, by up-
                    dating the file header with the correct number of particles.
  -t, --text MCPLFILE OUTFILE
                    Read particle contents of MCPLFILE and write into OUTFILE
                    using a simple ASCII-based format.
  -v, --version   : Display version of MCPL installation.
  -h, --help      : Display this usage information (ignores all other options).
  --traceback     : Show the Python traceback for errors (for debugging).
"""
    print(helpmsg.strip().replace('PROGNAME',progname))
    sys.exit(0)

def app_pymcpltool(argv=None):
    """Implements a python equivalent of the compiled MCPL tool. If no argv list is
    passed in, sys.argv will be used. In case of errors, MCPLError exceptions
    are raised. Messages are always printed, even if use_logging() was
    called."""
    with _ForcePrinting():
        _app_pymcpltool(argv)

def _app_pymcpltool(argv):
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
    opt_merge = False
    opt_forcemerge = False
    opt_keepuserflags = False
    opt_inplace = False
    opt_extract = False
    opt_preventcomment = False
    opt_repair = False
    opt_keepstatsum = False
    pdgcode_str = None
    #Options with values (--name VALUE or --name=VALUE):
    vopts = {}
    vopt_names = ('--select','--edit')
    filelist = []
    def bad(errmsg):
        _pymcpltool_usage(progname,errmsg)
    args = list(args)
    while args:
        a = args.pop(0)
        if a.startswith('--') and a.split('=')[0] in vopt_names:
            name, eq, value = a.partition('=')
            if not eq:
                if not args:
                    bad(f"Missing argument for {name}")
                value = args.pop(0)
            if name in vopts:
                bad(f"{name} specified more than once")
            vopts[name] = value
        elif a.startswith('--'):
            if a=='--merge':
                opt_merge=True
            elif a=='--forcemerge':
                opt_forcemerge=True
            elif a=='--keepuserflags':
                opt_keepuserflags=True
            elif a=='--inplace':
                opt_inplace=True
            elif a=='--extract':
                opt_extract=True
            elif a in ('--no-comment','--preventcomment'):
                opt_preventcomment=True
            elif a=='--keep-statsum':
                opt_keepstatsum=True
            elif a=='--repair':
                opt_repair=True
            elif a=='--justhead':
                opt_justhead=True
            elif a=='--nohead':
                opt_nohead=True
            elif a=='--version':
                opt_version=True
            elif a=='--stats':
                opt_stats=True
            elif a=='--pdf':
                opt_pdf=True
            elif a=='--gui':
                opt_gui=True
            elif a=='--text':
                opt_text=True
            elif a=='--traceback':
                pass#handled by main()
            elif a=='--help':
                _pymcpltool_usage(progname)
            else:
                bad(f"Unrecognised option : {a}")
        elif a.startswith('-'):
            a=a[1:]
            while a:
                f,a=a[0],a[1:]
                if f=='b':
                    if opt_blobkey is not None:
                        bad("-b specified more than once")
                    if not a:
                        bad("Missing argument for -b")
                    opt_blobkey,a = a,''
                elif f=='p':
                    if pdgcode_str is not None:
                        bad("-p specified more than once")
                    if not a:
                        bad("Missing argument for -p")
                    pdgcode_str,a = a,''
                elif f=='m':
                    opt_merge=True
                elif f=='e':
                    opt_extract=True
                elif f=='r':
                    opt_repair=True
                elif f=='l' or f=='s':
                    if not a:
                        bad("Bad option: missing number")
                    if not a.isdigit():
                        bad("Bad option: expected number")
                    if f=='l':
                        if opt_limit is not None:
                            bad("-l specified more than once")
                        opt_limit = int(a)
                    else:
                        assert f=='s'
                        if opt_skip is not None:
                            bad("-s specified more than once")
                        opt_skip = int(a)
                    a=''
                elif f=='j':
                    opt_justhead=True
                elif f=='n':
                    opt_nohead=True
                elif f=='v':
                    opt_version=True
                elif f=='t':
                    opt_text=True
                elif f=='h':
                    _pymcpltool_usage(progname)
                else:
                    bad(f"Unrecognised option : -{f}")
        else:
            filelist += [a]
    opt_select = vopts.get('--select')
    opt_edit = vopts.get('--edit')
    if not opt_extract and opt_edit is not None:
        bad("--edit can only be used with --extract.")
    if not opt_extract and opt_keepstatsum:
        bad("--keep-statsum can only be used with --extract.")
    if not opt_extract and opt_preventcomment:
        bad("--no-comment can only be used with --extract.")
    if opt_inplace and not opt_merge:
        bad("--inplace can only be used with --merge.")
    if opt_keepuserflags and not opt_forcemerge:
        bad("--keepuserflags can only be used with --forcemerge.")
    if opt_merge and opt_forcemerge:
        bad("--merge and --forcemerge can not both be specified .")
    number_dumpopts = sum(1 for e in (opt_justhead,opt_nohead,opt_blobkey) if e)
    if not opt_extract:
        number_dumpopts += sum(1 for e in (opt_limit is not None,opt_skip is not None) if e)
    numper_statopts = sum(1 for e in (opt_stats,opt_pdf,opt_gui) if e)
    any_mergeopts = opt_merge or opt_forcemerge
    if sum(1 for e in (opt_version,opt_text,number_dumpopts,numper_statopts,
                       any_mergeopts,opt_extract,opt_repair) if e)>1:
        bad('Conflicting options specified.')
    if number_dumpopts>1 and opt_blobkey:
        bad("Do not specify other dump options with -b.")
    if opt_pdf and not opt_stats:
        bad("Do not specify --pdf without --stats")
    if opt_gui and not opt_stats:
        bad("Do not specify --gui without --stats")
    if opt_gui and opt_pdf:
        bad("Do not specify both --pdf and --gui")
    for optname,optval in (('-p',pdgcode_str),('--select',opt_select)):
        if optval is not None and ( opt_version or opt_text or any_mergeopts
                                    or opt_repair or opt_justhead or opt_blobkey ):
            bad(f"{optname} can only be used with --extract, --stats,"
                " or when showing particles.")
    if pdgcode_str is not None and not opt_extract:
        #Turn -p into a selection:
        pdgcode = _tool_pdgcode(pdgcode_str,bad)
        sel = f'pdgcode == {pdgcode_str if pdgcode_str in _particle_names else pdgcode}'
        opt_select = sel if opt_select is None else f'{sel} && ({opt_select})'
    if opt_select is not None and not opt_extract:
        try:
            opt_select = ParticleFilter(opt_select)
        except MCPLError as e:
            bad(str(e))

    if opt_version:
        if filelist:
            bad("Unrecognised arguments for --version.")
        print(f"MCPL version {_determine_version()}")
        sys.exit(0)

    if any_mergeopts:
        _pymcpltool_merge(filelist,opt_forcemerge,opt_inplace,opt_keepuserflags,bad)
        sys.exit(0)

    if opt_extract:
        _pymcpltool_extract(filelist,opt_limit,opt_skip,pdgcode_str,opt_select,
                            opt_edit,opt_preventcomment,opt_keepstatsum,bad)
        sys.exit(0)

    if opt_text:
        if len(filelist)>2:
            bad("Too many arguments.")
        if len(filelist)!=2:
            bad("Must specify both input and output files with --text.")
        if (os.path.exists(filelist[1])):
            bad("Requested output file already exists.")
        try:
            fout = open(filelist[1],'w')  # noqa: SIM115
        except OSError:
            fout = None
        if not fout:
            raise MCPLError('Could not open output file.')
        try:
            convert2ascii(filelist[0],fout)
        finally:
            fout.close()
        sys.exit(0)

    #Dump or stats:
    if len(filelist)>1:
        bad("Too many arguments.")
    if not filelist:
        bad("No input file specified")

    if opt_repair:
        repair(filelist[0])
        sys.exit(0)

    if opt_stats:
        f=MCPLFile(filelist[0])
        if f.nparticles==0:
            bad("Can not calculate statistics for an empty file")
        if opt_select is not None:
            f = _SelectedFile(f,opt_select)
            if f.nparticles==0:
                bad("Can not calculate statistics when no particles are selected")
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
    dump_file(filelist[0],header=not opt_nohead,particles=not opt_justhead,
              limit=opt_limit,skip=opt_skip,select=opt_select)
    sys.exit(0)

def _tool_pdgcode(pdgcode_str,bad):
    """Decode argument of -p like in mcpltool"""
    if pdgcode_str in _particle_names:
        return _particle_names[pdgcode_str]
    if ( not re.fullmatch(r'[-+]?[0-9]+',pdgcode_str)
         or not ( -2147483648 <= int(pdgcode_str) <= 2147483647 )
         or not int(pdgcode_str) ):
        bad("Must specify non-zero 32bit integer or particle name as argument to -p.")
    return int(pdgcode_str)

def _tool_outfn(fn):
    """Output filename for --merge and --extract like in mcpltool (returns error
    message, filename to create, and whether to gzip it)."""
    if pathlib.Path(fn).is_file():
        return "Requested output file already exists.", None, False
    if fn.endswith('.mcpl.gz'):
        if pathlib.Path(fn[:-3]).is_file():
            return ( "Requested output file already exists (without .gz extension).",
                     None, False )
        return None, fn[:-3], True
    if fn.endswith('.gz'):
        return ( "Requested output file should not have .gz extension (unless it is .mcpl.gz).",
                 None, False )
    if not fn.endswith('.mcpl') and pathlib.Path(fn+'.mcpl').is_file():
        return "Requested output file already exists (with .mcpl extension).", None, False
    return None, fn, False

def _pymcpltool_close(outfile, attempt_gzip):
    if attempt_gzip:
        if not outfile.closeandgzip():
            _warning("Failed to gzip output. Non-gzipped output is"
                     f" found in {outfile.filename}")
            return outfile.filename
        return outfile.filename + '.gz'
    outfile.close()
    return outfile.filename

def _pymcpltool_merge(filelist, opt_forcemerge, opt_inplace, opt_keepuserflags, bad):
    if len(filelist) < 2:
        bad("Too few arguments for --forcemerge." if opt_forcemerge
            else "Too few arguments for --merge.")
    ifirst = 0 if opt_inplace else 1
    if not opt_forcemerge:
        for f in filelist[ifirst+1:]:
            if not can_merge(filelist[ifirst],f):
                bad("Requested files are incompatible for merge as they have"
                    " different header info.")
    if opt_inplace:
        for f in filelist[ifirst+1:]:
            merge_inplace(filelist[ifirst],f)
        return
    err, outfn, attempt_gzip = _tool_outfn(filelist[0])
    if err:
        bad(err)
    if opt_forcemerge:
        out = forcemerge_files(outfn,filelist[1:],opt_keepuserflags)
    else:
        out = merge_files(outfn,filelist[1:])
    _pymcpltool_close(out,attempt_gzip)

def _pymcpltool_extract(filelist, limit, skip, pdgcode_str, select, edit,
                        preventcomment, keepstatsum, bad):
    if len(filelist) > 2:
        bad("Too many arguments.")
    if len(filelist) != 2:
        bad("Must specify both input and output files with --extract.")
    err, outfn, attempt_gzip = _tool_outfn(filelist[1])
    if err:
        bad(err)
    try:
        flt = ParticleFilter(select) if select is not None else None
        edt = ParticleEdit(edit) if edit is not None else None
    except MCPLError as e:
        bad(str(e))
    pdgcode = 0
    if pdgcode_str is not None:
        pdgcode = _tool_pdgcode(pdgcode_str,bad)
    limit = limit or 0
    skip = skip or 0
    with MCPLFile(filelist[0],raw_strings=True) as fi:
        fo = MCPLOutFile(outfn)
        fo.transfer_metadata(fi)
        n_in = fi.nparticles
        if not preventcomment:
            #Describe which particles were extracted (but nothing specific to
            #the input file, to keep files extracted in the same way mergeable):
            opts = ( ( [ f'-l{limit}' ] if limit > 0 else [] )
                     + ( [ f'-s{skip}' ] if skip > 0 else [] )
                     + ( [ f'-p{pdgcode}' ] if pdgcode else [] ) )
            fo.hdr_add_comment('mcpltool: extracted particles'
                               + ( ' with ' + ' '.join(opts) if opts else '' ))
        if select is not None:
            fo.hdr_add_comment(f'pymcpltool: selected particles with: {select}')
        if edit is not None:
            fo.hdr_add_comment(f'pymcpltool: edited particles with: {edit}')
        #As in mcpltool, stat:sum entries are marked as not available when
        #selecting particles based on their positions in the file, and also
        #when editing their weights unless --keep-statsum was used (see the
        #guidelines for stat:sum entries):
        has_statsum = any( v is not None for v in fi.stat_sum.values() )
        if has_statsum and n_in > 0 and ( skip > 0 or 0 < limit < n_in ):
            _warning("Marking stat:sum entries in output file as "
                     "not available (-1) when filtering based on particle "
                     "positions")
            fo.hdr_scale_stat_sums(-1.0)
        elif ( has_statsum and not keepstatsum and edt is not None
               and 'weight' in edt.modified_fields ):
            _warning("Marking stat:sum entries in output file as "
                     "not available (-1) when editing particle weights"
                     " (use --keep-statsum to keep them)")
            fo.hdr_scale_stat_sums(-1.0)
        iend = skip + limit if limit > 0 else n_in
        try:
            for b in fi.particle_blocks:
                off = b.file_offset
                if off + len(b) <= skip:
                    continue
                if off >= iend:
                    break
                b = b[max(0,skip-off):min(len(b),iend-off)]
                if pdgcode:
                    b = b[b.pdgcode == pdgcode]
                if flt is not None:
                    b = b[flt(b)]
                if edt is not None:
                    fo.add_particles(b,**edt(b))
                else:
                    fo.add_particles(b)
        except MCPLError:
            fo.close()
            pathlib.Path(fo.filename).unlink()
            raise
        n_added = fo.nparticles
        outname = _pymcpltool_close(fo,attempt_gzip)
    _info(f"Successfully extracted {n_added} / {n_in} particles from"
          f" {filelist[0]} into {outname}")

def main():
    """This function simply calls app_pymcpltool(), but any raised MCPLError
    exception will be caught and transformed into a corresponding error message
    followed by a call to sys.exit(1). This is what the pymcpltool command and
    "python -m mcpl" run. With the --traceback option, MCPLError exceptions
    are not caught, so their Python traceback is shown."""
    if '--traceback' in sys.argv[1:]:
        app_pymcpltool()
        return
    try:
        app_pymcpltool()
    except MCPLError as e:
        print(f'MCPL ERROR: {e!s}')
        sys.exit(1)
