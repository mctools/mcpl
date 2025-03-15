
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

cmake_minimum_required(VERSION 3.21...3.31)

project( TestMCPLStandards VERSION 0.0.1 LANGUAGES C CXX )

if( NOT DEFINED "MCPL_DIR" )
  execute_process(
    COMMAND mcpl-config --show cmakedir
    OUTPUT_VARIABLE "MCPL_DIR" OUTPUT_STRIP_TRAILING_WHITESPACE
  )
endif()
find_package( MCPL 1.9.80 REQUIRED )

set( origsrc "${PROJECT_SOURCE_DIR}/main.c" )

include(CheckCCompilerFlag)
if(CMAKE_C_COMPILER_ID MATCHES "MSVC")
  set( strict_flags "/WX" "/W4" "/WD4324" )
else()
  set( strict_flags -Wall -Wextra -pedantic -Werror )
endif()

enable_testing()

foreach( extensions ON OFF )
  foreach( lang C CXX )
    if ( lang STREQUAL C )
      set( stds "90;99;11;17;23" )
      set( stdproperty C_STANDARD )
    else()
      set( stds "98;11;14;17;20;23" )#fixme: 98
      set( stdproperty CXX_STANDARD )
    endif()
    foreach( std ${stds} )
      set( bn "${lang}_${std}_extensions${extensions}" )
      set( src "${PROJECT_BINARY_DIR}/main_${bn}.${lang}" )
      file( COPY_FILE "${origsrc}" "${src}" )
      set( props
        LANGUAGE ${lang}
        ${stdproperty} ${std}
        "${stdproperty}_REQUIRED" ON ${lang}_EXTENSIONS ${extensions}
      )
      set_source_files_properties ( ${src} PROPERTIES ${props} )
      add_executable( "test_${bn}" "${src}" )
      target_link_libraries( "test_${bn}" MCPL::mcpl )#fixme back to MCPL::MCPL
      set_target_properties( "test_${bn}" PROPERTIES ${props} )
      target_compile_options( "test_${bn}" PRIVATE ${strict_flags} )
      add_test(
        NAME "test_${bn}"
        COMMAND "test_${bn}"
        "${PROJECT_SOURCE_DIR}/../../../examples/example.mcpl" )
    endforeach()
  endforeach()
endforeach()
