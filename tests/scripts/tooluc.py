
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

from MCPLTestUtils.dirs import ( test_data_dir, mcpltool_cmd )
import pathlib
import sys

def main():
    f = test_data_dir.joinpath('ref','reffile_1.mcpl')
    assert f.is_file()
    oslash = '\u00f8'
    o = pathlib.Path('.').joinpath(f'f{oslash}{oslash}',f'hell{oslash}.mcpl')
    o.parent.mkdir()
    o.write_bytes( f.read_bytes() )

    import subprocess
    rv = subprocess.run( [ mcpltool_cmd, f'f{oslash}{oslash}/hell{oslash}.mcpl' ],
                         capture_output = True )
    sys.stdout.buffer.write(rv.stdout)
    if rv.stderr:
        sys.stdout.buffer.write(rv.stderr)
    if rv.stderr or rv.returncode:
        raise SystemExit(1)
    print("All ok",flush=True)

if __name__ == '__main__':
    main()
