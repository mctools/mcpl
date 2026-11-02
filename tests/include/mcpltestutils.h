
/******************************************************************************/
/*                                                                            */
/*  This file is part of MCPL (see https://mctools.github.io/mcpl/)           */
/*                                                                            */
/*  Copyright 2015-2026 MCPL developers.                                      */
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if 1
const char * mcpltests_find_data( const char * subpath1, const char * subpath2 )
{
  //Quick and dirty, not MT safe.
#ifdef _MSC_VER
  //(getenv gives a warning with MSVC):
  static char * datadir = NULL;
  if ( !datadir ) {
    size_t n = 0;
    if ( _dupenv_s( &datadir, &n, "MCPL_TESTDATA_DIR" ) != 0 )
      datadir = NULL;
  }
#else
  const char * datadir = getenv("MCPL_TESTDATA_DIR");
#endif
  if (!datadir)
    return "MCPL_TESTDATA_DIR/NOT/SET";
#ifdef _WIN32
  const char * sep = "\\";
#else
  const char * sep = "/";
#endif
  static char buffer[32768+1];
  snprintf( buffer, sizeof(buffer), "%.16384s%s%.8000s%s%.8000s", datadir,
            subpath1 ? sep : "", subpath1 ? subpath1 : "",
            subpath2 ? sep : "", subpath2 ? subpath2 : "" );
  return buffer;
}


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
