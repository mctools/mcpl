
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

cmake_minimum_required(VERSION 3.16...3.31)

project( ExampleMCPLProject VERSION 0.0.1 LANGUAGES C )

#Find MCPL:

if( NOT DEFINED "MCPL_DIR" )
  #Need to invoke "mcpl-config --show cmakedir" if we want to be able to
  #work with mcpl-core installed via python wheels:
  execute_process(
    COMMAND mcpl-config --show cmakedir
    OUTPUT_VARIABLE "MCPL_DIR" OUTPUT_STRIP_TRAILING_WHITESPACE
  )
endif()
find_package( MCPL 2.0.0 REQUIRED )

#Add our own targets, and link to MCPL as appropriate:

add_executable( "testapp" "main.c" )
target_link_libraries( "testapp" MCPL::MCPL )
install (TARGETS "testapp" RUNTIME DESTINATION bin)
