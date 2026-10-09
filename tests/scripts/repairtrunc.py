
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

# Test that --repair handles files truncated anywhere after the header, both for
# files which were never closed (nparticles=0 in header) and files which were
# truncated after being closed, and that no partial particle is left behind.
# Files with more particles than the header claims must be left untouched.

import pathlib

import mcpldev as mcpl
from MCPLTestUtils.dirs import test_data_dir
from MCPLTestUtils.toolcheck_common import cmd


def main():
    ref = test_data_dir.joinpath('ref','reffile_16.mcpl')
    orig = ref.read_bytes()
    with mcpl.MCPLFile(ref) as f:
        hs, ps, n = f.headersize, f.particlesize, f.nparticles
    data_ok = orig[hs:]
    assert len(orig) == hs + n * ps
    f = pathlib.Path('truncated.mcpl')
    cuts = [ (0, 0), (0, ps // 2), (2, 0), (2, ps // 3), (n - 1, ps - 1) ]
    for header_nparticles in (0, n):
        for nfull, nextra in cuts:
            d = bytearray(orig[:hs + nfull * ps + nextra])
            d[8:16] = header_nparticles.to_bytes(8,'little')
            f.write_bytes(bytes(d))
            print(f'==> Header says {header_nparticles} particles, file has'
                  f' {nfull} particles plus {nextra} bytes')
            broken = ( nextra > 0 or nfull != header_nparticles )
            cmd('--repair', f, fail = not broken)
            d = f.read_bytes()
            assert len(d) == hs + nfull * ps
            assert d[hs:] == data_ok[:nfull * ps]
            with mcpl.MCPLFile(f) as fr:
                assert fr.nparticles == nfull
            cmd('--repair', f, fail = True)

    # Header claiming fewer particles than the file holds:
    for nfull, nextra in [ (3, 0), (3, ps // 3), (4, ps - 1), (5, 0) ]:
        d = bytearray(orig[:hs + nfull * ps + nextra])
        d[8:16] = (3).to_bytes(8,'little')
        f.write_bytes(bytes(d))
        print(f'==> Header says 3 particles, file has {nfull} particles plus'
              f' {nextra} bytes')
        cmd('--repair', f, fail = ( nextra == 0 or nfull > 3 ))
        if nfull > 3:
            assert f.read_bytes() == bytes(d)
        else:
            assert f.read_bytes() == bytes(d[:hs + 3 * ps])

if __name__ == '__main__':
    main()
