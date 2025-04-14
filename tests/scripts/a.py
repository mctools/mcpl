
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

# NEEDS: numpy

from MCPLTestUtils.dirs import test_data_dir
import gzip
import pathlib
import os

def run_pymcpltool(*args):
    from mcpldev.mcpl import app_pymcpltool
    ec = None
    try:
        app_pymcpltool(['pymcpltool']+[str(e) for e in args])
    except SystemExit as e:
        if str(e).isdigit():
            ec = int(str(e))
        else:
            raise
    print('<flush>')
    print(f"--> ENDED IN EXIT CODE: {ec}")

def main():
    os.environ['PYMCPLTOOL_FAKE_PYVERSION']='1'
    run_pymcpltool('-h')
    run_pymcpltool('-v')
    f1 = test_data_dir.joinpath('ref','reffile_1.mcpl')
    f2 = test_data_dir.joinpath('ref','reffile_12.mcpl')
    assert f1.is_file()
    assert f2.is_file()
    run_pymcpltool(f1)
    run_pymcpltool('-n','-s3','-l5',f1)
    run_pymcpltool('-j',f1)
    pathlib.Path('example.mcpl.gz').write_bytes(gzip.compress(f1.read_bytes()))
    run_pymcpltool('example.mcpl.gz')
    run_pymcpltool(f2)
    run_pymcpltool(f2,'-bBlaData')
    print()
    run_pymcpltool(f2,'--stats')

if __name__ == '__main__':
    main()
