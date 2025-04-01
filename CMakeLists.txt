
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

project( MCPLRoot LANGUAGES C CXX )

#The primary reason for having this CMakeLists.txt at the root of the repository
#is to enable CTests of all the projects.

#Build mcpl-core and mcpl-extra. Note that if tests are enabled, mcpl-python is
#also tested, even though not explicitly listed here as the MCPL Python module
#will be injected via PYTHONPATH (done in CMake code in the tests subdirectory):
add_subdirectory("${PROJECT_SOURCE_DIR}/mcpl_core")
add_subdirectory("${PROJECT_SOURCE_DIR}/mcpl_extra")

if ( MCPL_ENABLE_TESTING )
  #CTests are enabled. First determine which tests for mcpl-extra code are
  #available. Always use those from this repo:
  set( MCPLEXTRA_TEST_DIR_LIST "${PROJECT_SOURCE_DIR}/tests/extra" )
  #But we might also have some additional tests:
  set( MCPLEXTRA_ADDITIONAL_TESTS "" CACHE PATH "Directory with extra tests")
  if ( MCPLEXTRA_ADDITIONAL_TESTS )
    if ( NOT IS_DIRECTORY "${MCPLEXTRA_ADDITIONAL_TESTS}" )
      message( FATAL_ERROR
        "MCPLEXTRA_ADDITIONAL_TESTS dir not found:"
        " ${MCPLEXTRA_ADDITIONAL_TESTS}"
      )
    endif()
    list( APPEND MCPLEXTRA_TEST_DIR_LIST "${MCPLEXTRA_ADDITIONAL_TESTS}" )
  endif()
  #Finally enable and add the tests:
  enable_testing()
  add_subdirectory("${PROJECT_SOURCE_DIR}/tests")
endif()
