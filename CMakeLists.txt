##################################################################################
#                                                                                #
# CMake file which can be used to compile and link all code in the MCPL          #
# distribution, and which provides CMake configuration files                     #
# for subsequent usage.                                                          #
#                                                                                #
# One way to invoke cmake to build and install would be like this (run this from #
# a temporary build dir)                                                         #
#                                                                                #
#  $> cmake /path/to/sourcedir -DCMAKE_INSTALL_PREFIX=/path/to/mcplinstalldir    #
#                                                                                #
# Followed by (replace the number 8 by the number of processes you want to       #
# use for the compilation):                                                      #
#                                                                                #
#  $> make install -j8                                                           #
#                                                                                #
# Downstream CMake-based projects can now use find_package(MCPL) calls,          #
# possibly after setting -DMCPL_DIR=/path/to/mcplinstalldir                      #
#                                                                                #
# Refer to the INSTALL file from the MCPL distribution for more details.         #
#                                                                                #
# Written 2016-2022 by T. Kittelmann.                                            #
#                                                                                #
##################################################################################

# We require cmake 3.10. This is intended to strike a balance between features
# and availability. Of popular platforms, a lower number would only have helped
# MCPL usage on a few slightly older distributions such as Ubuntu 16.04 (has
# 3.5.1), Debian oldstable (has 3.7.2 as of Nov2020). CentOS6 and CentOS7 have
# CMake 2.8.12 which is clearly below any sensible threshold, so users on these
# platforms can already be expected to be used to install custom versions of
# tools like CMake (for instance CentOS7 provides cmake3 as a separate package,
# providing CMake 3.11). In any case, on platforms lacking CMake 3.10, one
# must install a newer cmake somehow (this is usually rather simple). See also:
# https://cliutils.gitlab.io/modern-cmake/chapters/intro/installing.html
#
# The maximum value is the maximum value with which we have tested. The reason
# for specifying this maximum value is that it affects the default values of
# cmake policies, depending on which version introduced them.

cmake_minimum_required(VERSION 3.10...3.24)
cmake_policy(SET CMP0054 NEW)

# Respect value of CMAKE_BUILD_TYPE if already defined, otherwise fall back to
# Release. In any case, expose CMAKE_BUILD_TYPE as an explicit cache variable
# (gives drop-down list in gui). This must come before the call to
# project(..). We do not do this in case the generator is multi-cfg, and we also
# provide the hidden MCPL_NOTOUCH_CMAKE_BUILD_TYPE option to not do it.
#
if( NOT MCPL_NOTOUCH_CMAKE_BUILD_TYPE )
  get_property( gen_is_multicfg GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
  if ( NOT gen_is_multicfg )
    if( DEFINED CMAKE_BUILD_TYPE )
      set( _def_cbt ${CMAKE_BUILD_TYPE} )
    else()
      set( _def_cbt Release )
    endif()
    set( CMAKE_BUILD_TYPE ${_def_cbt}  CACHE STRING "Choose the type of build, options are: Debug Release RelWithDebInfo and MinSizeRel." )
    set_property( CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS Debug Release RelWithDebInfo MinSizeRel None )
  endif()
endif()

#Setup project:

set( _project_metadata LANGUAGES C )
if ( NOT MCPL_DISABLE_CXX )
  #Hidden option to not need a c++ compiler (in principle only needed for geant4 hooks).
  list( APPEND _project_metadata CXX )
endif()
list( APPEND _project_metadata DESCRIPTION "Monte Carlo Particle Lists" )
if( "${CMAKE_VERSION}" VERSION_GREATER_EQUAL "3.12.0" )
  list( APPEND _project_metadata HOMEPAGE_URL "https://github.com/mctools/mcpl")
endif()

cmake_policy( SET CMP0048 NEW )#Not sure if this is really needed

project( MCPL VERSION 1.6.2 ${_project_metadata} )

unset( _project_metadata )

if ( MCPL_ENABLE_CPACK )
  set(CPACK_PACKAGE_CONTACT "mcpl-developers@cern.ch")
  set(CPACK_NSIS_PACKAGE_NAME "${PROJECT_NAME} ${PROJECT_VERSION}")
  set(CPACK_NSIS_DISPLAY_NAME "${PROJECT_NAME} ${PROJECT_VERSION}")
  include(CPack)
endif()

if( NOT MCPL_NOTOUCH_CMAKE_BUILD_TYPE )
  if ( NOT gen_is_multicfg )
    if ( "x${CMAKE_BUILD_TYPE}" STREQUAL "x" )
      #This can happen if parent project called the project(..) function before
      #doing the song and dance we did above.
      set( CMAKE_BUILD_TYPE Release )
    endif()
  endif()
endif()

# Set module path
set( CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_CURRENT_LIST_DIR}/cmake/modules")

#Define options:
include(mcpl_options)

#Installation directories (try to follow standard conventions):
include(GNUInstallDirs)
set(MCPL_BINDIR "${CMAKE_INSTALL_BINDIR}")#e.g. <prefix>/bin>
set(MCPL_LIBDIR "${CMAKE_INSTALL_LIBDIR}")#e.g. <prefix>/lib>
set(MCPL_INCDIR "${CMAKE_INSTALL_INCLUDEDIR}")#e.g. <prefix>/include>
set(MCPL_DATAROOT "${CMAKE_INSTALL_DATADIR}/${PROJECT_NAME}")#e.g. <prefix>/share/MCPL>
#set(MCPL_DATAFILESDIR "${MCPL_DATAROOT}/data")#e.g. <prefix>/share/MCPL/data>
if ( NOT MCPL_PYPATH )
  set(MCPL_PYPATH "${MCPL_DATAROOT}/python")#e.g. <prefix>/share/MCPL/python
endif()
#set(MCPL_PYMODDIR "${MCPL_PYPATH}/mcpl")#e.g. <prefix>/share/MCPL/python/mcpl
if ( NOT MCPL_CMAKEDIR )
  set(MCPL_CMAKEDIR "${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}")#e.g. <prefix>/lib/cmake/MCPL>
endif()

#Get a few relative paths, mostly for expansion in various installed files (we
#use PROJECT_BINARY_DIR as prefix here, but it should not matter which as long
#as it is an absolute path):
#file(RELATIVE_PATH MCPL_relpath_PYMODDIR2LIBDIR "${PROJECT_BINARY_DIR}/${MCPL_PYMODDIR}" "${PROJECT_BINARY_DIR}/${MCPL_LIBDIR}")
file(RELATIVE_PATH MCPL_relpath_BINDIR2LIBDIR   "${PROJECT_BINARY_DIR}/${MCPL_BINDIR}"   "${PROJECT_BINARY_DIR}/${MCPL_LIBDIR}")
file(RELATIVE_PATH MCPL_relpath_BINDIR2PYPATH   "${PROJECT_BINARY_DIR}/${MCPL_BINDIR}"   "${PROJECT_BINARY_DIR}/${MCPL_PYPATH}")
#file(RELATIVE_PATH MCPL_relpath_BINDIR2DATAROOT "${PROJECT_BINARY_DIR}/${MCPL_BINDIR}"   "${PROJECT_BINARY_DIR}/${MCPL_DATAROOT}")
file(RELATIVE_PATH MCPL_relpath_BINDIR2CMAKEDIR "${PROJECT_BINARY_DIR}/${MCPL_BINDIR}"   "${PROJECT_BINARY_DIR}/${MCPL_CMAKEDIR}")
file(RELATIVE_PATH MCPL_relpath_BINDIR2INCDIR   "${PROJECT_BINARY_DIR}/${MCPL_BINDIR}"   "${PROJECT_BINARY_DIR}/${MCPL_INCDIR}")
file(RELATIVE_PATH MCPL_relpath_BINDIR2ROOT     "${PROJECT_BINARY_DIR}/${MCPL_BINDIR}"   "${PROJECT_BINARY_DIR}/")
file(RELATIVE_PATH MCPL_relpath_CMAKEDIR2ROOT   "${PROJECT_BINARY_DIR}/${MCPL_CMAKEDIR}" "${PROJECT_BINARY_DIR}/")
file(RELATIVE_PATH MCPL_relpath_CMAKEDIR2BINDIR   "${PROJECT_BINARY_DIR}/${MCPL_CMAKEDIR}" "${PROJECT_BINARY_DIR}/${MCPL_BINDIR}")
file(RELATIVE_PATH MCPL_relpath_CMAKEDIR2LIBDIR   "${PROJECT_BINARY_DIR}/${MCPL_CMAKEDIR}" "${PROJECT_BINARY_DIR}/${MCPL_LIBDIR}")
file(RELATIVE_PATH MCPL_relpath_CMAKEDIR2INCDIR   "${PROJECT_BINARY_DIR}/${MCPL_CMAKEDIR}" "${PROJECT_BINARY_DIR}/${MCPL_INCDIR}")
file(RELATIVE_PATH MCPL_relpath_CMAKEDIR2PYPATH   "${PROJECT_BINARY_DIR}/${MCPL_CMAKEDIR}" "${PROJECT_BINARY_DIR}/${MCPL_PYPATH}")
#file(RELATIVE_PATH MCPL_relpath_CMAKEDIR2DATAFILESDIR   "${PROJECT_BINARY_DIR}/${MCPL_CMAKEDIR}" "${PROJECT_BINARY_DIR}/${MCPL_DATAFILESDIR}")

#Dummy interface target for common properties.
add_library( mcpl_common INTERFACE )
target_compile_features( mcpl_common INTERFACE c_std_99 )
if ( NOT MCPL_DISABLE_CXX )
  target_compile_features( mcpl_common INTERFACE cxx_std_11 )
endif()

#Properties for binaries / executables (can't transfer all properties via
#INTERFACE targets, so we need this variable-based workaround):
set( binaryprops "" )#empty list

if ( MODIFY_RPATH )
  #Set RPATH properties. For some annoying reason, this is not possible to do
  #via interface targets, so we have to use a variable-based workaround:
  if ( NOT DEFINED CMAKE_INSTALL_RPATH_USE_LINK_PATH )
    #TODO: Figure out if we really need this (perhaps only for geant4 targets?)
    set( CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE )
  endif()
  if( NOT APPLE )
    #Relocatable RPATHS: $ORIGIN in RPATH (including the $-char!!)  means the
    #location of the binary requiring the dependency:
    list( APPEND binaryprops INSTALL_RPATH "$ORIGIN/${MCPL_relpath_BINDIR2LIBDIR}" )
  else()
    #On OSX, rpaths are absolute paths (todo: revisit if this is still the case)
    get_filename_component( tmp "${CMAKE_INSTALL_PREFIX}/${MCPL_LIBDIR}" ABSOLUTE)
    list( APPEND binaryprops INSTALL_RPATH  "${tmp}" )
  endif()

  #Test if compiler supports -Wl,--disable-new-dtags. If it does, apply it
  #(otherwise RPATH sections in binaries become RUNPATH instead, which can be
  #overridden by users LD_LIBRARY_PATH (CMake>=3.14 is needed for LINK_OPTIONS on
  #try_compile and for the target_link_options function):
  #
  #NB: CMake 3.18 introduces CheckLinkerFlag module which we can eventually use
  #    instead of try_compile!!
  if( ${CMAKE_VERSION} VERSION_GREATER_EQUAL "3.14.0" )
    set(TMP_TESTDIR ${PROJECT_BINARY_DIR}/test_dtagflags)
    file(WRITE ${TMP_TESTDIR}/test.c "int main() { return 0; }\n")
    try_compile(LINKER_HAS_DTAGS "${TMP_TESTDIR}" "${TMP_TESTDIR}/test.c" LINK_OPTIONS -Wl,--disable-new-dtags)
    if (LINKER_HAS_DTAGS)
      #target_link_options(MCPL PUBLIC "-Wl,--disable-new-dtags")
      target_link_options( mcpl_common INTERFACE -Wl,--disable-new-dtags )
    endif()
  endif()
endif()

set(SRC "${PROJECT_SOURCE_DIR}/src")
set(SRCFAT "${PROJECT_SOURCE_DIR}/src_fat")
set(SRCEX "${PROJECT_SOURCE_DIR}/examples")
set(INSTDEST "RUNTIME;DESTINATION;${MCPL_BINDIR};LIBRARY;DESTINATION;${MCPL_LIBDIR};ARCHIVE;DESTINATION;${MCPL_LIBDIR}")

#ZLib support:
include( mcpl_zlib )
if ( MCPL_ZLIB )
  set( MCPL_ZLIB_ONOFF ON )
else()
  set( MCPL_ZLIB_ONOFF OFF )
  message("zlib support not enabled - gzipped input files will NOT be directly readable by resulting binaries.")
endif()

#Make sure we link in math functions correctly (typically the linker needs libm on unix, but nothing on Windows).
set(TMP_TESTLIBMSRC "#include <math.h>\nint main(int argc,char** argv) { (void)argv;double a=(exp)(argc+1.0); return (int)(a*0.1); }\n")
set(TMP_TESTDIR ${PROJECT_BINARY_DIR}/test_libm)
file(WRITE ${TMP_TESTDIR}/test.c "${TMP_TESTLIBMSRC}")
try_compile(ALWAYS_HAS_MATH "${TMP_TESTDIR}" "${TMP_TESTDIR}/test.c")
if (ALWAYS_HAS_MATH)
  set( MATH_NEEDS_LIBM OFF )
else()
  set( MATH_NEEDS_LIBM ON )
  set( TMP_TESTDIR ${PROJECT_BINARY_DIR}/test_libm2 )
  file( WRITE ${TMP_TESTDIR}/test.c "${TMP_TESTLIBMSRC}" )
  try_compile( tmp "${TMP_TESTDIR}" "${TMP_TESTDIR}/test.c" LINK_LIBRARIES m )
  if( NOT tmp )
    message(FATAL_ERROR "Could not figure out link flags needed to enable math functions")
  endif()
endif()

add_library( mcpl SHARED "${SRC}/mcpl/mcpl.c" )
set(MCPL_LIBNAME "${CMAKE_SHARED_LIBRARY_PREFIX}mcpl${CMAKE_SHARED_LIBRARY_SUFFIX}")
target_link_libraries( mcpl PRIVATE mcpl_common )
add_zlib_dependency( mcpl -DMCPL_HASZLIB )

target_include_directories(mcpl
 PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/src/mcpl>
        $<INSTALL_INTERFACE:${MCPL_INCDIR}> )

if (MATH_NEEDS_LIBM)
  target_link_libraries( mcpl PRIVATE m )
endif()

add_executable(mcpltool "${SRC}/mcpl/mcpltool_app.c")
target_link_libraries( mcpltool PRIVATE mcpl mcpl_common )
if (binaryprops)
  set_target_properties(mcpltool PROPERTIES ${binaryprops})
endif()

install( TARGETS mcpl mcpltool EXPORT MCPLTargets ${INSTDEST} )
install( EXPORT MCPLTargets FILE MCPLTargets.cmake NAMESPACE MCPL:: DESTINATION ${MCPL_CMAKEDIR} )
add_library(MCPL::mcpl ALIAS mcpl)#always alias namespaces locally

include(CMakePackageConfigHelpers)
write_basic_package_version_file( "${PROJECT_BINARY_DIR}/MCPLConfigVersion.cmake"
                                  VERSION ${MCPL_VERSION} COMPATIBILITY SameMajorVersion )

configure_file( "${PROJECT_SOURCE_DIR}/cmake/MCPLConfig.cmake.in"
                "${PROJECT_BINARY_DIR}/MCPLConfig.cmake" @ONLY )

install( FILES "${PROJECT_BINARY_DIR}/MCPLConfigVersion.cmake" "${PROJECT_BINARY_DIR}/MCPLConfig.cmake"
         DESTINATION ${MCPL_CMAKEDIR} )


install(FILES "${SRC}/mcpl/mcpl.h" DESTINATION ${MCPL_INCDIR})

if ( MCPL_ENABLE_SSW )
  add_library(sswmcpl SHARED "${SRC}/mcnpssw/sswmcpl.c" "${SRC}/mcnpssw/sswread.c")
  target_include_directories( sswmcpl PUBLIC "${SRC}/mcnpssw")
  target_link_libraries( sswmcpl PRIVATE mcpl mcpl_common)
  if (MATH_NEEDS_LIBM)
    target_link_libraries(sswmcpl PRIVATE m)
  endif()
  add_zlib_dependency( sswmcpl -DDSSWREAD_HASZLIB )
  add_executable(ssw2mcpl "${SRC}/mcnpssw/ssw2mcpl_app.c")
  target_link_libraries(ssw2mcpl PRIVATE sswmcpl)
  add_executable(mcpl2ssw "${SRC}/mcnpssw/mcpl2ssw_app.c")
  target_link_libraries(mcpl2ssw PRIVATE sswmcpl)
  if (binaryprops)
    set_target_properties(sswmcpl PROPERTIES ${binaryprops})
    set_target_properties(ssw2mcpl PROPERTIES ${binaryprops})
    set_target_properties(mcpl2ssw PROPERTIES ${binaryprops})
  endif()
  install(TARGETS mcpl2ssw ssw2mcpl sswmcpl ${INSTDEST})
endif()

if ( MCPL_ENABLE_PHITS )
  add_library(phitsmcpl SHARED "${SRC}/phits/phitsmcpl.c" "${SRC}/phits/phitsread.c")
  target_include_directories( phitsmcpl PUBLIC "${SRC}/phits")
  target_link_libraries( phitsmcpl PRIVATE mcpl mcpl_common )
  add_zlib_dependency( phitsmcpl -DDPHITSREAD_HASZLIB )
  add_executable(phits2mcpl "${SRC}/phits/phits2mcpl_app.c")
  target_link_libraries( phits2mcpl PRIVATE phitsmcpl )
  add_executable(mcpl2phits "${SRC}/phits/mcpl2phits_app.c")
  target_link_libraries( mcpl2phits PRIVATE phitsmcpl )
  install(TARGETS mcpl2phits phits2mcpl phitsmcpl ${INSTDEST})
  if (binaryprops)
    set_target_properties(phitsmcpl PROPERTIES ${binaryprops})
    set_target_properties(phits2mcpl PROPERTIES ${binaryprops})
    set_target_properties(mcpl2phits PROPERTIES ${binaryprops})
  endif()
endif()

if ( MCPL_ENABLE_PYTHON )
  install(FILES "${SRC}/python/mcpl.py" DESTINATION ${MCPL_PYPATH})
  install(PROGRAMS "${SRC}/python/pymcpltool" DESTINATION ${MCPL_BINDIR})
  if ( MCPL_ENABLE_EXAMPLES )
    install(PROGRAMS "${SRCEX}/pyexample_readmcpl" DESTINATION ${MCPL_BINDIR} RENAME mcplexample_pyread)
  endif()
  if ( MCPL_ENABLE_FATBINARIES )
    install(PROGRAMS "${SRCFAT}/pymcpltool" DESTINATION ${MCPL_BINDIR} RENAME pymcpltool_fat)
  endif()
endif()

if ( MCPL_ENABLE_EXAMPLES )
  add_executable( mcplexample_read "${SRCEX}/rawexample_readmcpl.c")
  target_link_libraries( mcplexample_read PRIVATE mcpl mcpl_common)
  add_executable(mcplexample_write "${SRCEX}/rawexample_writemcpl.c")
  target_link_libraries(mcplexample_write PRIVATE mcpl mcpl_common)
  add_executable(mcplexample_filter "${SRCEX}/rawexample_filtermcpl.c")
  target_link_libraries(mcplexample_filter PRIVATE mcpl mcpl_common)
  install(TARGETS mcplexample_read mcplexample_write mcplexample_filter ${INSTDEST})
  if (binaryprops)
    set_target_properties(mcplexample_read PROPERTIES ${binaryprops})
    set_target_properties(mcplexample_write PROPERTIES ${binaryprops})
    set_target_properties(mcplexample_filter PROPERTIES ${binaryprops})
  endif()
endif()

if ( MCPL_ENABLE_FATBINARIES )
  add_library(mcpl_fat SHARED "${SRCFAT}/mcpl_fat.c")
  target_include_directories(mcpl_fat PUBLIC "${SRC}/mcpl")
  add_executable(mcpltool_fat "${SRCFAT}/mcpltool_app_fat.c")
  install(TARGETS mcpl_fat mcpltool_fat ${INSTDEST})
  if (MATH_NEEDS_LIBM)
    target_link_libraries( mcpl_fat PRIVATE m mcpl_common )
    target_link_libraries( mcpltool_fat PRIVATE m mcpl_common )
  endif()
  if ( MCPL_ENABLE_SSW )
    add_executable(ssw2mcpl_fat "${SRCFAT}/ssw2mcpl_app_fat.c")
    add_executable(mcpl2ssw_fat "${SRCFAT}/mcpl2ssw_app_fat.c")
    if (MATH_NEEDS_LIBM)
      target_link_libraries( ssw2mcpl_fat PRIVATE m mcpl_common )
      target_link_libraries( mcpl2ssw_fat PRIVATE m mcpl_common )
    endif()
    install(TARGETS ssw2mcpl_fat mcpl2ssw_fat ${INSTDEST})
  endif()
  if ( MCPL_ENABLE_PHITS )
    add_executable(phits2mcpl_fat "${SRCFAT}/phits2mcpl_app_fat.c")
    add_executable(mcpl2phits_fat "${SRCFAT}/mcpl2phits_app_fat.c")
    if (MATH_NEEDS_LIBM)
      target_link_libraries( phits2mcpl_fat PRIVATE m mcpl_common )
      target_link_libraries( mcpl2phits_fat PRIVATE m mcpl_common )
    endif()
    install(TARGETS phits2mcpl_fat mcpl2phits_fat ${INSTDEST})
  endif()
endif()

if ( MCPL_ENABLE_GEANT4 )
  if ( MCPL_DISABLE_CXX )
    message(FATAL_ERROR "Do not use MCPL_ENABLE_GEANT4 with MCPL_DISABLE_CXX.")
  endif()
  find_package( Geant4 )
  if( NOT Geant4_FOUND )
    message(FATAL_ERROR "MCPL_ENABLE_GEANT4 set to ON but failed to enable Geant4 support.")
  endif()
else()
  set(Geant4_FOUND NO)
endif()

if (Geant4_FOUND)
  add_library(g4mcpl SHARED "${SRC}/geant4/G4MCPLGenerator.cc" "${SRC}/geant4/G4MCPLWriter.cc")
  set(G4MCPL_LIBNAME "${CMAKE_SHARED_LIBRARY_PREFIX}g4mcpl${CMAKE_SHARED_LIBRARY_SUFFIX}")
  target_link_libraries( g4mcpl PUBLIC mcpl ${Geant4_LIBRARIES} PRIVATE mcpl_common )
  target_include_directories(g4mcpl
    PUBLIC
    $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/src/geant4>
    $<INSTALL_INTERFACE:${MCPL_INCDIR}>
    )
  target_include_directories(g4mcpl SYSTEM PUBLIC ${Geant4_INCLUDE_DIRS})
  if (binaryprops)
    set_target_properties(g4mcpl PROPERTIES ${binaryprops})
  endif()
  install( TARGETS g4mcpl EXPORT G4MCPLTargets ${INSTDEST} )
  install( EXPORT G4MCPLTargets FILE G4MCPLTargets.cmake NAMESPACE MCPL:: DESTINATION ${MCPL_CMAKEDIR} )
  add_library(MCPL::g4mcpl ALIAS g4mcpl)#always alias namespaces locally

  install(FILES "${SRC}/geant4/G4MCPLGenerator.hh" "${SRC}/geant4/G4MCPLWriter.hh" DESTINATION ${MCPL_INCDIR})
  if ( MCPL_ENABLE_EXAMPLES )
    add_executable(mcplexample_geant4read "${SRCEX}/g4example_readmcpl.cc")
    target_link_libraries(mcplexample_geant4read PRIVATE g4mcpl mcpl_common)
    add_executable(mcplexample_geant4write "${SRCEX}/g4example_writemcpl.cc")
    target_link_libraries(mcplexample_geant4write PRIVATE g4mcpl mcpl_common)
    if (binaryprops)
      set_target_properties(mcplexample_geant4read PROPERTIES ${binaryprops})
      set_target_properties(mcplexample_geant4write PROPERTIES ${binaryprops})
    endif()
    install(TARGETS mcplexample_geant4read mcplexample_geant4write ${INSTDEST})
  endif()
endif()

#Always provide mcpl-config:
configure_file( "${PROJECT_SOURCE_DIR}/cmake/mcpl-config.in" "${PROJECT_BINARY_DIR}/mcpl-config" @ONLY )
install( PROGRAMS "${PROJECT_BINARY_DIR}/mcpl-config" DESTINATION ${MCPL_BINDIR} )
