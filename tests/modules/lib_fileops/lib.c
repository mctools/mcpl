
////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  This file is part of MCPL (see https://mctools.github.io/mcpl/)           //
//                                                                            //
//  Copyright 2015-2026 MCPL developers.                                      //
//                                                                            //
//  Licensed under the Apache License, Version 2.0 (the "License");           //
//  you may not use this file except in compliance with the License.          //
//  You may obtain a copy of the License at                                   //
//                                                                            //
//      http://www.apache.org/licenses/LICENSE-2.0                            //
//                                                                            //
//  Unless required by applicable law or agreed to in writing, software       //
//  distributed under the License is distributed on an "AS IS" BASIS,         //
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  //
//  See the License for the specific language governing permissions and       //
//  limitations under the License.                                            //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "mcpltestmodutils.h"
#include "mcpltest_errstate.h"

//The file operations of the C library which mcpltool-c gave on the command
//line (dumps, merges, repairs, and gzipping), with the variants with error
//states, so the tests (tests/scripts/cfileops.py) can do what mcpltool-c did
//with the C library, and see its errors. Each returns "ok", or the error.

MCPLTEST_CTYPE_DICTIONARY
{
  return
    "const char * mcpltest_merge( const char *, const char *, int, int );"
    "const char * mcpltest_merge_inplace( const char *, const char * );"
    "int mcpltest_can_merge( const char *, const char * );"
    "const char * mcpltest_repair( const char * );"
    "const char * mcpltest_gzip( const char * );"
    "const char * mcpltest_dump( const char *, int, unsigned, unsigned, const char * );"
    ;
}

static char mcpltest_result_buffer[2048];

static const char * mcpltest_result( const mcpl_errstate_t * es )
{
  if ( !es->code )
    return "ok";
  const char * kind = ( es->code == MCPL_ERROR_IO ? "I/O error"
                        : es->code == MCPL_ERROR_MEMORY ? "memory error"
                        : "error" );
  snprintf( mcpltest_result_buffer, sizeof(mcpltest_result_buffer),
            "%s: %s", kind, es->msg );
  return mcpltest_result_buffer;
}

//Merges the files (their names separated by newlines) into the new file
//output, with mcpl_forcemerge_files if force is set (keeping the userflags
//if keepuserflags is set), else with mcpl_merge_files:
MCPLTEST_CTYPES const char * mcpltest_merge( const char * output,
                                             const char * filenames,
                                             int force, int keepuserflags )
{
  mcpl_errstate_t es;
  es.code = 0;
  char buf[4096];
  const char * files[64];
  unsigned nfiles = 0;
  snprintf( buf, sizeof(buf), "%s", filenames );
  for ( char * s = buf; *s && nfiles < 64; ) {
    files[nfiles++] = s;
    char * nl = strchr(s,'\n');
    if ( !nl )
      break;
    *nl = '\0';
    s = nl + 1;
  }
  mcpl_outfile_t f = ( force
                       ? mcpl_forcemerge_files_es( output, nfiles, files,
                                                   keepuserflags, 0, &es )
                       : mcpl_merge_files_es( output, nfiles, files, 0, &es ) );
  if ( !es.code )
    mcpl_close_outfile_es( f, &es );
  return mcpltest_result( &es );
}

MCPLTEST_CTYPES const char * mcpltest_merge_inplace( const char * file1,
                                                     const char * file2 )
{
  mcpl_errstate_t es;
  es.code = 0;
  mcpl_merge_inplace_es( file1, file2, &es );
  return mcpltest_result( &es );
}

//Whether the files can be merged (1 or 0), or -1 if they can not be opened:
MCPLTEST_CTYPES int mcpltest_can_merge( const char * file1, const char * file2 )
{
  mcpl_errstate_t es;
  es.code = 0;
  int res = mcpl_can_merge_es( file1, file2, &es );
  return es.code ? -1 : res;
}

MCPLTEST_CTYPES const char * mcpltest_repair( const char * filename )
{
  mcpl_errstate_t es;
  es.code = 0;
  mcpl_repair_es( filename, &es );
  return mcpltest_result( &es );
}

MCPLTEST_CTYPES const char * mcpltest_gzip( const char * filename )
{
  mcpl_errstate_t es;
  es.code = 0;
  mcpl_gzip_file_es( filename, &es );
  return mcpltest_result( &es );
}

static void mcpltest_write_output( const char * msg, void * ctx )
{
  fputs( msg, (FILE*)ctx );
}

//Prints the header (parts 0 or 1) and the particles (parts 0 or 2) of the
//file, nlimit (0: all) of them after the first nskip, with the print handler,
//or into the file output (as bytes, if not empty):
MCPLTEST_CTYPES const char * mcpltest_dump( const char * filename, int parts,
                                            unsigned nskip, unsigned nlimit,
                                            const char * output )
{
  mcpl_errstate_t es;
  es.code = 0;
  FILE * out = NULL;
  if ( *output ) {
    out = mcpltest_fopen( output, "wb" );
    if ( !out )
      return "error: can not open the output file of the dump";
  }
  mcpl_file_t f = mcpl_open_file_es( filename, &es );
  int opened = !es.code;
  if ( opened )
    mcpl_dump_file_es( f, parts, nskip, nlimit,
                       out ? mcpltest_write_output : NULL, out, &es );
  if ( f.internal )
    mcpl_close_file( f );
  if ( out )
    fclose( out );
  //(failures to open the file are marked, as the dump then has nothing):
  const char * res = mcpltest_result( &es );
  if ( !opened ) {
    //(res can be in mcpltest_result_buffer, so it is copied first):
    char tmp[1024];
    snprintf( tmp, sizeof(tmp), "%.1000s", res );
    snprintf( mcpltest_result_buffer, sizeof(mcpltest_result_buffer),
              "%s (when opening)", tmp );
    return mcpltest_result_buffer;
  }
  return res;
}
