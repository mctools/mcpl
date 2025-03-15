
/******************************************************************************/
/*                                                                            */
/*  This file is part of MCPL (see https://mctools.github.io/mcpl/)           */
/*                                                                            */
/*  Copyright 2015-2025 MCPL developers.                                      */
/*                                                                            */
/*  Licensed under the Apache License, Version 2.0 (the "License");           */
/*  you may not use this file except in compliance with the License.          */
/*  You may obtain a copy of the License at                                   */
/*                                                                            */
/*      http://www.apache.org/licenses/LICENSE-2.0                            */
/*                                                                            */
/*  Unless required by applicable law or agreed to in writing, software       */
/*  distributed under the License is distributed on an "AS IS" BASIS,         */
/*  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  */
/*  See the License for the specific language governing permissions and       */
/*  limitations under the License.                                            */
/*                                                                            */
/******************************************************************************/

//Note about this template: At CMake configuration time, the AT-SIGN enclosed
//CMake variables are expanded. Then at CMake build time, the Generator
//expressions are expanded.

const char * mcplcfg_const_bin2libdir(void) { return "@MCPL_relpath_BINDIR2LIBDIR@"; }
const char * mcplcfg_const_bin2shlibdir(void) { return "@MCPL_relpath_BINDIR2SHLIBDIR@"; }
const char * mcplcfg_const_libname(void) { return "@MCPL_libname_genexp@"; }//NB: generator expression
const char * mcplcfg_const_shlibname(void) { return "@MCPL_shlibname_genexp@"; }//NB: generator expression
const char * mcplcfg_const_bin2libpath(void) { return "@MCPL_relpath_BINDIR2LIBDIR@/@MCPL_libname_genexp@"; }
const char * mcplcfg_const_bin2shlibpath(void) { return "@MCPL_relpath_BINDIR2SHLIBDIR@/@MCPL_shlibname_genexp@"; }
const char * mcplcfg_const_bin2incdir(void) { return "@MCPL_relpath_BINDIR2INCDIR@"; }
const char * mcplcfg_const_bin2cmakedir(void) { return "@MCPL_relpath_BINDIR2CMAKEDIR@"; }
const char * mcplcfg_const_version(void) { return "@MCPL_VERSION@"; }
const char * mcplcfg_const_intversion(void) { return "@mcplcfgapp_intversion@"; }
//const char * mcplcfg_const_namespace(void) { return "@MCPL_NAMESPACE@"; }
const char * mcplcfg_const_cmakebuildtype(void) { return "$<CONFIG>"; }//NB: generator expression
int mcplcfg_boolopt_expects_shlibdir_override(void) { return @mcplcfgapp_expect_shlibdir_override_01@; }
