
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

#Check the variables provided by find_package(MCPL), by comparing them with
#the output of mcpl-config, and by running the commands. Everything is done
#when configuring this project, which fails if anything is wrong.

cmake_minimum_required(VERSION 3.16...4.4)

project( TestMCPLCMakeVars VERSION 0.0.1 LANGUAGES C )

if( NOT DEFINED "MCPL_DIR" )
  execute_process(
    COMMAND mcpl-config --show cmakedir
    OUTPUT_VARIABLE "MCPL_DIR" OUTPUT_STRIP_TRAILING_WHITESPACE
  )
endif()
find_package( MCPL 2.0.0 REQUIRED )

function( check_failed msg )
  message( FATAL_ERROR "Problem with variables from find_package(MCPL): ${msg}" )
endfunction()

foreach( var MCPL_CMAKEDIR MCPL_BINDIR MCPL_LIBDIR MCPL_INCDIR MCPL_LIBNAME
             MCPL_CMD_MCPLTOOL MCPL_CMD_MCPLCONFIG )
  message( STATUS "${var} = \"${${var}}\"" )
  if ( NOT ${var} )
    check_failed( "${var} is empty" )
  endif()
endforeach()

foreach( var MCPL_CMAKEDIR MCPL_BINDIR MCPL_LIBDIR MCPL_INCDIR )
  if ( NOT IS_DIRECTORY "${${var}}" )
    check_failed( "${var} is not a directory" )
  endif()
endforeach()
if ( NOT EXISTS "${MCPL_INCDIR}/mcpl.h" )
  check_failed( "MCPL_INCDIR does not contain mcpl.h" )
endif()
if ( NOT EXISTS "${MCPL_LIBDIR}/${MCPL_LIBNAME}" )
  check_failed( "MCPL_LIBDIR does not contain MCPL_LIBNAME" )
endif()
foreach( var MCPL_CMD_MCPLTOOL MCPL_CMD_MCPLCONFIG )
  if ( NOT EXISTS "${${var}}" OR IS_DIRECTORY "${${var}}" )
    check_failed( "${var} is not a file" )
  endif()
endforeach()

#The commands must work and report the version found:
foreach( var MCPL_CMD_MCPLTOOL MCPL_CMD_MCPLCONFIG )
  execute_process(
    COMMAND "${${var}}" --version
    OUTPUT_VARIABLE out OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE rv
  )
  if ( NOT rv EQUAL 0 OR NOT out MATCHES "${MCPL_VERSION}" )
    check_failed( "${var} --version failed or gave \"${out}\"" )
  endif()
endforeach()

#The directories and library name must be the same as those of mcpl-config:
foreach( item_and_var cmakedir:MCPL_CMAKEDIR bindir:MCPL_BINDIR
                      libdir:MCPL_LIBDIR includedir:MCPL_INCDIR
                      libname:MCPL_LIBNAME )
  string( REPLACE ":" ";" item_and_var "${item_and_var}" )
  list( GET item_and_var 0 item )
  list( GET item_and_var 1 var )
  execute_process(
    COMMAND "${MCPL_CMD_MCPLCONFIG}" --show "${item}"
    OUTPUT_VARIABLE out OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE rv
  )
  if ( NOT rv EQUAL 0 )
    check_failed( "mcpl-config --show ${item} failed" )
  endif()
  if ( item STREQUAL "libname" )
    set( a "${out}" )
    set( b "${${var}}" )
  else()
    file( REAL_PATH "${out}" a )
    file( REAL_PATH "${${var}}" b )
  endif()
  if ( NOT a STREQUAL b )
    check_failed( "${var} is \"${b}\" but mcpl-config --show ${item} gives \"${a}\"" )
  endif()
endforeach()

message( STATUS "All variables from find_package(MCPL) are OK" )
