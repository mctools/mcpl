
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
import sys

from ._common import MCPLError, _determine_version, _output_bytearray_raw
from ._fileops import convert2ascii, dump_file
from ._messages import _ForcePrinting
from ._reader import MCPLFile
from ._stats import dump_stats, plot_stats


def _pymcpltool_usage(progname,errmsg=None):
    if errmsg:
        print(f"ERROR: {errmsg}\n")
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
    filelist = []
    def bad(errmsg):
        _pymcpltool_usage(progname,errmsg)
    for a in args:
        if a.startswith('--'):
            if a=='--justhead':
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
        print(f"MCPL version {_determine_version()}")
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

def main():
    """This function simply calls app_pymcpltool(), but any raised MCPLError
    exception will be caught and transformed into a corresponding error message
    followed by a call to sys.exit(1). This is what the pymcpltool command and
    "python -m mcpl" run."""
    try:
        app_pymcpltool()
    except MCPLError as e:
        print(f'MCPL ERROR: {e!s}')
        sys.exit(1)
