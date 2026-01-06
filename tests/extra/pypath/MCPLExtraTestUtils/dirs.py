
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

def _find_data_dir(extra):
    import pathlib
    d = pathlib.Path(__file__).resolve().absolute().parent.parent.parent
    if not extra:
        d = d.parent
    ddir = d.joinpath('data')
    assert ddir.is_dir()
    return ddir

def _find_cmd(envvar):
    import os
    import pathlib
    f=pathlib.Path(os.environ[envvar])
    assert f.is_file()
    return f

extra_test_data_dir = _find_data_dir(extra=True)
core_test_data_dir = _find_data_dir(extra=False)
mcpl2ssw_cmd = _find_cmd('MCPL2SSW_FILE')
ssw2mcpl_cmd = _find_cmd('SSW2MCPL_FILE')
mcpl2phits_cmd = _find_cmd('MCPL2PHITS_FILE')
phits2mcpl_cmd = _find_cmd('PHITS2MCPL_FILE')
mcpltool_cmd = _find_cmd('MCPL_TOOL_FILE')

