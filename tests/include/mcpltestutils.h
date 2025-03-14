
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

#endif
