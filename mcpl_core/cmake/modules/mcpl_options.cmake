
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

include( mctools_utils )

#Variables. Note that if changing the default value of a variable with a
#corresponding deprecated variable below, the default value should be modified
#in the add_deprecated_boolvar(..) call as well!

enum_option( MCPL_ENABLE_ZLIB "Whether to enable zlib support" DEFAULT FETCH FETCH_NG USEPREINSTALLED )
bool_option( MCPL_ENABLE_CFGAPP "Whether to build and install the mcpl-config command" "ON" )
bool_option( MCPL_ENABLE_CORE_TESTING "Enable the few CTests fully contained within the mcpl_core project." "OFF" )
enum_option( MCPL_BUILD_STRICT "Stricter build (primarily for testing). Can optionally select specific standard." "OFF" "ON" "99" "11" "14" "17" "23" )

if ( MCPL_ENABLE_ZLIB STREQUAL "DEFAULT" )
  if ( WIN32 )
    set( MCPL_ENABLE_ZLIB "FETCH")
  else()
    set( MCPL_ENABLE_ZLIB "USEPREINSTALLED")
  endif()
endif()

if ( DEFINED MCPL_ENABLE_RPATHMOD )
  message( FATAL_ERROR
    "MCPL_ENABLE_RPATHMOD no longer supported."
  )
endif()
if ( DEFINED MCPL_BUILD_FATBINARIES )
  message( FATAL_ERROR
    "MCPL_ENABLE_PYTHON not supported: The mcpl-core"
    " project no longer contains any python code."
  )
endif()
if ( DEFINED MCPL_ENABLE_EXAMPLES )
  message( FATAL_ERROR
    "MCPL_ENABLE_EXAMPLES not supported: code examples"
    " are now maintained outside of the main project."
  )
endif()
if ( DEFINED MCPL_BUILD_FATBINARIES )
  message( FATAL_ERROR
    "MCPL_BUILD_FATBINARIES not supported: The MCPL project"
    " no longer provides code for fat binaries."
  )
endif()
if ( DEFINED MCPL_ENABLE_GEANT4 )
  message( FATAL_ERROR
    "MCPL_ENABLE_GEANT4 not supported: The MCPL-Geant4"
    " bindings are now provided in a standalone project."
  )
endif()
if ( DEFINED MCPL_ENABLE_PHITS )
  message( FATAL_ERROR
    "MCPL_ENABLE_GEANT4 not supported: The MCPL-Geant4"
    " bindings are now provided in a standalone project."
  )
endif()
if ( DEFINED MCPL_ENABLE_SSW )
  message( FATAL_ERROR
    "MCPL_ENABLE_GEANT4 not supported: The MCPL-Geant4"
    " bindings are now provided in a standalone project."
  )
endif()
