
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

include_guard()

function( mcpl_create_header resvar_includepath )
  #Generate mcpl.h via both configure_file (for non-config specific variables)
  #and then file(GENERATE ..) (for generator expressions) based on the
  #mcpl.h.in template.
  set( srctemplate "${PROJECT_SOURCE_DIR}/include/mcpl.h.in" )
  set( tgtincdir "${PROJECT_BINARY_DIR}/autogen_include_mcplh" )
  set( tgtdir "${tgtincdir}" )
  set( tgtfile "${tgtdir}/mcpl.h" )
  file( MAKE_DIRECTORY "${tgtdir}" )
  set( t1 "1000000 * ${MCPL_VERSION_MAJOR}" )
  set( t2 "1000 * ${MCPL_VERSION_MINOR}" )
  set( t3 "${MCPL_VERSION_PATCH}" )
  math(EXPR version_int "(${t1})+(${t2})+(${t3})" )
  set( ncapidefs "" )
  string( APPEND ncapidefs "#define MCPL_VERSION_MAJOR ${MCPL_VERSION_MAJOR}\n" )
  string( APPEND ncapidefs "#define MCPL_VERSION_MINOR ${MCPL_VERSION_MINOR}\n" )
  string( APPEND ncapidefs "#define MCPL_VERSION_PATCH ${MCPL_VERSION_PATCH}\n" )
  string( APPEND ncapidefs "#define MCPL_VERSION ${version_int}\n" )
  string( APPEND ncapidefs "#define MCPL_VERSION_STR \"${MCPL_VERSION}\"\n" )
  set( MCPL_HOOK_FOR_ADDING_DEFINES
    " -- CMake definitions begin -- */\n\n${ncapidefs}\n/* -- CMake definitions end --" )
  configure_file( "${srctemplate}" "${tgtfile}" @ONLY )
  set( "${resvar_includepath}" "${tgtincdir}" PARENT_SCOPE )
endfunction()

