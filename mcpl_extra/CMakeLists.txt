
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

#Detect skbuild mode (std/monolithic) if appropriate:

if ( DEFINED SKBUILD_PROJECT_NAME )
  set( MCPLEXTRA_NOTOUCH_CMAKE_BUILD_TYPE "ON" )
endif()

# Respect value of CMAKE_BUILD_TYPE if already defined, otherwise fall back to
# Release. In any case, expose CMAKE_BUILD_TYPE as an explicit cache variable
# (gives drop-down list in gui). This must come before the call to
# project(..). We do not do this in case the generator is multi-cfg, and we also
# provide the hidden MCPLEXTRA_NOTOUCH_CMAKE_BUILD_TYPE option to not do it.
#

if( NOT MCPLEXTRA_NOTOUCH_CMAKE_BUILD_TYPE )
  get_property( gen_is_multicfg GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG )
  if ( NOT gen_is_multicfg )
    if( DEFINED CMAKE_BUILD_TYPE )
      set( _def_cbt ${CMAKE_BUILD_TYPE} )
    else()
      set( _def_cbt Release )
    endif()
    set( CMAKE_BUILD_TYPE ${_def_cbt} CACHE STRING
      "Choose the type of build, options are: Debug Release RelWithDebInfo and MinSizeRel." )
    set_property( CACHE CMAKE_BUILD_TYPE
      PROPERTY STRINGS Debug Release RelWithDebInfo MinSizeRel None )
  endif()
endif()

#Setup project:

project( MCPLExtra VERSION 1.9.80
  LANGUAGES C
  DESCRIPTION "Monte Carlo Particle Lists"
  HOMEPAGE_URL "https://github.com/mctools/mcpl"
)

if( NOT MCPLEXTRA_NOTOUCH_CMAKE_BUILD_TYPE )
  if ( NOT gen_is_multicfg )
    if ( NOT CMAKE_BUILD_TYPE )
      #This can happen if parent project called the project(..) function before
      #doing the song and dance we did above.
      set(CMAKE_BUILD_TYPE Release)
    endif()
  endif()
endif()

#Find MCPL (mcpl-core):
if ( NOT TARGET MCPL::MCPL )
  if( NOT DEFINED "MCPL_DIR" )
    #Need to invoke "mcpl-config --show cmakedir" if we want to be able to
    #work with mcpl-core installed via python wheels:
    execute_process(
      COMMAND mcpl-config --show cmakedir
      OUTPUT_VARIABLE "MCPL_DIR" OUTPUT_STRIP_TRAILING_WHITESPACE
    )
  endif()
  find_package( MCPL 1.9.80 REQUIRED )
endif()

if ( DEFINED SKBUILD_PROJECT_NAME )
  message( STATUS "scikit-build mode detected. Overriding some settings." )
  set( mcplextra_pymodname "_mcpl_extra" )
  set( CMAKE_INSTALL_LIBDIR "${mcplextra_pymodname}/data/lib" )
  set( CMAKE_INSTALL_INCLUDEDIR "${mcplextra_pymodname}/data/include" )
  set( CMAKE_INSTALL_BINDIR "${mcplextra_pymodname}/data/bin" )
endif()

if ( MCPLEXTRA_ENABLE_CPACK )
  set( CPACK_PACKAGE_CONTACT "MCPL developers" )
  set( CPACK_PACKAGE_HOMEPAGE_URL "https://github.com/mctools/mcpl" )
  set( CPACK_NSIS_PACKAGE_NAME "${PROJECT_NAME} ${PROJECT_VERSION}" )
  set( CPACK_NSIS_DISPLAY_NAME "${PROJECT_NAME} ${PROJECT_VERSION}" )
  include(CPack)
endif()

#Installation directories (try to follow standard conventions):
include(GNUInstallDirs)
set(MCPLEXTRA_BINDIR "${CMAKE_INSTALL_BINDIR}")#e.g. <prefix>/bin>
set(MCPLEXTRA_LIBDIR "${CMAKE_INSTALL_LIBDIR}")#e.g. <prefix>/lib>

set(mcplextra_skbuild_shlib_in_wheel_scripts "OFF")
if ( WIN32 )
  #dll's must be in %PATH% so we put them in bin (same as seems to be the way
  #most packages do it on conda-forge).
  set(MCPLEXTRA_SHLIBDIR "${MCPLEXTRA_BINDIR}")
  if ( DEFINED SKBUILD_PROJECT_NAME )
    #For wheels we will place the mcpl.dll into the scripts folder, since
    #that seems to be the only way to get the dll onto the PATH.
    set(MCPLEXTRA_SHLIBDIR "${SKBUILD_SCRIPTS_DIR}")
    set(mcplextra_skbuild_shlib_in_wheel_scripts "ON")
  endif()
else()
  #sane standard world
  set(MCPLEXTRA_SHLIBDIR "${MCPLEXTRA_LIBDIR}")
endif()

set(MCPLEXTRA_INCDIR "${CMAKE_INSTALL_INCLUDEDIR}")#e.g. <prefix>/include>
if ( NOT MCPLEXTRA_CMAKEDIR )
  set(MCPLEXTRA_CMAKEDIR "${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}")#e.g. <prefix>/lib/cmake/MCPL>
endif()

include(CheckCCompilerFlag)
if(CMAKE_C_COMPILER_ID MATCHES "MSVC")
  set( MCPLEXTRA_STRICT_COMP_FLAGS "/WX" "/W4" )
else()
  set( MCPLEXTRA_STRICT_COMP_FLAGS -Wall -Wextra -pedantic -Werror )
endif()

if ( MCPLEXTRA_BUILD_STRICT )
  #Set globally warnings -> errors (although only has an effect in CMake 3.24 or
  #later):
  set( "CMAKE_COMPILE_WARNING_AS_ERROR" "ON" )
  # turn list into space separated string for check_c_compiler_flag:
  string( REPLACE ";" " " tmp "${MCPLEXTRA_STRICT_COMP_FLAGS}" )
  check_c_compiler_flag( "${tmp}" mcplextra_compiler_supports_strict_comp_flags )
endif()

set( STRICT_CSTD OFF )
if ( MCPLEXTRA_BUILD_STRICT )
  #We also want to test the C-example with strict C standard (90, 99, 11). For
  #simplicity we simply pick a C standard value based on the provided c++
  #standard, in a way which allows us to cover the various C standards.
  if ( MCPLEXTRA_BUILD_STRICT STREQUAL "99" OR MCPLEXTRA_BUILD_STRICT STREQUAL "ON" )
    set( STRICT_CSTD 99 )
  elseif ( MCPLEXTRA_BUILD_STRICT STREQUAL "11" )
    set( STRICT_CSTD 11 )
  elseif ( MCPLEXTRA_BUILD_STRICT STREQUAL "17" )
    if( "${CMAKE_VERSION}" VERSION_LESS "3.21" )
      message(FATAL_ERROR "MCPLEXTRA_BUILD_STRICT=17 requires cmake 3.21")
    endif()
    set( STRICT_CSTD 17 )
  elseif ( MCPLEXTRA_BUILD_STRICT STREQUAL "23" )
    if( "${CMAKE_VERSION}" VERSION_LESS "3.21" )
      message(FATAL_ERROR "MCPLEXTRA_BUILD_STRICT=17 requires cmake 3.21")
    endif()
    set( STRICT_CSTD 23 )
  else()
    #should have been caught earlier:
    message( FATAL_ERROR "Unexpected value of MCPLEXTRA_BUILD_STRICT" )
  endif()
endif()

function( detect_math_libs )
  #FIXME: To common module (along with the -fp-model=precise, and build_strict
  #stuff. To be shared between mcpl-core, mcpl-extra, and ncrystal.

  #Make sure we link in math functions correctly (typically the linker needs
  #libm on unix, but nothing on Windows). Sets MCPL_MATH_LIBRARIES in calling
  #scope unless already defined.
  if ( DEFINED MCPL_MATH_LIBRARIES )
    return()
  endif()
  set( result "" )
  set(TMP_TESTLIBMSRC
    "#include <math.h>\nint main(int argc,char** argv) { (void)argv;double a=(exp)(argc+1.0); return (int)(a*0.1); }\n")
  set(TMP_TESTDIR ${PROJECT_BINARY_DIR}/test_libm)
  file(WRITE ${TMP_TESTDIR}/test.c "${TMP_TESTLIBMSRC}")
  try_compile(ALWAYS_HAS_MATH "${TMP_TESTDIR}" "${TMP_TESTDIR}/test.c")
  if (NOT ALWAYS_HAS_MATH)
    set(TMP_TESTDIR ${PROJECT_BINARY_DIR}/test_libm2)
    file(WRITE ${TMP_TESTDIR}/test.c "${TMP_TESTLIBMSRC}")
    try_compile(MATH_NEEDS_LIBM "${TMP_TESTDIR}" "${TMP_TESTDIR}/test.c" LINK_LIBRARIES m)
    if (MATH_NEEDS_LIBM)
      set( result "m" )
    else()
      message( FATAL_ERROR "Could not figure out link flags needed to enable math functions" )
    endif()
  endif()
  set( "MCPL_MATH_LIBRARIES" "${result}" PARENT_SCOPE )
endfunction()

set( mcplextra_extra_private_compile_options "" )
if ( "x${CMAKE_C_COMPILER_ID}" STREQUAL "xIntelLLVM" )
  #Intel defaults to the equivalent of -ffast-math, revert back to proper math:
  set( mcplextra_extra_private_compile_options -fp-model=precise )
elseif( "${CMAKE_VERSION}" VERSION_LESS "3.20" AND "x${CMAKE_C_COMPILER_ID}" STREQUAL "xClang" )
  #Older cmake had the llvm-based intel compiler classified as "Clang". In
  #this case, we check whether or not the -fp-model=precise flag is supported
  #or not:
  include(CheckCCompilerFlag)
  check_c_compiler_flag( -fp-model=precise compiler_supports_fpmodelprecise )
  if ( compiler_supports_fpmodelprecise )
    set( mcplextra_extra_private_compile_options -fp-model=precise )
  endif()
endif()

#MCPL library and header files, including optional built-in modules if enabled:
set(
  mcplsswlib_src_files
  "src/ssw/common/sswread.h"  "src/ssw/common/sswread.c"
  "src/ssw/common/sswmcpl.h"  "src/ssw/common/sswmcpl.c"
)
set(
  mcplphitslib_src_files
  "src/phits/common/phitsread.h"  "src/phits/common/phitsread.c"
  "src/phits/common/phitsmcpl.h"  "src/phits/common/phitsmcpl.c"
)
set( ssw2mcpl_main "src/ssw/app_ssw2mcpl/main.c" )
set( mcpl2ssw_main "src/ssw/app_mcpl2ssw/main.c" )
set( phits2mcpl_main "src/phits/app_phits2mcpl/main.c" )
set( mcpl2phits_main "src/phits/app_mcpl2phits/main.c" )

set(
  srcs_c_all
  ${mcplsswlib_src_files} ${ssw2mcpl_main} ${mcpl2ssw_main}
  ${mcplphitslib_src_files} ${phits2mcpl_main} ${mcpl2phits_main}
)
set( srcs_all ${srcs_c_all} )

set_source_files_properties(
  ${srcs_c_all}
  PROPERTIES C_VISIBILITY_PRESET "hidden"
)

set(
  all_targets
  "ssw2mcpl" "mcpl2ssw"
  "phits2mcpl" "mcpl2phits"
)

if ( MCPLEXTRA_BUILD_STRICT AND mcplextra_compiler_supports_strict_comp_flags )
  set_property(
    SOURCE ${srcs_all}
    APPEND PROPERTY COMPILE_OPTIONS "${MCPLEXTRA_STRICT_COMP_FLAGS}"
  )
endif()

detect_math_libs()

add_executable( ssw2mcpl ${ssw2mcpl_main} ${mcplsswlib_src_files} )
target_include_directories( ssw2mcpl PRIVATE "${PROJECT_SOURCE_DIR}/src/ssw/common" )

add_executable( mcpl2ssw ${mcpl2ssw_main} ${mcplsswlib_src_files} )
target_include_directories( mcpl2ssw PRIVATE "${PROJECT_SOURCE_DIR}/src/ssw/common" )

add_executable( phits2mcpl ${phits2mcpl_main} ${mcplphitslib_src_files} )
target_include_directories( phits2mcpl PRIVATE "${PROJECT_SOURCE_DIR}/src/phits/common" )

add_executable( mcpl2phits ${mcpl2phits_main} ${mcplphitslib_src_files} )
target_include_directories( mcpl2phits PRIVATE "${PROJECT_SOURCE_DIR}/src/phits/common" )

foreach( tgt ${all_targets} )
  target_link_libraries( ${tgt} MCPL::MCPL ${MCPL_MATH_LIBRARIES} )
  target_compile_options( ${tgt} PRIVATE ${mcplextra_extra_private_compile_options} )
  install(
    TARGETS ${tgt}
    RUNTIME DESTINATION ${MCPLEXTRA_BINDIR}
  )
  if ( STRICT_CSTD )
    set_target_properties (
      ${tgt} PROPERTIES
      C_STANDARD ${STRICT_CSTD}
      C_STANDARD_REQUIRED ON C_EXTENSIONS OFF
    )
  endif()
endforeach()

if ( MCPL_ENABLE_TESTING )
  #Purely for usage in CTests apps
  add_library( mcplsswtestlib SHARED ${mcplsswlib_src_files} )
  target_compile_definitions( mcplsswtestlib PRIVATE MCPLSSW_IS_TEST_LIB )
  target_link_libraries( mcplsswtestlib MCPL::MCPL ${MCPL_MATH_LIBRARIES} )
  add_library( mcplphitstestlib SHARED ${mcplphitslib_src_files} )
  target_compile_definitions( mcplphitstestlib PRIVATE MCPLPHITS_IS_TEST_LIB )
  target_link_libraries( mcplphitstestlib MCPL::MCPL ${MCPL_MATH_LIBRARIES} )
  if ( WIN32 )
    set_target_properties(
      mcplsswtestlib PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS TRUE
    )
    set_target_properties(
      mcplphitstestlib PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS TRUE
    )
  endif()
endif()

