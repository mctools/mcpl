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

#ifndef mcpltest_errstate_h
#define mcpltest_errstate_h

/* Utilities for tests of the functions with error states (the _es variants). */

#include "mcpl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _MSC_VER
#  include <share.h>
#endif

#ifdef _MSC_VER
#  define MCPLTEST_INLINE __inline
#else
#  define MCPLTEST_INLINE inline
#endif

/* fopen (MSVC deprecates fopen, so _fsopen, which shares files like fopen,   */
/* is used there):                                                           */
static MCPLTEST_INLINE FILE * mcpltest_fopen( const char * filename,
                                             const char * mode )
{
#ifdef _MSC_VER
  return _fsopen( filename, mode, _SH_DENYNO );
#else
  return fopen( filename, mode );
#endif
}

////////////////////////////////////////////////////////////////////////////////
// Utilities

static MCPLTEST_INLINE void test_fail( const char * msg )
{
  printf("TEST FAILURE: %s\n",msg);
  exit(1);
}

typedef struct {
  unsigned char * data;
  size_t size;
} buffer_t;

static MCPLTEST_INLINE buffer_t file_load( const char * filename )
{
  buffer_t b;
  FILE * fh = mcpltest_fopen(filename,"rb");
  if (!fh)
    test_fail("could not open file for reading");
  fseek(fh,0,SEEK_END);
  long n = ftell(fh);
  fseek(fh,0,SEEK_SET);
  b.size = (size_t)n;
  b.data = (unsigned char*)malloc(b.size ? b.size : 1);
  if ( fread(b.data,1,b.size,fh) != b.size )
    test_fail("could not read file");
  fclose(fh);
  return b;
}

static MCPLTEST_INLINE void file_save( const char * filename, const unsigned char * data,
                       size_t n )
{
  FILE * fh = mcpltest_fopen(filename,"wb");
  if (!fh)
    test_fail("could not open file for writing");
  if ( n && fwrite(data,1,n,fh) != n )
    test_fail("could not write file");
  fclose(fh);
}

static MCPLTEST_INLINE size_t buf_find( const buffer_t * b, const char * needle )
{
  //(no code after test_fail, since MSVC warns about unreachable code)
  size_t n = strlen(needle);
  size_t i = 0;
  while ( i + n <= b->size && memcmp( b->data + i, needle, n ) != 0 )
    ++i;
  if ( i + n > b->size )
    test_fail("buf_find: needle not found");
  return i;
}

//Save a modified copy of a buffer (n bytes, replacing nrepl bytes at pos):
static MCPLTEST_INLINE void save_modified( const char * filename, const buffer_t * b,
                           size_t n, size_t pos, const void * repl,
                           size_t nrepl )
{
  if ( n > b->size || pos > b->size || nrepl > b->size - pos )
    test_fail("save_modified: out of bounds");
  unsigned char * d = (unsigned char*)malloc(b->size ? b->size : 1);
  if (!d)
    test_fail("save_modified: memory allocation failed");
  if ( b->size )
    memcpy(d,b->data,b->size);
  if ( nrepl )
    memcpy( d + pos, repl, nrepl );
  file_save( filename, d, n );
  free(d);
}

//NaN and infinity (via strtod, since compilers warn about divisions by zero
//and overflowing constants):
static MCPLTEST_INLINE double mcpltest_nan(void)
{
  return strtod("nan",NULL);
}

static MCPLTEST_INLINE double mcpltest_inf(void)
{
  return strtod("inf",NULL);
}

static MCPLTEST_INLINE void quiet_print_handler( const char * msg )
{
  (void)msg;
}

//gzip file (creating filename.gz and removing filename), without printouts:
static MCPLTEST_INLINE void quiet_gzip( const char * filename )
{
  mcpl_set_print_handler(quiet_print_handler);
  if (!mcpl_gzip_file(filename))
    test_fail("mcpl_gzip_file failed");
  mcpl_set_print_handler(NULL);
}

////////////////////////////////////////////////////////////////////////////////
// Error states

#define ES_UNTOUCHED_CODE (-7)

static MCPLTEST_INLINE void es_reset( mcpl_errstate_t * es )
{
  //Fill with markers, to check that functions always set the code, but only
  //write the message in case of errors:
  memset(es,'x',sizeof(*es));
  es->code = ES_UNTOUCHED_CODE;
  es->reserved = -7;
  memcpy(es->msg,"untouched",10);
}

static MCPLTEST_INLINE int es_failed( const mcpl_errstate_t * es )
{
  if ( es->code == ES_UNTOUCHED_CODE )
    test_fail("error code not set");
  if ( es->code == 0 ) {
    if ( strcmp(es->msg,"untouched") != 0 )
      test_fail("error message written without an error");
    return 0;
  }
  if ( es->code < 1 || es->code > 3 )
    test_fail("invalid error code");

  if ( strlen(es->msg) >= sizeof(es->msg) )
    test_fail("message not terminated");
  return 1;
}

static MCPLTEST_INLINE const char * code_name( int code )
{
  switch (code) {
  case MCPL_ERROR_RUNTIME: return "RUNTIME";
  case MCPL_ERROR_IO: return "IO";
  case MCPL_ERROR_MEMORY: return "MEMORY";
  default: return "??";
  }
}

static MCPLTEST_INLINE void print_result( const char * what, const mcpl_errstate_t * es )
{
  if ( es_failed(es) )
    printf("%s -> ERROR %s: %s\n",what,code_name(es->code),es->msg);
  else
    printf("%s -> ok\n",what);
}

#endif
