
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


def set_values( src, dst, ipart, values ):
    """Copy MCPL file src to dst, with new values in the packed data of the
    particle at index ipart (a dictionary with field names of the packed data,
    like 'x' or 'uve1'). This can for instance create files with NaN or
    infinite values, which can not be written with the MCPL APIs."""
    import pathlib

    import mcpldev as mcpl
    import numpy as np
    with mcpl.MCPLFile(src) as f:
        pos0 = f.headersize + ipart * f.particlesize
        fields = f._pdt.fields
    data = bytearray(pathlib.Path(src).read_bytes())
    for field, value in values.items():
        dt, offset = fields[field][0], fields[field][1]
        data[pos0+offset:pos0+offset+dt.itemsize] = np.array([value],dtype=dt).tobytes()
    pathlib.Path(dst).write_bytes(bytes(data))
