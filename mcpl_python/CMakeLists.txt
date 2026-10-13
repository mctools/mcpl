
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

#Installs the pure-Python mcpl module and the pymcpltool command into a
#system (Debian-style) layout, and can package them with CPack as the Debian
#package python3-mcpl. For pip installations use pyproject.toml instead.

cmake_minimum_required(VERSION 3.16...4.4)

file( STRINGS "${CMAKE_CURRENT_LIST_DIR}/src/mcpl/__init__.py" _v
  REGEX "^__version__ *= *'[0-9.]+'" )
string( REGEX MATCH "[0-9.]+" _v "${_v}" )

project( MCPLPython VERSION ${_v} LANGUAGES NONE
  DESCRIPTION "Utilities and API for accessing MCPL (.mcpl) files"
  HOMEPAGE_URL "https://github.com/mctools/mcpl"
)

set( MCPL_PYTHON_MODDIR "lib/python3/dist-packages" CACHE STRING
  "Destination of the mcpl Python module (relative to install prefix)" )

install( DIRECTORY "${PROJECT_SOURCE_DIR}/src/mcpl"
  DESTINATION "${MCPL_PYTHON_MODDIR}"
  PATTERN "__pycache__" EXCLUDE
)

#Same as the pymcpltool entry point in pyproject.toml:
file( WRITE "${PROJECT_BINARY_DIR}/pymcpltool"
  "#!/usr/bin/python3\nfrom mcpl._cli import main\nmain()\n" )
install( PROGRAMS "${PROJECT_BINARY_DIR}/pymcpltool"
  DESTINATION bin )

if ( MCPL_ENABLE_CPACK )
  set( CPACK_PACKAGE_NAME "python3-mcpl" )
  set( CPACK_PACKAGE_CONTACT "MCPL developers <mcpl-developers@cern.ch>" )
  set( CPACK_DEBIAN_FILE_NAME DEB-DEFAULT )
  set( CPACK_DEBIAN_PACKAGE_ARCHITECTURE "all" )
  set( CPACK_DEBIAN_PACKAGE_SECTION "python" )
  #Mirrors dependencies and optional-dependencies in pyproject.toml:
  set( CPACK_DEBIAN_PACKAGE_DEPENDS "python3 (>= 3.9), python3-numpy (>= 1:1.22)" )
  set( CPACK_DEBIAN_PACKAGE_RECOMMENDS "mcpl (= ${PROJECT_VERSION})" )
  set( CPACK_DEBIAN_PACKAGE_SUGGESTS "python3-matplotlib, python3-plotly" )
  set( CPACK_DEBIAN_PACKAGE_DESCRIPTION "Python module (mcpl) and the pymcpltool command for reading, writing,\ninspecting and plotting MCPL (.mcpl) particle list files." )
  file( WRITE "${PROJECT_BINARY_DIR}/debian/copyright"
    "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/\n"
    "Upstream-Name: MCPL\nSource: https://github.com/mctools/mcpl\n\n"
    "Files: *\nCopyright: 2015-2026 MCPL developers\nLicense: Apache-2.0\n"
    " On Debian systems, the full text of the Apache License, Version 2.0\n"
    " can be found in /usr/share/common-licenses/Apache-2.0.\n" )
  install( FILES "${PROJECT_BINARY_DIR}/debian/copyright"
    DESTINATION "share/doc/python3-mcpl" )
  include( "${PROJECT_SOURCE_DIR}/../mcpl_core/cmake/modules/mcpl_debchangelog.cmake" OPTIONAL )
  if ( COMMAND mcpl_install_debian_changelog )
    mcpl_install_debian_changelog( "python3-mcpl" "${CPACK_PACKAGE_CONTACT}" )
  endif()
  #Byte-compile on install and clean up on removal (like dh_python3 does):
  file( WRITE "${PROJECT_BINARY_DIR}/debian/postinst"
    "#!/bin/sh\nset -e\nif command -v py3compile >/dev/null 2>&1; then\n"
    "  py3compile -p python3-mcpl\nfi\n" )
  file( WRITE "${PROJECT_BINARY_DIR}/debian/prerm"
    "#!/bin/sh\nset -e\nif command -v py3clean >/dev/null 2>&1; then\n"
    "  py3clean -p python3-mcpl\nfi\n" )
  set( CPACK_DEBIAN_PACKAGE_CONTROL_STRICT_PERMISSION ON )
  set( CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA
    "${PROJECT_BINARY_DIR}/debian/postinst;${PROJECT_BINARY_DIR}/debian/prerm" )
  include(CPack)
endif()
