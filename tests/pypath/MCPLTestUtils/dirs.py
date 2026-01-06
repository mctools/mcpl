
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

"""

   Module providing directories needed during testing.

"""


def _find_data_dir():
    import pathlib
    _pymoddir = pathlib.Path(__file__).resolve().absolute().parent
    #from .modeinfo import is_simplebuild_mode
    if False:#is_simplebuild_mode():
        #import os
        ddir = None#pathlib.Path(os.environ['SBLD_DATA_DIR'])/'NCTestUtils'
    else:
        ddir = _pymoddir.parent.parent.joinpath('data')
    assert ddir.is_dir()
    return ddir

def _find_mcpltool_cmd():
    import os
    import pathlib
    f=pathlib.Path(os.environ['MCPL_TOOL_FILE']).absolute()
    assert f.is_file()
    return f

def _find_mcpllib():
    import os
    import pathlib
    f=pathlib.Path(os.environ['MCPL_LIB']).absolute()
    assert f.is_file()
    return f

test_data_dir = _find_data_dir()
mcpltool_cmd = _find_mcpltool_cmd()
mcpllib = _find_mcpllib()
