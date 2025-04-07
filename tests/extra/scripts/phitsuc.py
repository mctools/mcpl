
################################################################################
##                                                                            ##
##  This file is part of MCPL (see https://mctools.github.io/mcpl/)           ##
##                                                                            ##
##  Copyright 2015-2025 MCPL developers.                                      ##
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

from MCPLExtraTestUtils.dirs import ( core_test_data_dir,
                                      mcpl2phits_cmd,
                                      phits2mcpl_cmd,
                                      mcpltool_cmd )
import pathlib
import sys

def main():
    f = core_test_data_dir.joinpath('ref','reffile_1.mcpl')
    assert f.is_file()
    oslash = '\u00f8'
    o = pathlib.Path('.').joinpath(f'f{oslash}{oslash}',f'hell{oslash}.mcpl')
    o.parent.mkdir()
    o.write_bytes( f.read_bytes() )

    import subprocess
    print("Run mcpl2phits",flush=True)
    rv = subprocess.run( [ mcpl2phits_cmd,
                           f'f{oslash}{oslash}/hell{oslash}.mcpl',
                           f'f{oslash}{oslash}/hell{oslash}.dmp' ],
                         capture_output = True )
    sys.stdout.buffer.write(rv.stdout)
    if rv.stderr:
        sys.stdout.buffer.write(rv.stderr)
    if rv.stderr or rv.returncode:
        raise SystemExit(1)

    print("Run phits2mcpl",flush=True)
    rv = subprocess.run( [ phits2mcpl_cmd,
                           f'f{oslash}{oslash}/hell{oslash}.dmp',
                           f'f{oslash}{oslash}/hell{oslash}2.mcpl' ],
                         capture_output = True )
    sys.stdout.buffer.write(rv.stdout)
    if rv.stderr:
        sys.stdout.buffer.write(rv.stderr)
    if rv.stderr or rv.returncode:
        raise SystemExit(1)

    print("Run mcpltool",flush=True)
    assert pathlib.Path(f'f{oslash}{oslash}/hell{oslash}2.mcpl.gz').is_file()
    rv = subprocess.run( [ mcpltool_cmd,
                           f'f{oslash}{oslash}/hell{oslash}2.mcpl.gz' ],
                         capture_output = True )
    sys.stdout.buffer.write(rv.stdout)
    if rv.stderr:
        sys.stdout.buffer.write(rv.stderr)
    if rv.stderr or rv.returncode:
        raise SystemExit(1)

    print("All ok",flush=True)

if __name__ == '__main__':
    main()
