
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

from MCPLTestUtils.dirs import test_data_dir as test_data_dir_ref
from MCPLTestUtils.dirs import mcpltool_cmd as mcpltool_cmd_ref

from MCPLExtraTestUtils.dirs import ( extra_test_data_dir,
                                      core_test_data_dir,
                                      mcpl2ssw_cmd,
                                      ssw2mcpl_cmd,
                                      mcpltool_cmd )
import subprocess
import sys

def main():

    assert extra_test_data_dir.is_dir()
    assert core_test_data_dir.is_dir()
    assert mcpl2ssw_cmd.is_file()
    assert ssw2mcpl_cmd.is_file()
    assert mcpltool_cmd.is_file()

    assert test_data_dir_ref == core_test_data_dir
    assert mcpltool_cmd_ref == mcpltool_cmd
    for cmdname, cmd in [ ('mcpl2ssw',mcpl2ssw_cmd),
                          ('ssw2mcpl',ssw2mcpl_cmd),
                          ('mcpltool',mcpltool_cmd) ]:
        print(f"\n\nLAUNCHING {cmdname} --help:\n\n")
        rv = subprocess.run([cmd,'--help'],check=True,capture_output=True)
        assert not rv.stderr
        assert rv.returncode == 0
        print(end='',flush=True)
        sys.stdout.buffer.write(rv.stdout)
        print(end='',flush=True)
        #print(rv.stdout.decode(),end='',flush=True)

main()
