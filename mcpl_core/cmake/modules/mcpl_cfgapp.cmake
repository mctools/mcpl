
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

function( mcplcfgapp_create_mcplconfig_h targetfile expects_shlibdir_override )
  #Generate mcplconfig.h via file(GENERATE ..) from template. Supports generator
  #expressions in both targetfile and template contents.
  if ( expects_shlibdir_override )
    set( mcplcfgapp_expect_shlibdir_override_01 "1" )
  else()
    set( mcplcfgapp_expect_shlibdir_override_01 "0" )
  endif()
  if ( UNIX )
    set( MCPL_libname_genexp "$<TARGET_FILE_NAME:mcpl>" )
    set( MCPL_shlibname_genexp "$<TARGET_FILE_NAME:mcpl>" )
  else()
    set( MCPL_libname_genexp "$<TARGET_IMPORT_FILE_NAME:mcpl>" )
    set( MCPL_shlibname_genexp "$<TARGET_FILE_NAME:mcpl>" )
  endif()
  set( t1 "1000000 * ${MCPL_VERSION_MAJOR}" )
  set( t2 "1000 * ${MCPL_VERSION_MINOR}" )
  set( t3 "${MCPL_VERSION_PATCH}" )
  math(EXPR mcplcfgapp_intversion "(${t1})+(${t2})+(${t3})" )
  #First generated a configured version of the template:
  configure_file(
    "${MCPL_SOURCE_DIR}/cmake/template_mcplconfig.h"
    "${PROJECT_BINARY_DIR}/template_mcplconfig.h.configured"
    @ONLY
  )
  #At build-time, generate the actual files needed for inclusion, expanding any
  #generator-expressions:
  file(
    GENERATE
    OUTPUT "${targetfile}"
    INPUT "${PROJECT_BINARY_DIR}/template_mcplconfig.h.configured"
  )
endfunction()

function( create_mcpl_config_app expects_shlibdir_override )
  set( autogenheader_name "mcplconfig_autogen_$<CONFIG>.h")
  set ( workdir "${PROJECT_BINARY_DIR}/mcplcfgapp" )

  mcplcfgapp_create_mcplconfig_h(
    "${workdir}/include/${autogenheader_name}"
    "${expects_shlibdir_override}"
  )
  configure_file(
    "${PROJECT_SOURCE_DIR}/src/mcpl_fileutils.h"
    "${workdir}/include/mcpl_fileutils.h"
    COPYONLY
  )
  configure_file(
    "${PROJECT_SOURCE_DIR}/src/mcpl_fileutils.c"
    "${workdir}/mcpl_fileutils.c"
    COPYONLY
  )
  add_executable( mcpl_cfgapp
    "${PROJECT_SOURCE_DIR}/app_config/main.c"
    "${workdir}/mcpl_fileutils.c"
    "${workdir}/include/${autogenheader_name}"
    "${workdir}/include/mcpl_fileutils.h"
  )
  set_target_properties(
    mcpl_cfgapp PROPERTIES
    OUTPUT_NAME "mcpl-config"
  )

  #C99 and C11 seems to be OK for most systems. Using C99 to be conservative
  #(could be reconsidered if we need it):
  set_target_properties( mcpl_cfgapp PROPERTIES LANGUAGE C )
  target_compile_features( mcpl_cfgapp PUBLIC c_std_99 )
  target_compile_definitions(
    mcpl_cfgapp
    PUBLIC "MCPLCFGAPPHEADER=\"${autogenheader_name}\""
  )
  target_include_directories( mcpl_cfgapp PUBLIC "${workdir}/include" )

  #Note, we install in MCPL_BINDIR even if SKBUILD_SCRIPTS_DIR is
  #set.
  install( TARGETS mcpl_cfgapp DESTINATION "${MCPL_BINDIR}" )
endfunction()
