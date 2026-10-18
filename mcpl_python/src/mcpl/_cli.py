
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

"""The mcpltool command."""

__all__ = ['app_mcpltool', 'app_pymcpltool']

import os
import pathlib
import re
import sys

from ._common import MCPLError, _determine_version, _output_bytearray_raw
from ._fileops import (
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
from ._writer import MCPLOutFile


def _mcpltool_usage(progname,errmsg=None):
    if errmsg:
        print(f"ERROR: {errmsg}\n")
        print("Run with -h or --help for usage information")
        sys.exit(1)
    helpmsg = """
Tool for inspecting or modifying Monte Carlo Particle List (.mcpl) files.

The default behaviour is to display the contents of the FILE in human readable
format (see Dump Options below for how to modify what is displayed).

This installation supports direct reading of gzipped files (.mcpl.gz).

Usage:
  PROGNAME [dump-options] FILE
  PROGNAME --merge [merge-options] FILE1 FILE2
  PROGNAME --extract [extract-options] FILE1 FILE2
  PROGNAME --repair FILE
  PROGNAME --hist EXPR [hist-options] FILE [FILE2 ...]
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
               Userdata will be discarded unless all files have the same
               userdata layout.

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

Histogram options:
  --hist EXPR FILE1 [FILE2 ...]
                    Plot histogram of the values of the expression EXPR, which
                    must not have units (divide by a unit, e.g. "ekin/MeV").
                    With more files, there is a curve for each file. For a 2D
                    histogram, give two expressions separated by " : ".
  --select EXPR, -pPDGCODE
                  : Only include the selected particles (as above).
  --bins N        : Number of bins (by default chosen from the number of
                    particles, and with the unicode and ascii backends at most
                    the resolution of the plot).
  --range LOW:HIGH: Range of the histogram (default is all values). For 2D
                    histograms, use XLOW:XHIGH,YLOW:YHIGH (or XLOW:XHIGH).
  --logx, --logy  : Logarithmic binning and x axis, or logarithmic y axis.
  --lethargy      : Divide by the bin widths in lethargy (implies --logx).
  --split EXPR    : Separate curves for each value of the expression EXPR,
                    e.g. --split pdgcode, or --split "x > 0cm".
  --unweighted    : Count particles instead of summing their weights.
  --print         : Print histogram contents rather than plotting it.
  --output FILE   : Save plot in FILE (e.g. .pdf, .png, or .html with plotly).
  --backend NAME  : Plotting backend (default is the one named by the
                    MCPL_PLOT_BACKEND environment variable, or else the first
                    available of: matplotlib, plotly, unicode, ascii). The
                    unicode and ascii backends draw plots as text in the
                    terminal (or in .txt files with --output).

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
  --output FILE, --backend NAME
                  : Like --pdf, but saving plots in FILE, and/or with the given
                    plotting backend (as for --hist).

Other options:
  -r, --repair FILE
                    Attempt to repair FILE which was not properly closed, by up-
                    dating the file header with the correct number of particles.
  -t, --text MCPLFILE OUTFILE
                    Read particle contents of MCPLFILE and write into OUTFILE
                    using a simple ASCII-based format.
  --create-examples[=N]
                    Create three example files, with N particles each (default
                    1000000), in the current directory (to try out mcpltool).
  -d, --dry-run   : Do everything except writing files (e.g. to check for
                    errors or see what would happen before doing it), with
                    --merge, --forcemerge, --extract, --repair, --text and
                    --create-examples. It is ignored with commands which do not
                    write files, so it can always be added to be sure that
                    nothing is written.
  -v, --version   : Display version of MCPL installation.
  -h, --help      : Display this usage information (ignores all other options).
  --traceback     : Show the Python traceback for errors (for debugging).
"""
    print(helpmsg.strip().replace('PROGNAME',progname))
    sys.exit(0)

def app_mcpltool(argv=None):
    """Implements the mcpltool command. If no argv list is
    passed in, sys.argv will be used. In case of errors, MCPLError exceptions
    are raised. Messages are always printed, even if use_logging() was
    called."""
    with _ForcePrinting():
        _app_mcpltool(argv)

def _app_mcpltool(argv):
    if argv is None:
        argv = sys.argv

    progname,args = os.path.basename(argv[0]),argv[1:]
    if progname == '__main__.py':
        progname = 'python -m mcpl'

    #NB: We do not use standard python parsing modules, since we want to be
    #as strictly compatible with mcpltool-c as possible.

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
    opt_dryrun = False
    pdgcode_str = None
    #Options with values (--name VALUE or --name=VALUE) and histogram flags:
    vopts = {}
    vopt_names = ('--select','--edit','--hist','--bins','--range','--split',
                  '--output','--backend')
    hflags = set()
    hflag_names = ('--logx','--logy','--lethargy','--unweighted','--print')
    filelist = []
    def bad(errmsg):
        _mcpltool_usage(progname,errmsg)
    args = list(args)
    #(--create-examples can only be combined with --dry-run):
    opt_examples = None
    for a in args:
        if a == '--create-examples' or a.startswith('--create-examples='):
            if opt_examples is not None:
                bad("--create-examples specified more than once")
            opt_examples = a.partition('=')[2]
    if opt_examples is not None:
        if any( not ( a.startswith('--create-examples') or a in
                      ('-d','--dry-run','--traceback') ) for a in args ):
            bad("--create-examples can only be combined with --dry-run.")
        n = None
        if opt_examples:
            if not opt_examples.isdigit() or not int(opt_examples) > 0:
                bad("--create-examples=N requires a positive integer N")
            n = int(opt_examples)
        from ._examples import create_examples
        dry_run = '-d' in args or '--dry-run' in args
        try:
            create_examples( n, dry_run = dry_run )
        except MCPLError as e:
            bad(str(e))
        _mcpltool_dryrun_note(dry_run)
        return
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
        elif a in hflag_names:
            hflags.add(a)
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
            elif a=='--dry-run':
                opt_dryrun=True
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
                _mcpltool_usage(progname)
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
                elif f=='d':
                    opt_dryrun=True
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
                    _mcpltool_usage(progname)
                else:
                    bad(f"Unrecognised option : -{f}")
        else:
            filelist += [a]
    opt_select = vopts.get('--select')
    opt_edit = vopts.get('--edit')
    opt_hist = vopts.get('--hist')
    for o in ('--bins','--range','--split') + tuple(sorted(hflags)):
        if ( o in vopts or o in hflags ) and opt_hist is None:
            bad(f"{o} can only be used with --hist.")
    for o in ('--output','--backend'):
        if o in vopts and opt_hist is None and not opt_stats:
            bad(f"{o} can only be used with --hist or --stats.")
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
    #(--dry-run is ignored with commands which do not write files, so it can
    #always be added to be safe, but plots can not be saved in a dry run):
    if opt_dryrun and ( opt_pdf or '--output' in vopts ):
        bad("--dry-run can not be used with --pdf or --output (which save"
            " plots in files).")
    if sum(1 for e in (opt_version,opt_text,number_dumpopts,numper_statopts,
                       any_mergeopts,opt_extract,opt_repair,
                       opt_hist is not None) if e)>1:
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
            bad(f"{optname} can only be used with --extract, --stats, --hist,"
                " or when showing particles.")
    if pdgcode_str is not None and not opt_extract:
        #Turn -p into a selection:
        pdgcode = _tool_pdgcode(pdgcode_str,bad)
        sel = f'pdgcode == {pdgcode_str if pdgcode_str in _particle_names else pdgcode}'
        opt_select = sel if opt_select is None else f'{sel} && ({opt_select})'
    if opt_select is not None and not opt_extract:
        from ._expressions import ParticleFilter
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
        _mcpltool_merge(filelist,opt_forcemerge,opt_inplace,opt_keepuserflags,
                          opt_dryrun,bad)
        _mcpltool_dryrun_note(opt_dryrun)
        sys.exit(0)

    if opt_extract:
        _mcpltool_extract(filelist,opt_limit,opt_skip,pdgcode_str,opt_select,
                            opt_edit,opt_preventcomment,opt_keepstatsum,
                            opt_dryrun,bad)
        _mcpltool_dryrun_note(opt_dryrun)
        sys.exit(0)

    if opt_hist is not None:
        from ._clistats import mcpltool_hist
        mcpltool_hist(filelist,opt_hist,opt_select,vopts,hflags,bad)
        sys.exit(0)

    if opt_text:
        if len(filelist)>2:
            bad("Too many arguments.")
        if len(filelist)!=2:
            bad("Must specify both input and output files with --text.")
        if (os.path.exists(filelist[1])):
            bad("Requested output file already exists.")
        if opt_dryrun:
            #(still read and convert everything, for the same errors):
            import io
            convert2ascii(filelist[0],io.StringIO())
            _mcpltool_dryrun_note(opt_dryrun)
            sys.exit(0)
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
        repair(filelist[0], dry_run = opt_dryrun)
        _mcpltool_dryrun_note(opt_dryrun)
        sys.exit(0)

    if opt_stats:
        from ._clistats import mcpltool_stats
        mcpltool_stats(filelist[0],opt_select,opt_pdf,opt_gui,vopts,bad)
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

def _mcpltool_close(outfile, attempt_gzip):
    if attempt_gzip:
        if not outfile.closeandgzip():
            _warning("Failed to gzip output. Non-gzipped output is"
                     f" found in {outfile.filename}")
            return outfile.filename
        return outfile.filename + '.gz'
    outfile.close()
    return outfile.filename

def _mcpltool_dryrun_note(dry_run):
    if dry_run:
        _info('dry run, nothing was written')

def _mcpltool_merge(filelist, opt_forcemerge, opt_inplace, opt_keepuserflags,
                      dry_run, bad):
    if len(filelist) < 2:
        bad("Too few arguments for --forcemerge." if opt_forcemerge
            else "Too few arguments for --merge.")
    ifirst = 0 if opt_inplace else 1
    if not opt_forcemerge:
        from ._fileops import _merge_incompat_reason, _open_raw
        for f in filelist[ifirst+1:]:
            with _open_raw(filelist[ifirst]) as f1, _open_raw(f) as f2:
                reason = _merge_incompat_reason(f1, f2)
            if reason is not None:
                bad("Requested files are incompatible for merge as they have"
                    f" different header info ({reason}).")
    if opt_inplace:
        for f in filelist[ifirst+1:]:
            merge_inplace(filelist[ifirst],f,dry_run=dry_run)
        return
    err, outfn, attempt_gzip = _tool_outfn(filelist[0])
    if err:
        bad(err)
    if opt_forcemerge:
        out = forcemerge_files(outfn,filelist[1:],opt_keepuserflags,dry_run=dry_run)
    else:
        out = merge_files(outfn,filelist[1:],dry_run=dry_run)
    if out is not None:
        _mcpltool_close(out,attempt_gzip)

def _mcpltool_extract(filelist, limit, skip, pdgcode_str, select, edit,
                        preventcomment, keepstatsum, dry_run, bad):
    if len(filelist) > 2:
        bad("Too many arguments.")
    if len(filelist) != 2:
        bad("Must specify both input and output files with --extract.")
    err, outfn, attempt_gzip = _tool_outfn(filelist[1])
    if err:
        bad(err)
    if select is not None or edit is not None:
        from ._expressions import ParticleEdit, ParticleFilter
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
        #Like mcpltool-c, only warn about NaN or infinite values in the
        #particles in the range given by -s and -l:
        fi._check_nonfinite = False
        fo = MCPLOutFile(outfn, _dry_run = dry_run)
        #(a failed extraction must not leave an output file behind)
        try:
            fo.transfer_metadata(fi)
            n_in = fi.nparticles
            if not preventcomment:
                #Describe which particles were extracted (but nothing specific
                #to the input file, to keep files extracted in the same way
                #mergeable):
                opts = ( ( [ f'-l{limit}' ] if limit > 0 else [] )
                         + ( [ f'-s{skip}' ] if skip > 0 else [] )
                         + ( [ f'-p{pdgcode}' ] if pdgcode else [] ) )
                fo.hdr_add_comment('mcpltool: extracted particles'
                                   + ( ' with ' + ' '.join(opts)
                                       if opts else '' ))
            if select is not None:
                fo.hdr_add_comment('mcpltool: selected particles with:'
                                   f' {select}')
            if edit is not None:
                fo.hdr_add_comment('mcpltool: edited particles with:'
                                   f' {edit}')
            #As in mcpltool, stat:sum entries are marked as not available
            #when selecting particles based on their positions in the file,
            #and also when editing their weights unless --keep-statsum was
            #used (see the guidelines for stat:sum entries):
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
            for b in fi.particle_blocks:
                off = b.file_offset
                if off + len(b) <= skip:
                    continue
                if off >= iend:
                    break
                b = b[max(0,skip-off):min(len(b),iend-off)]
                fi._warn_if_nonfinite(b)
                if pdgcode:
                    b = b[b.pdgcode == pdgcode]
                if flt is not None:
                    b = b[flt(b)]
                if edt is not None:
                    fo.add_particles(b,**edt(b))
                else:
                    fo.add_particles(b)
            n_added = fo.nparticles
            outname = _mcpltool_close(fo,attempt_gzip)
        except BaseException:
            fo._abort()
            raise
    _info(f"{'Would extract' if dry_run else 'Successfully extracted'}"
          f" {n_added} / {n_in} particles from {filelist[0]} into {outname}")

def main():
    """This function simply calls app_mcpltool(), but any raised MCPLError
    exception will be caught and transformed into a corresponding error message
    followed by a call to sys.exit(1). This is what the mcpltool command and
    "python -m mcpl" run. With the --traceback option, MCPLError exceptions
    are not caught, so their Python traceback is shown."""
    if '--traceback' in sys.argv[1:]:
        app_mcpltool()
        return
    try:
        app_mcpltool()
    except MCPLError as e:
        print(f'MCPL ERROR: {e!s}')
        sys.exit(1)

def app_pymcpltool(argv=None):
    """The old name of app_mcpltool (still available for backwards
    compatibility)."""
    print('MCPL WARNING: app_pymcpltool has been renamed to app_mcpltool,'
          ' and will be removed in a future release.')
    app_mcpltool(argv)

def _main_pymcpltool():
    """The pymcpltool command, which is the old name of the mcpltool
    command."""
    print('MCPL WARNING: The pymcpltool command has been renamed to mcpltool,'
          ' and will be removed in a future release.')
    main()
