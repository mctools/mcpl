
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

#Tests require newer cmake (NB: Synchronize minimum value with that found in the
#check for MCPL_ENABLE_TESTING support in the mcpl_core/CMakeLists.txt
#file):
cmake_minimum_required(VERSION 3.28...3.30)

project( MCPLTests LANGUAGES CXX C )

if ( NOT TARGET mcpl OR NOT TARGET mcplsswtestlib )
  message( FATAL_ERROR "Can only test as part of the MCPL build" )
endif()
set( mcpltests_mcpllib_target mcpl )

enable_testing()

set( CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_CURRENT_LIST_DIR}/cmake")
include( mctools_testutils )

include( "${CMAKE_CURRENT_LIST_DIR}/../mcpl_core/cmake/modules/mcpl_detectmathlibs.cmake" )
detect_math_libs()


#We want to symlink so that "import mcpldev" works instead of "import mpcpl" for
#the tests (to reduce conflicts with MCPL installed in the environment). We copy
#instead as a fall-back (e.g. on Windows).

set( mcpltest_pypath "${PROJECT_BINARY_DIR}/mcpl_tests_pypath" )
file( MAKE_DIRECTORY "${mcpltest_pypath}" )
file( CREATE_LINK
  "${MCPLRoot_SOURCE_DIR}/mcpl_python/src/mcpl"
  "${mcpltest_pypath}/mcpldev"
  COPY_ON_ERROR
  SYMBOLIC
)

set( mcpltest_pyenvmod "" )
list(
  APPEND mcpltest_pyenvmod
  "PYTHONPATH=path_list_prepend:${mcpltest_pypath}"
  "PYTHONPATH=path_list_prepend:${PROJECT_SOURCE_DIR}/pypath"
)
#list(
#  APPEND mcpltest_pyenvmod
#  "MCPL_LIB=set:$<TARGET_FILE:${mcpltests_mcpllib_target}>"
#)

list(
  APPEND mcpltest_pyenvmod
  "MCPL_TOOL_FILE=set:$<TARGET_FILE:mcpltool>"
)

list(
  APPEND mcpltest_pyenvmod
  "PYTHONIOENCODING=set:UTF-8"
  "PYTHONLEGACYWINDOWSSTDIO=set:UTF-8"
)

set( mcpltests_extra_link_libs "${mcpltests_mcpllib_target}" ${MCPL_MATH_LIBRARIES} )

#backtrace from FPE tests need -lexecinfo on FreeBSD:
find_package(Backtrace)
if( Backtrace_FOUND AND Backtrace_LIBRARY )
  #NB: From cmake 3.30, the FindBacktrace modules also provides a proper target
  #(Backtrace::Backtrace) which we should eventually use instead.
  list( APPEND mcpltests_extra_link_libs "${Backtrace_LIBRARY}" )
endif()

set( mcpltests_extra_inc_dirs PUBLIC "${CMAKE_CURRENT_LIST_DIR}/include" )
#TEMP mctools_testutils_add_test_libs(
#TEMP   "${CMAKE_CURRENT_LIST_DIR}/libs"
#TEMP   "${mcpltests_extra_link_libs}"
#TEMP   "${mcpltests_extra_inc_dirs}"
#TEMP )
#TEMP mctools_testutils_add_test_modules(
#TEMP   "${CMAKE_CURRENT_LIST_DIR}/modules"
#TEMP   "${mcpltests_extra_link_libs}"
#TEMP   "${mcpltests_extra_inc_dirs}"
#TEMP )

set( mcpltest_appenvmod "" )

list(
  APPEND mcpltest_appenvmod
  "MCPL_TESTDATA_DIR=set:${CMAKE_CURRENT_LIST_DIR}/data"
)

if ( WIN32 )
  #Do not get "dll not found" errors for the MCPL library. Note that PATH
  #plays the role of LD_LIBRARY_PATH on Windows (and there is seemingly not
  #really any rpath-like solution).
  list(
    APPEND mcpltest_appenvmod
    "PATH=path_list_prepend:$<TARGET_FILE_DIR:${mcpltests_mcpllib_target}>"
  )
endif()

mctools_testutils_add_tests_pyscripts(
  "${CMAKE_CURRENT_LIST_DIR}/scripts" "${mcpltest_pyenvmod}"
)

mctools_testutils_add_tests_apps(
  "${CMAKE_CURRENT_LIST_DIR}/src"
  "${mcpltests_extra_link_libs}"
  "${mcpltests_extra_inc_dirs}"
  "${mcpltest_appenvmod}"
)

#Now add tests for mcpl-extra:
set( mcplextratest_base_pyenvmod "${mcpltest_pyenvmod}" )
set( mcplextratest_base_appenvmod "${mcpltest_appenvmod}" )
if ( WIN32 )
  set(
    mcplextratest_base_envmod_common
    "PATH=path_list_prepend:$<TARGET_FILE_DIR:mcplsswtestlib>"
    "PATH=path_list_prepend:$<TARGET_FILE_DIR:${mcpltests_mcpllib_target}>"
  )
elseif( APPLE )
  set(
    mcplextratest_base_envmod_common
    "DYLD_LIBRARY_PATH=path_list_prepend:$<TARGET_FILE_DIR:mcplsswtestlib>"
    "DYLD_LIBRARY_PATH=path_list_prepend:$<TARGET_FILE_DIR:${mcpltests_mcpllib_target}>"
  )
else()
  set(
    mcplextratest_base_envmod_common
    "LD_LIBRARY_PATH=path_list_prepend:$<TARGET_FILE_DIR:mcplsswtestlib>"
    "LD_LIBRARY_PATH=path_list_prepend:$<TARGET_FILE_DIR:${mcpltests_mcpllib_target}>"
  )
endif()

list(
  APPEND mcplextratest_base_pyenvmod
  "PYTHONPATH=path_list_prepend:${PROJECT_SOURCE_DIR}/extra/pypath"
  "MCPL2SSW_FILE=set:$<TARGET_FILE:mcpl2ssw>"
  "SSW2MCPL_FILE=set:$<TARGET_FILE:ssw2mcpl>"
  ${mcplextratest_base_envmod_common}
)
list(
  APPEND mcplextratest_base_appenvmod
  ${mcplextratest_base_envmod_common}
)
#message(FATAL_ERROR "test ${MCPLEXTRA_TEST_DIR_LIST}")

#FIXME: Add to the envs vars!
foreach( mcplextra_testdir ${MCPLEXTRA_TEST_DIR_LIST} )
  set( tmp_pyenvmod "${mcplextratest_base_pyenvmod}" )
  set( tmp_appenvmod "${mcplextratest_base_appenvmod}" )
  if ( IS_DIRECTORY "${mcplextra_testdir}/data" )
    list(
      APPEND tmp_appenvmod
      "MCPLEXTRADATADIR=set:${mcplextra_testdir}/data"
    )
    list(
      APPEND tmp_pyenvmod
      "MCPLEXTRADATADIR=set:${mcplextra_testdir}/data"
    )
  endif()
  if ( IS_DIRECTORY "${mcplextra_testdir}/pypath" )
    list(
      APPEND tmp_pyenvmod
      "PYTHONPATH=path_list_prepend:${mcplextra_testdir}/pypath"
    )
  endif()
  if ( IS_DIRECTORY "${mcplextra_testdir}/scripts" )
    mctools_testutils_add_tests_pyscripts(
      "${mcplextra_testdir}/scripts"
      "${tmp_pyenvmod}"
    )
  endif()
  if ( IS_DIRECTORY "${mcplextra_testdir}/src" )
    mctools_testutils_add_tests_apps(
      "${mcplextra_testdir}/src"
      "${mcpltests_extra_link_libs};mcplsswtestlib"
      "${mcpltests_extra_inc_dirs};${MCPLExtra_SOURCE_DIR}/src/ssw/common"
      "${tmp_appenvmod}"
    )
  endif()
endforeach()
