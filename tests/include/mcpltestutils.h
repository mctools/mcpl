
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

#ifndef mcpltestutils_h
#define mcpltestutils_h

#include <stdlib.h>
#include <string.h>

#if 1
#ifdef _MSC_VER
#  pragma warning( push )
#  pragma warning( disable : 4996 )
#endif
const char * mcpltests_find_data( const char * subpath1, const char * subpath2 )
{
  //Quick and dirty, not MT safe.
  const char * datadir = getenv("MCPL_TESTDATA_DIR");
  if (!datadir)
    return "MCPL_TESTDATA_DIR/NOT/SET";
  static char buffer[32768+1];
  buffer[0] = '\0';
  strncat(buffer,datadir,16384);
#ifdef _WIN32
  const char * sep = "\\";
#else
  const char * sep = "/";
#endif
  if ( subpath1 ) {
    strncat(buffer,sep,2);
    strncat(buffer,subpath1,16384);
  }
  if ( subpath2 ) {
    strncat(buffer,sep,2);
    strncat(buffer,subpath2,16384);
  }
  return buffer;
}
#ifdef _MSC_VER
#  pragma warning( pop )
#endif


#else
//If only we could use the common C fileutils:
const char * mcpltests_find_data( const char * subpath1, const char * subpath2 )
{
  //Quick and dirty, not MT safe.
  mcu8str varname = mcu8str_view_cstr("MCPL_TESTDATA_DIR");
  mcu8str f = mctools_getenv( &varname );
  if (!f.c_str)
    return "MCPL_TESTDATA_DIR/NOT/SET";
#ifdef _WIN32
  const char * sep = "\\";
#else
  const char * sep = "/";
#endif
  if ( subpath1 ) {
    mcu8str_append_cstr( &f, sep );
    mcu8str_append_cstr( &f, subpath1 );
  }
  if ( subpath2 ) {
    mcu8str_append_cstr( &f, sep );
    mcu8str_append_cstr( &f, subpath2 );
  }
  char buf[4096];
  if ( sizeof(buf) < f.size + 1 ) {
    printf("ERROR: mcpltests_find_data buffer too small");
    exit(1);
  }
  memcpy(buf,f.c_str,f.size+1);
  mcu8str_dealloc(&f);
  return buf;
}
#endif

#endif
