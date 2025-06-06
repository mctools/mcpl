
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

import pathlib

devpymoddir = pathlib.Path(__file__).absolute().resolve().parent
reporoot = devpymoddir.parent.parent.parent
coreroot = reporoot / 'mcpl_core'
coreroot_include = coreroot / 'include'
coreroot_src = coreroot / 'src'
pyroot = reporoot / 'mcpl_python'
testroot = reporoot / 'tests'

def is_empty_dir( path ):
    return path.is_dir() and not any( True for p in path.iterdir() )
