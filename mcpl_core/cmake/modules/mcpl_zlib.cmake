
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

function( setup_zlib )
  #Function which detects and/provide ZLib support and sets MCPL_ZLIB_LIBRARIES.
  set( mcpl_zlib_required_depversion "OFF" PARENT_SCOPE )

  set( do_zlib_fetch OFF )
  if ( MCPL_ENABLE_ZLIB STREQUAL "FETCH" )
    set( do_zlib_fetch ON )
    set( zlib_fetch_sources https://github.com/madler/zlib/archive/v1.3.1.tar.gz )
    set( zlib_fetch_sources_sha256 17e88863f3600672ab49182f217281b6fc4d3c762bde361935e436a95214d05c )
  elseif ( MCPL_ENABLE_ZLIB STREQUAL "FETCH_NG" )
    set( do_zlib_fetch ON )
    set( zlib_fetch_sources https://github.com/zlib-ng/zlib-ng/archive/2.2.4.tar.gz )
    set( zlib_fetch_sources_sha256 a73343c3093e5cdc50d9377997c3815b878fd110bf6511c2c7759f2afb90f5a3 )
  endif()
  set( _mcpl_zlib_tgt "" PARENT_SCOPE )
  set( _mcpl_zlib_srcfiles "" PARENT_SCOPE )
  set( _mcpl_zlib_extra_compile_definitions "" PARENT_SCOPE )
  set( _mcpl_zlib_extra_include_dirs "" PARENT_SCOPE )

  if ( NOT do_zlib_fetch )
    #look for preinstalled:
    #TODO: we should have a test (on all 5 github platforms?) that fetches
    #1.2.7 and run CTests. And one with 1.3.1.
    find_package( ZLIB 1.2.7 REQUIRED )
    set( _mcpl_zlib_tgt "ZLIB::ZLIB" PARENT_SCOPE )
    set( mcpl_zlib_required_depversion "${ZLIB_VERSION}" PARENT_SCOPE )
    return()
  endif()

  #Ok, must try to fetch + build! It is well that we do it here inside a
  #function, to prevent poluting most of our code with variables dealing with
  #this.
  message("Will fetch ZLib from ${zlib_fetch_sources} and build into all relevant MCPL binaries.")
  include(FetchContent)
  FetchContent_Declare( zlib URL "${zlib_fetch_sources}" URL_HASH "SHA256=${zlib_fetch_sources_sha256}" )

  if ( MCPL_ENABLE_ZLIB STREQUAL "FETCH" )
    #Variable used in zlib's CMakeLists.txt to prevent zlib files being installed
    #as a side-effect:
    set( SKIP_INSTALL_ALL True )
    set( ZLIB_INSTALL OFF )

    #Avoid annoying warning (since zlib does not add VERSION in project call but
    #as standalone variable):
    set(CMAKE_POLICY_DEFAULT_CMP0048 NEW)

    #Other ZLIB options, mostly to disable things:
    set( ZLIB_BUILD_EXAMPLES OFF )
    set( ZLIB_BUILD_TESTING OFF )
    set( ZLIB_BUILD_SHARED OFF )
    set( ZLIB_BUILD_STATIC ON )
    set( ZLIB_BUILD_MINIZIP OFF )
    set( ZLIB_PREFIX ON )
  else()
    #Avoid annoying warning (since zlib-ng does not add VERSION in project call
    #but as standalone variable):
    set(CMAKE_POLICY_DEFAULT_CMP0048 NEW)
    set( ZLIB_COMPAT ON )
    set( WITH_GTEST OFF )
    set( ZLIB_ENABLE_TESTS OFF )
    set( ZLIBNG_ENABLE_TESTS OFF )
    set( ZLIB_SYMBOL_PREFIX "mcpl" )
    set( WITH_OPTIM OFF )
    set( SKIP_INSTALL_ALL True )
    set( ZLIB_INSTALL OFF )
  endif()

  #Populate and add_subdirectory:
  FetchContent_MakeAvailable(zlib)

  set_target_properties( zlibstatic PROPERTIES EXCLUDE_FROM_ALL True )
  set_target_properties( zlib PROPERTIES EXCLUDE_FROM_ALL True )

  #Get zlib source files:
  get_target_property( zlib_source_files zlibstatic SOURCES)
  set( tmp_zlibsrcfiles "" )
  foreach( zlibfile ${zlib_source_files} )
    if ( IS_ABSOLUTE ${zlibfile} )
      list( APPEND tmp_zlibsrcfiles "${zlibfile}" )
    else()
      list( APPEND tmp_zlibsrcfiles "${zlib_SOURCE_DIR}/${zlibfile}" )
    endif()
  endforeach()

  #get compile definitions needed for these source files, both from the target and the directory:
  #NB: The COMPILE_DEFINITIONS are the PRIVATE+PUBLIC definitions. If we need
  #the INTERFACE/PUBLIC definitions we would have to look at the
  #INTERFACE_COMPILE_DEFINITIONS. In principle we should add those to the OTHER
  #(i.e. non-zlib) source files for a given mcpl target.
  get_target_property( tmp_defs1 zlibstatic COMPILE_DEFINITIONS)
  if ( tmp_defs1 )
    list(APPEND _mcpl_zlib_extra_compile_definitions ${tmp_defs1} )
  endif()
  get_directory_property( tmp_defs2 DIRECTORY "${zlib_SOURCE_DIR}" COMPILE_DEFINITIONS )
  if ( tmp_defs2 )
    list(APPEND _mcpl_zlib_extra_compile_definitions ${tmp_defs2} )
  endif()

  #results:
  set( _mcpl_zlib_srcfiles "${tmp_zlibsrcfiles}" PARENT_SCOPE )
  set( _mcpl_zlib_extra_include_dirs "${zlib_BINARY_DIR}" "${zlib_SOURCE_DIR}" PARENT_SCOPE)
  set( _mcpl_zlib_extra_compile_definitions "${_mcpl_zlib_extra_compile_definitions}" PARENT_SCOPE )

  message(STATUS "ZLIB sources built into MCPL binaries: ${tmp_zlibsrcfiles}")
  message(STATUS "Extra definitions for ZLIB sources built into MCPL binaries: ${_mcpl_zlib_extra_compile_definitions}")
endfunction()

setup_zlib()

function( add_zlib_dependency targetname )
  #Adds private ZLib dependency to target. Any extra arguments are assumed to be
  #compile definitions which should only be added if ZLib support is present.
  if ( _mcpl_zlib_tgt )
    target_link_libraries( ${targetname} PRIVATE ${_mcpl_zlib_tgt} )
  else()
    target_sources( ${targetname} PRIVATE ${_mcpl_zlib_srcfiles} )
    target_include_directories( ${targetname} PRIVATE ${_mcpl_zlib_extra_include_dirs} )
    if ( _mcpl_zlib_extra_compile_definitions )
      set_source_files_properties( ${_mcpl_zlib_srcfiles} PROPERTIES COMPILE_DEFINITIONS "${_mcpl_zlib_extra_compile_definitions}" )
    endif()
  endif()
  if ( ARGN )
    target_compile_definitions( ${targetname} PRIVATE ${ARGN} )
  endif()
endfunction()
