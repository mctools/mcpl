
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

#ifndef MCPL_testmodutils_h
#define MCPL_testmodutils_h

/* inline functions for implementing compiled test modules (to be loaded with */
/* the Lib class from loadlib.py.                                             */

#if defined (_WIN32) || defined (__CYGWIN__) || defined (WIN32)
#  define MCPLTEST_API __declspec(dllexport)
#elif defined(__GNUC__) || defined(__clang__)
#  define MCPLTEST_API __attribute__ ((visibility ("default")))
#else
#  define MCPLTEST_API
#endif
#ifdef __cplusplus
#  define MCPLTEST_CTYPES extern "C" MCPLTEST_API
#else
#  define MCPLTEST_CTYPES MCPLTEST_API
#endif

#define MCPLTEST_CTYPE_DICTIONARY MCPLTEST_CTYPES const char * mcpltest_ctypes_dictionary()

#ifndef MCPLTESTMODUTILS_NO_MCPL_INCLUDE
#  include "mcpl.h"
#endif


#endif
