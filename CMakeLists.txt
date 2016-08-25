##################################################################################
#                                                                                #
# Example CMake file which can be used to compile and link all files distributed #
# with MCPL. Obviously, in many cases, users will simply copy a few source files #
# into their existing setup, and build them using whatever system they use to    #
# build the rest of their code.                                             .    #
#                                                                                #
# One way to invoke cmake to build and install would be like this:               #
#                                                                                #
#  $> cmake /path/to/sourcedir -DCMAKE_INSTALL_PREFIX=/path/to/installdir        #
#                                                                                #
# Followed by:                                                                   #
#                                                                                #
#  $> make install                                                               #
#                                                                                #
# Written 2016 by T. Kittelmann.                                                 #
#                                                                                #
##################################################################################

cmake_minimum_required(VERSION 3.0.0)

project(MCPL CXX C)

set(BUILD_EXAMPLES  ON CACHE STRING "Whether to build examples.")
set(BUILD_WITHZLIB  ON CACHE STRING "Whether to link with ZLib if available.")
set(BUILD_WITHSSW   ON CACHE STRING "Whether to build the MCPL-SSW converters.")
set(BUILD_WITHG4    ON CACHE STRING "Whether to build Geant4 plugins if Geant4 is available.")
set(BUILD_FAT      OFF CACHE STRING "Whether to also build the fat binaries.")

if (NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

if (CMAKE_VERSION VERSION_LESS "3.1")
  set (CMAKE_C_FLAGS "--std=c99 ${CMAKE_C_FLAGS}")
else ()
  set (CMAKE_C_STANDARD 99)
endif ()

if (CMAKE_VERSION VERSION_LESS "3.1")
  set (CMAKE_CXX_FLAGS "--std=c++0x ${CMAKE_CXX_FLAGS}")
else ()
  set (CMAKE_CXX_STANDARD 11)
endif ()

set(SRC "${CMAKE_CURRENT_SOURCE_DIR}/src")
set(SRCFAT "${CMAKE_CURRENT_SOURCE_DIR}/src_fat")
set(SRCEX "${CMAKE_CURRENT_SOURCE_DIR}/examples")
set(INSTDEST "RUNTIME;DESTINATION;bin;LIBRARY;DESTINATION;lib;ARCHIVE;DESTINATION;lib")

add_library(mcpl SHARED "${SRC}/mcpl/mcpl.c")
target_include_directories(mcpl PUBLIC "${SRC}/mcpl")
target_link_libraries(mcpl m)
add_executable(mcpltool "${SRC}/mcpl/mcpltool_app.c")
target_link_libraries(mcpltool mcpl)
install(TARGETS mcpl mcpltool ${INSTDEST})
install(FILES "${SRC}/mcpl/mcpl.h" DESTINATION include)

if (BUILD_WITHSSW)
  add_library(sswmcpl SHARED "${SRC}/mcnpssw/sswmcpl.c" "${SRC}/mcnpssw/sswread.c")
  target_include_directories(sswmcpl PUBLIC "${SRC}/mcnpssw")
  target_link_libraries(sswmcpl mcpl m)
  add_executable(ssw2mcpl "${SRC}/mcnpssw/ssw2mcpl_app.c")
  target_link_libraries(ssw2mcpl sswmcpl)
  add_executable(mcpl2ssw "${SRC}/mcnpssw/mcpl2ssw_app.c")
  target_link_libraries(mcpl2ssw sswmcpl)
  install(TARGETS mcpl2ssw ssw2mcpl sswmcpl ${INSTDEST})
endif()

if (BUILD_EXAMPLES)
  add_executable(mcplexample_read "${SRCEX}/rawexample_readmcpl.c")
  target_link_libraries(mcplexample_read mcpl)
  add_executable(mcplexample_write "${SRCEX}/rawexample_writemcpl.c")
  target_link_libraries(mcplexample_write mcpl)
  add_executable(mcplexample_filter "${SRCEX}/rawexample_filtermcpl.c")
  target_link_libraries(mcplexample_filter mcpl)
  install(TARGETS mcplexample_read mcplexample_write mcplexample_filter ${INSTDEST})
endif()

if (BUILD_FAT)
  add_library(mcpl_fat SHARED "${SRCFAT}/mcpl_fat.c")
  target_include_directories(mcpl_fat PUBLIC "${SRC}/mcpl")
  target_link_libraries(mcpl_fat m)
  add_executable(mcpltool_fat "${SRCFAT}/mcpltool_app_fat.c")
  target_link_libraries(mcpltool_fat m)
  install(TARGETS mcpl_fat mcpltool_fat ${INSTDEST})
  if (BUILD_WITHSSW)
    add_executable(ssw2mcpl_fat "${SRCFAT}/ssw2mcpl_app_fat.c")
    target_link_libraries(ssw2mcpl_fat m)
    add_executable(mcpl2ssw_fat "${SRCFAT}/mcpl2ssw_app_fat.c")
    target_link_libraries(mcpl2ssw_fat m)
    install(TARGETS ssw2mcpl_fat mcpl2ssw_fat ${INSTDEST})
  endif()
endif()

if (BUILD_WITHZLIB)
  find_package(ZLIB)
  if(NOT ZLIB_FOUND)
    message("BUILD_WITHZLIB set to ON but failed to enable zlib support.")
  endif()
else()
  set(ZLIB_FOUND NO)
endif()

if(ZLIB_FOUND)
  target_compile_definitions(mcpl PRIVATE "-DMCPL_HASZLIB")
  target_include_directories(mcpl SYSTEM PRIVATE ${ZLIB_INCLUDE_DIRS})
  target_link_libraries(mcpl ${ZLIB_LIBRARIES})
  if (BUILD_WITHSSW)
    target_compile_definitions(sswmcpl PRIVATE "-DSSWREADER_HASZLIB")
    target_include_directories(sswmcpl SYSTEM PRIVATE ${ZLIB_INCLUDE_DIRS})
  endif()
else()
  message("zlib support not enabled - gzipped input files will NOT be directly readable by resulting binaries.")
endif()


if (BUILD_WITHG4)
  find_package(Geant4)
  if(NOT Geant4_FOUND)
    message("BUILD_WITHG4 set to ON but failed to enable Geant4 support.")
  endif()
else()
  set(Geant4_FOUND NO)
endif()

if (Geant4_FOUND)
  add_library(g4mcpl SHARED "${SRC}/geant4/G4MCPLGenerator.cc" "${SRC}/geant4/G4MCPLWriter.cc")
  target_link_libraries(g4mcpl mcpl ${Geant4_LIBRARIES})
  target_include_directories(g4mcpl PUBLIC "${SRC}/geant4")
  target_include_directories(g4mcpl SYSTEM PUBLIC ${Geant4_INCLUDE_DIRS})
  install(TARGETS g4mcpl ${INSTDEST})
  install(FILES "${SRC}/geant4/G4MCPLGenerator.hh" "${SRC}/geant4/G4MCPLWriter.hh" DESTINATION include)
  if (BUILD_EXAMPLES)
    add_executable(mcplexample_geant4read "${SRCEX}/g4example_readmcpl.cc")
    target_link_libraries(mcplexample_geant4read g4mcpl)
    add_executable(mcplexample_geant4write "${SRCEX}/g4example_writemcpl.cc")
    target_link_libraries(mcplexample_geant4write g4mcpl)
    install(TARGETS mcplexample_geant4read mcplexample_geant4write ${INSTDEST})
  endif()
endif()
