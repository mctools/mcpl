
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

//Tests of errors while writing data to files (like with full disks), which
//are emulated with a limit on the size of files (RLIMIT_FSIZE). Errors must
//leave output files unusable (but closable), and the files left on disk must
//be recoverable when their headers were written completely. Since when
//errors are detected depends on the buffering in the C library, this test
//has no reference log, but checks its expectations itself. It is skipped on
//Windows, which has no such limits.

#include "mcpltest_errstate.h"

#ifdef _WIN32

int main( int argc, char ** argv )
{
  (void)argc;
  (void)argv;
  printf("Test skipped on Windows (no limits on file sizes)\n");
  return 0;
}

#else

#include <signal.h>
#include <sys/resource.h>

static struct rlimit original_limit;

static void set_filesize_limit( rlim_t nbytes )
{
  struct rlimit l = original_limit;
  l.rlim_cur = nbytes;
  if ( setrlimit( RLIMIT_FSIZE, &l ) != 0 )
    test_fail("could not set file size limit");
}

static void reset_filesize_limit(void)
{
  if ( setrlimit( RLIMIT_FSIZE, &original_limit ) != 0 )
    test_fail("could not reset file size limit");
}

static void fill_particle( mcpl_particle_t * p, int i )
{
  memset(p,0,sizeof(*p));
  p->position[0] = 1.0 + i;
  p->direction[2] = 1.0;
  p->ekin = 0.001 * ( i + 1 );
  p->weight = 1.0;
  p->pdgcode = 2112;
}

static long file_size( const char * filename )
{
  FILE * fh = fopen(filename,"rb");
  if (!fh)
    return -1;
  fseek(fh,0,SEEK_END);
  long n = ftell(fh);
  fclose(fh);
  return n;
}

static void expect_error( const mcpl_errstate_t * es, int code,
                          const char * what )
{
  if ( !es_failed(es) || es->code != code ) {
    printf("  %s: code %i, expected %i\n",what,es->code,code);
    test_fail("expected error not seen");
  }
  printf("  %s -> ERROR %s: %s\n",what,code_name(es->code),es->msg);
}

//Open the file (left after errors) and check that the particles it contains
//are the first ones written (returns the number of particles):
static uint64_t check_recovered( const char * filename, int expect_ok )
{
  mcpl_errstate_t es;
  es_reset(&es);
  mcpl_file_t f = mcpl_open_file_es(filename,&es);
  if ( !f.internal ) {
    if ( expect_ok )
      test_fail("could not open file left after errors");
    printf("  file left after errors (%li bytes) can not be opened: %s\n",
           file_size(filename),es.msg);
    return 0;
  }
  if ( !expect_ok )
    test_fail("file left after errors could unexpectedly be opened");
  uint64_t n = 0;
  const mcpl_particle_t * p;
  while ( ( p = mcpl_read_es(f,&es) ) ) {
    if ( p->position[0] != 1.0 + (double)n )
      test_fail("unexpected particle in file left after errors");
    ++n;
  }
  if ( es_failed(&es) )
    test_fail("error while reading file left after errors");
  printf("  file left after errors (%li bytes) has %u particles\n",
         file_size(filename),(unsigned)n);
  mcpl_close_file(f);
  return n;
}

//Write particles until an error happens (at most nmax), returning the number
//of particles written without errors, and checking that all later calls fail
//with the same error:
static unsigned write_until_error( mcpl_outfile_t f, unsigned nmax,
                                   mcpl_errstate_t * es )
{
  mcpl_particle_t p;
  unsigned n = 0;
  for ( ; n < nmax; ++n ) {
    fill_particle(&p,(int)n);
    es_reset(es);
    mcpl_add_particle_es(f,&p,es);
    if ( es_failed(es) )
      break;
  }
  if ( n == nmax )
    return n;
  expect_error(es,MCPL_ERROR_IO,"add_particle");
  //The file is now unusable:
  mcpl_errstate_t es2;
  es_reset(&es2);
  mcpl_add_particle_es(f,&p,&es2);
  if ( es2.code != es->code || strcmp(es2.msg,es->msg) != 0 )
    test_fail("different error after the first one");
  es_reset(&es2);
  mcpl_hdr_add_stat_sum_es(f,"nevents",1.0,&es2);
  if ( es2.code != es->code || strcmp(es2.msg,es->msg) != 0 )
    test_fail("different error after the first one");
  printf("  further calls fail with the same error\n");
  return n;
}

static void test_header_too_large(void)
{
  printf("\n==> Header larger than the file size limit:\n");
  mcpl_errstate_t es;
  set_filesize_limit(100);
  es_reset(&es);
  mcpl_outfile_t f = mcpl_create_outfile_es("df_header.mcpl",&es);
  char comment[1000];
  memset(comment,'c',999);
  comment[999] = '\0';
  mcpl_hdr_add_comment(f,comment);
  write_until_error(f,1000,&es);
  es_reset(&es);
  mcpl_close_outfile_es(f,&es);
  if ( es.code != 0 )
    test_fail("closing file after error failed");
  printf("  close_outfile -> ok\n");
  reset_filesize_limit();
  check_recovered("df_header.mcpl",0);
  remove("df_header.mcpl");

  //Header written only when closing (no particles):
  set_filesize_limit(100);
  es_reset(&es);
  f = mcpl_create_outfile_es("df_header2.mcpl",&es);
  mcpl_hdr_add_comment(f,comment);
  es_reset(&es);
  mcpl_close_outfile_es(f,&es);
  expect_error(&es,MCPL_ERROR_IO,"close_outfile (writing the header)");
  reset_filesize_limit();
  check_recovered("df_header2.mcpl",0);
  remove("df_header2.mcpl");
}

static void test_particles( const char * filename, int gzip )
{
  printf("\n==> Particles exceeding the file size limit%s:\n",
         gzip ? " (closing with gzip)" : "");
  mcpl_errstate_t es;
  set_filesize_limit(20000);
  es_reset(&es);
  mcpl_outfile_t f = mcpl_create_outfile_es(filename,&es);
  mcpl_hdr_add_stat_sum(f,"nevents",-1.0);
  unsigned n = write_until_error(f,100000,&es);
  printf("  %s particles were added before the error\n",
         n > 100 ? "more than 100" : "less than 100");
  es_reset(&es);
  if ( gzip ) {
    int rc = mcpl_closeandgzip_outfile_es(f,&es);
    if ( rc != 0 || es.code != 0 )
      test_fail("closing file after error failed");
  } else {
    mcpl_close_outfile_es(f,&es);
    if ( es.code != 0 )
      test_fail("closing file after error failed");
  }
  printf("  close -> ok (leaves the file unfinished)\n");
  reset_filesize_limit();
  //The file left is unfinished, but can be read (with a warning):
  uint64_t nrec = check_recovered(filename,1);
  if ( nrec == 0 || nrec > n )
    test_fail("unexpected number of particles in file left after errors");
  //And repaired:
  mcpl_repair(filename);
  if ( check_recovered(filename,1) != nrec )
    test_fail("different number of particles after repair");
  remove(filename);
}

static void test_error_at_close(void)
{
  printf("\n==> Particles exceeding the file size limit only when closing:\n");
  mcpl_errstate_t es;
  //A few particles, which are still buffered when the limit is hit:
  set_filesize_limit(300);
  es_reset(&es);
  mcpl_outfile_t f = mcpl_create_outfile_es("df_close.mcpl",&es);
  unsigned n = write_until_error(f,20,&es);
  es_reset(&es);
  mcpl_close_outfile_es(f,&es);
  if ( n == 20 ) {
    printf("  20 particles added without errors\n");
    expect_error(&es,MCPL_ERROR_IO,"close_outfile");
  } else {
    //(only if the C library buffers less than about 700 bytes)
    if ( es.code != 0 )
      test_fail("closing file after error failed");
  }
  reset_filesize_limit();
  uint64_t nrec = check_recovered("df_close.mcpl",1);
  if ( nrec == 0 || nrec >= 20 )
    test_fail("unexpected number of particles in file left after errors");
  remove("df_close.mcpl");
}

static void test_legacy(void)
{
  printf("\n==> Legacy functions raise the same errors:\n");
  mcpl_errstate_t es;
  set_filesize_limit(20000);
  //First with _es:
  mcpl_outfile_t f = mcpl_create_outfile("df_legacy1.mcpl");
  write_until_error(f,100000,&es);
  mcpl_close_outfile(f);
  //Then with the legacy function, until it raises an error (leaves the file
  //object unclosed):
  static mcpl_outfile_t f2;//(static, to not be clobbered by longjmp)
  static unsigned i;
  f2 = mcpl_create_outfile("df_legacy2.mcpl");
  mcpl_particle_t p;
  fill_particle(&p,0);
  LEGACY_CHECK( &es, for ( i = 0; i < 100000; ++i ) mcpl_add_particle(f2,&p) );
  printf("  same error as with mcpl_add_particle_es: %s\n",es.msg);
  reset_filesize_limit();
  remove("df_legacy1.mcpl");
  remove("df_legacy2.mcpl");
}

int main( int argc, char ** argv )
{
  (void)argc;
  (void)argv;
  if ( getenv("MCPLTEST_NO_LEGACY") )
    legacy_enabled = 0;
  //Writing beyond the limit should give errors, not end the process:
  signal(SIGXFSZ,SIG_IGN);
  if ( getrlimit( RLIMIT_FSIZE, &original_limit ) != 0 )
    test_fail("could not get file size limit");
  test_header_too_large();
  test_particles("df_particles.mcpl",0);
  test_particles("df_particles2.mcpl",1);
  test_error_at_close();
  test_legacy();
  printf("\nAll ok\n");
  return 0;
}

#endif
