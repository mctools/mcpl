
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

__all__ = ['convert2ascii', 'dump_file']

import os

from ._reader import MCPLFile


def dump_file(filename,header=True,particles=True,limit=10,skip=0,**kwargs):
    """Python equivalent of mcpl_dump(..) function from mcpl.h, which can be used to
    dump both header and particle contents of a file to stdout."""
    f = MCPLFile(filename,**kwargs)
    print(f"Opened MCPL file {os.path.basename(filename)}:")
    if header:
        f.dump_hdr()
    if particles:
        f.dump_particles(limit=limit,skip=skip)

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
