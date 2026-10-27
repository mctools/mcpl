
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
//be recoverable when their headers were written completely. This also applies
//to the operations on files (merging, compressing). Since when
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
  FILE * fh = mcpltest_fopen(filename,"rb");
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
  //(gzip=2: closing with the function without _es)
  printf("\n==> Particles exceeding the file size limit%s:\n",
         gzip == 2 ? " (closing with gzip, without _es)"
         : ( gzip ? " (closing with gzip)" : "" ) );
  mcpl_errstate_t es;
  set_filesize_limit(20000);
  es_reset(&es);
  mcpl_outfile_t f = mcpl_create_outfile_es(filename,&es);
  mcpl_hdr_add_stat_sum(f,"nevents",-1.0);
  unsigned n = write_until_error(f,100000,&es);
  printf("  %s particles were added before the error\n",
         n > 100 ? "more than 100" : "less than 100");
  es_reset(&es);
  if ( gzip == 2 ) {
    //(the unfinished file is not compressed, so it can be repaired):
    if ( mcpl_closeandgzip_outfile(f) != 0 )
      test_fail("closeandgzip_outfile did not report the failure");
  } else if ( gzip ) {
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

//Write a file (without limits) with n particles, starting at particle i0:
static void write_file( const char * filename, unsigned i0, unsigned n,
                        int doubleprec )
{
  mcpl_outfile_t f = mcpl_create_outfile(filename);
  if ( doubleprec )
    mcpl_enable_doubleprec(f);
  mcpl_hdr_add_stat_sum(f,"nevents",(double)n);
  mcpl_particle_t p;
  for ( unsigned i = 0; i < n; ++i ) {
    fill_particle(&p,(int)(i0+i));
    mcpl_add_particle(f,&p);
  }
  mcpl_close_outfile(f);
}

//Check the file left after errors in a merge into a new file (the error might
//happen when closing the output, if it is still buffered at that point):
static void check_merge_output( const char * what, mcpl_outfile_t f,
                                mcpl_errstate_t * es, const char * filename,
                                unsigned ntot )
{
  if ( !es_failed(es) ) {
    if ( !f.internal )
      test_fail("merge returned no file without errors");
    es_reset(es);
    mcpl_close_outfile_es(f,es);
  }
  expect_error(es,MCPL_ERROR_IO,what);
  reset_filesize_limit();
  //Left unfinished, with the first particles:
  uint64_t nrec = check_recovered(filename,1);
  if ( nrec == 0 || nrec >= ntot )
    test_fail("unexpected number of particles in file left after errors");
  mcpl_repair(filename);
  if ( check_recovered(filename,1) != nrec )
    test_fail("different number of particles after repair");
  remove(filename);
}

static void test_fileops(void)
{
  //Particles 0-1999 in df_in1.mcpl and 2000-3999 in df_in2.mcpl (so merged
  //files have particles in order), and the latter in double precision in
  //df_in2dp.mcpl (which can only be force-merged with df_in1.mcpl):
  write_file("df_in1.mcpl",0,2000,0);
  write_file("df_in2.mcpl",2000,2000,0);
  write_file("df_in2dp.mcpl",2000,2000,1);
  const char * files[2] = { "df_in1.mcpl", "df_in2.mcpl" };
  const char * files_dp[2] = { "df_in1.mcpl", "df_in2dp.mcpl" };
  mcpl_errstate_t es;

  printf("\n==> Merging files exceeding the file size limit:\n");
  set_filesize_limit(20000);
  es_reset(&es);
  mcpl_outfile_t f = mcpl_merge_files_es("df_merged.mcpl",2,files,&es);
  check_merge_output("merge_files",f,&es,"df_merged.mcpl",4000);

  printf("\n==> Force-merging files exceeding the file size limit:\n");
  set_filesize_limit(20000);
  es_reset(&es);
  f = mcpl_forcemerge_files_es("df_fmerged.mcpl",2,files_dp,0,&es);
  check_merge_output("forcemerge_files",f,&es,"df_fmerged.mcpl",4000);

  printf("\n==> Merging in place exceeding the file size limit:\n");
  write_file("df_inplace.mcpl",0,2000,0);
  long size_before = file_size("df_inplace.mcpl");
  set_filesize_limit((rlim_t)size_before + 20000);
  es_reset(&es);
  mcpl_merge_inplace_es("df_inplace.mcpl","df_in2.mcpl",&es);
  expect_error(&es,MCPL_ERROR_IO,"merge_inplace");
  reset_filesize_limit();
  //File 1 is left unfinished, with its own and some of the added particles:
  uint64_t nrec = check_recovered("df_inplace.mcpl",1);
  if ( nrec <= 2000 || nrec >= 4000 )
    test_fail("unexpected number of particles in file left after errors");
  mcpl_repair("df_inplace.mcpl");
  if ( check_recovered("df_inplace.mcpl",1) != nrec )
    test_fail("different number of particles after repair");
  remove("df_inplace.mcpl");

  printf("\n==> Compressing a file exceeding the file size limit:\n");
  write_file("df_gz.mcpl",0,4000,0);
  set_filesize_limit(2000);
  es_reset(&es);
  mcpl_gzip_file_es("df_gz.mcpl",&es);
  expect_error(&es,MCPL_ERROR_IO,"gzip_file");
  reset_filesize_limit();
  //The partial compressed file is removed, and the original is kept:
  if ( file_size("df_gz.mcpl.gz") != -1 )
    test_fail("partial compressed file not removed");
  printf("  partial compressed file removed\n");
  if ( check_recovered("df_gz.mcpl",1) != 4000 )
    test_fail("original file not kept");
  remove("df_gz.mcpl");

  remove("df_in1.mcpl");
  remove("df_in2.mcpl");
  remove("df_in2dp.mcpl");
}

static void test_close_unfinished(void)
{
  printf("\n==> Closing without finishing, exceeding the file size limit:\n");
  mcpl_errstate_t es;
  //Buffered particles exceeding the limit when written:
  set_filesize_limit(300);
  es_reset(&es);
  mcpl_outfile_t f = mcpl_create_outfile_es("df_unf1.mcpl",&es);
  unsigned n = write_until_error(f,20,&es);
  es_reset(&es);
  mcpl_close_outfile_unfinished_es(f,&es);
  if ( n == 20 ) {
    printf("  20 particles added without errors\n");
    expect_error(&es,MCPL_ERROR_IO,"close_outfile_unfinished");
  } else {
    //(only if the C library buffers less than about 700 bytes; errors are
    //not reported again)
    if ( es.code != 0 )
      test_fail("closing file after error failed");
  }
  reset_filesize_limit();
  uint64_t nrec = check_recovered("df_unf1.mcpl",1);
  if ( nrec == 0 || nrec >= 20 )
    test_fail("unexpected number of particles in file left after errors");
  remove("df_unf1.mcpl");

  //After errors which made the file unusable (not reported again):
  set_filesize_limit(20000);
  es_reset(&es);
  f = mcpl_create_outfile_es("df_unf2.mcpl",&es);
  write_until_error(f,100000,&es);
  es_reset(&es);
  mcpl_close_outfile_unfinished_es(f,&es);
  if ( es.code != 0 )
    test_fail("error reported again by close_outfile_unfinished");
  printf("  close_outfile_unfinished after the error -> ok\n");
  reset_filesize_limit();
  check_recovered("df_unf2.mcpl",1);
  remove("df_unf2.mcpl");
}

int main( int argc, char ** argv )
{
  (void)argc;
  (void)argv;
  //Writing beyond the limit should give errors, not end the process:
  signal(SIGXFSZ,SIG_IGN);
  if ( getrlimit( RLIMIT_FSIZE, &original_limit ) != 0 )
    test_fail("could not get file size limit");
  test_header_too_large();
  test_particles("df_particles.mcpl",0);
  test_particles("df_particles2.mcpl",1);
  test_particles("df_particles3.mcpl",2);
  test_error_at_close();
  test_fileops();
  test_close_unfinished();
  printf("\nAll ok\n");
  return 0;
}

#endif
