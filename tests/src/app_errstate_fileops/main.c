
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

//Tests of the functions reporting errors in an error state (the _es variants)
//for operations on files (merging, repairing, compressing and dumping). All
//errors are checked in-process, and the files left after errors are checked
//as well (unchanged, or unfinished and repairable). Errors while writing data
//(e.g. full disks) are tested in app_errstate_diskfull. (The functions without
//_es are wrappers which pass a NULL error state, and their errors are tested
//in errstate_legacy.py.)

#include "mcpltest_errstate.h"
#include "mcpltestutils.h"
#ifdef _WIN32
#  include <direct.h>
#else
#  include <sys/stat.h>
#  include <unistd.h>
#endif

////////////////////////////////////////////////////////////////////////////////
// Utilities

static void fill_particle( mcpl_particle_t * p, int i )
{
  memset(p,0,sizeof(*p));
  p->position[0] = 1.0 + i;
  p->direction[2] = 1.0;
  p->ekin = 0.001 * ( i + 1 );
  p->weight = 1.0 + i;
  p->pdgcode = ( i % 2 ) ? 22 : 2112;
}

//File with n particles (the first one with x=x0), a comment and a stat:sum:
static void create_file( const char * filename, int n, int x0,
                         double nevents, int doubleprec )
{
  mcpl_outfile_t f = mcpl_create_outfile(filename);
  mcpl_hdr_set_srcname(f,"errstate_fileops");
  mcpl_hdr_add_comment(f,"a comment");
  mcpl_hdr_add_stat_sum(f,"nevents",nevents);
  if ( doubleprec )
    mcpl_enable_doubleprec(f);
  mcpl_particle_t * p = mcpl_get_empty_particle(f);
  for ( int i = 0; i < n; ++i ) {
    fill_particle(p,x0+i-1);
    mcpl_add_particle(f,p);
  }
  mcpl_close_outfile(f);
}

static uint64_t file_size( const char * filename )
{
  buffer_t b = file_load(filename);
  free(b.data);
  return (uint64_t)b.size;
}

static void copy_file( const char * src, const char * dest )
{
  buffer_t b = file_load(src);
  file_save(dest,b.data,b.size);
  free(b.data);
}

//Print the contents of a file:
static void dump_file( const char * filename )
{
  mcpl_errstate_t es;
  es_reset(&es);
  mcpl_file_t f = mcpl_open_file_es(filename,&es);
  if ( es_failed(&es) ) {
    print_result("  reading back",&es);
    return;
  }
  //(source names of force-merged files contain the MCPL version, which is
  //not printed):
  char srcname[256];
  snprintf(srcname,sizeof(srcname),"%s",mcpl_hdr_srcname(f));
  char * v = strstr(srcname," (from MCPL v");
  if ( v )
    memcpy(v," (from MCPL)",13);
  printf("  file %s: nparticles=%u srcname=\"%s\" doubleprec=%i\n",
         filename,(unsigned)mcpl_hdr_nparticles(f),srcname,
         mcpl_hdr_has_doubleprec(f));
  for ( unsigned i = 0; i < mcpl_hdr_ncomments(f); ++i )
    printf("    comment %u: \"%s\"\n",i,mcpl_hdr_comment(f,i));
  const mcpl_particle_t * p;
  printf("    particle x values:");
  while ( ( p = mcpl_read_es(f,&es) ) )
    printf(" %g",p->position[0]);
  printf("\n");
  print_result("  reading back",&es);
  mcpl_close_file(f);
}

static void make_dir( const char * path )
{
#ifdef _WIN32
  _mkdir(path);
#else
  mkdir(path,0755);
#endif
}

static void remove_dir( const char * path )
{
#ifdef _WIN32
  _rmdir(path);
#else
  rmdir(path);
#endif
}

static int file_exists( const char * filename )
{
  FILE * fh = mcpltest_fopen(filename,"rb");
  if (!fh)
    return 0;
  fclose(fh);
  return 1;
}

//Truncate a file, removing the last nbytes:
static void truncate_copy( const char * src, const char * dest, size_t nbytes )
{
  buffer_t b = file_load(src);
  file_save(dest,b.data,b.size-nbytes);
  free(b.data);
}

////////////////////////////////////////////////////////////////////////////////
// Merging into new files

static void test_merge_files(void)
{
  printf("\n==> Merging files into new files:\n");
  mcpl_errstate_t es;
  create_file("m1.mcpl",3,1,10.0,0);
  create_file("m2.mcpl",2,11,20.0,0);
  create_file("m3_dp.mcpl",2,21,30.0,1);
  truncate_copy("m2.mcpl","m2_trunc.mcpl",10);
  //m2_trunc.mcpl claims 2 particles, but only has one complete one.

  struct { const char * what; const char * out; unsigned n;
    const char * f[3]; } cases[] = {
    { "no input files", "mout.mcpl", 0, { NULL, NULL, NULL } },
    { "NULL input file", "mout.mcpl", 2, { "m1.mcpl", NULL, NULL } },
    { "same file twice", "mout.mcpl", 2, { "m1.mcpl", "m1.mcpl", NULL } },
    { "missing input file", "mout.mcpl", 2, { "m1.mcpl", "nosuchfile.mcpl", NULL } },
    { "incompatible files", "mout.mcpl", 2, { "m1.mcpl", "m3_dp.mcpl", NULL } },
    { "output file exists", "m2.mcpl", 1, { "m1.mcpl", NULL, NULL } },
    //(".mcpl" is appended to the output filename, giving an input file):
    { "output file exists with .mcpl", "m1", 2, { "m1.mcpl", "m2.mcpl", NULL } },
    { "NULL output file", NULL, 1, { "m1.mcpl", NULL, NULL } },
  };
  const uint64_t m1size = file_size("m1.mcpl");
  for ( unsigned i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i ) {
    char what[256];
    snprintf(what,sizeof(what),"merge_files (%s)",cases[i].what);
    es_reset(&es);
    mcpl_outfile_t f = mcpl_merge_files_es(cases[i].out,cases[i].n,
                                           cases[i].f,&es);
    if ( f.internal )
      test_fail("merge unexpectedly succeeded");
    print_result(what,&es);
    if ( cases[i].out && strcmp(cases[i].out,"mout.mcpl") == 0
         && file_exists("mout.mcpl") )
      test_fail("output file created");
  }
  if ( file_size("m1.mcpl") != m1size )
    test_fail("input file modified");

  //Input file which turns out to be truncated while transferring particles:
  //the output is left unfinished (and can be repaired):
  {
    const char * files[2] = { "m1.mcpl", "m2_trunc.mcpl" };
    es_reset(&es);
    mcpl_outfile_t f = mcpl_merge_files_es("mout.mcpl",2,files,&es);
    if ( f.internal )
      test_fail("merge unexpectedly succeeded");
    print_result("merge_files (truncated input file)",&es);
    printf("  output left unfinished:\n");
    dump_file("mout.mcpl");
    es_reset(&es);
    mcpl_repair_es("mout.mcpl",&es);
    print_result("  repair",&es);
    dump_file("mout.mcpl");
    remove("mout.mcpl");
  }

  //Successful merges (also of a file in the old format 2):
  {
    const char * files[2] = { "m1.mcpl", "m2.mcpl" };
    es_reset(&es);
    mcpl_outfile_t f = mcpl_merge_files_es("mout.mcpl",2,files,&es);
    print_result("merge_files (valid)",&es);
    mcpl_close_outfile_es(f,&es);
    print_result("close_outfile",&es);
    dump_file("mout.mcpl");
    remove("mout.mcpl");
    const char * fmt2 = mcpltests_find_data("reffmt2","reffile_1.mcpl");
    copy_file(fmt2,"m_fmt2.mcpl");
    const char * files2[1] = { "m_fmt2.mcpl" };
    es_reset(&es);
    f = mcpl_merge_files_es("mout.mcpl",1,files2,&es);
    print_result("merge_files (format 2)",&es);
    mcpl_close_outfile(f);
    mcpl_file_t fin = mcpl_open_file("mout.mcpl");
    printf("  merged file has format version %u and %u particles\n",
           mcpl_hdr_version(fin),(unsigned)mcpl_hdr_nparticles(fin));
    mcpl_close_file(fin);
    remove("mout.mcpl");
  }

  printf("\n==> Checking if files can be merged:\n");
  {
    struct { const char * f1; const char * f2; } cc[] = {
      { "m1.mcpl", "m2.mcpl" }, { "m1.mcpl", "m3_dp.mcpl" },
      { "m1.mcpl", "nosuchfile.mcpl" }, { NULL, "m1.mcpl" },
    };
    for ( unsigned i = 0; i < sizeof(cc)/sizeof(cc[0]); ++i ) {
      es_reset(&es);
      int rc = mcpl_can_merge_es(cc[i].f1,cc[i].f2,&es);
      char what[256];
      snprintf(what,sizeof(what),"can_merge(%s,%s) = %i",
               cc[i].f1 ? cc[i].f1 : "NULL",cc[i].f2,rc);
      print_result(what,&es);
    }
  }
}

////////////////////////////////////////////////////////////////////////////////
// Forced merges

static void test_forcemerge_files(void)
{
  printf("\n==> Forced merges:\n");
  mcpl_errstate_t es;
  struct { const char * what; const char * out; unsigned n;
    const char * f[3]; } cases[] = {
    { "no input files", "fout.mcpl", 0, { NULL, NULL, NULL } },
    { "same file twice", "fout.mcpl", 2, { "m1.mcpl", "m1.mcpl", NULL } },
    { "missing input file", "fout.mcpl", 2, { "m1.mcpl", "nosuchfile.mcpl", NULL } },
    { "output file exists", "m2.mcpl", 2, { "m1.mcpl", "m3_dp.mcpl", NULL } },
    { "output file exists with .mcpl", "m1", 2, { "m1.mcpl", "m3_dp.mcpl", NULL } },
  };
  const uint64_t m1size = file_size("m1.mcpl");
  for ( unsigned i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i ) {
    char what[256];
    snprintf(what,sizeof(what),"forcemerge_files (%s)",cases[i].what);
    es_reset(&es);
    mcpl_outfile_t f = mcpl_forcemerge_files_es(cases[i].out,cases[i].n,
                                                cases[i].f,0,&es);
    if ( f.internal )
      test_fail("merge unexpectedly succeeded");
    print_result(what,&es);
  }
  if ( file_size("m1.mcpl") != m1size )
    test_fail("input file modified");
  //Truncated input file (output left unfinished):
  {
    const char * files[2] = { "m3_dp.mcpl", "m2_trunc.mcpl" };
    es_reset(&es);
    mcpl_outfile_t f = mcpl_forcemerge_files_es("fout.mcpl",2,files,0,&es);
    if ( f.internal )
      test_fail("merge unexpectedly succeeded");
    print_result("forcemerge_files (truncated input file)",&es);
    printf("  output left unfinished:\n");
    dump_file("fout.mcpl");
    remove("fout.mcpl");
  }
  //Input file with a NaN value (output left unfinished):
  {
    create_file("m_nan.mcpl",3,31,1.0,0);
    buffer_t b = file_load("m_nan.mcpl");
    mcpl_file_t fin = mcpl_open_file("m_nan.mcpl");
    size_t pos = (size_t)mcpl_hdr_header_size(fin)
      + 2 * mcpl_hdr_particle_size(fin);//position x of the third particle
    mcpl_close_file(fin);
    const unsigned char fnan[4] = { 0x00, 0x00, 0xc0, 0x7f };
    save_modified("m_nan.mcpl",&b,b.size,pos,fnan,4);
    free(b.data);
    const char * files[2] = { "m3_dp.mcpl", "m_nan.mcpl" };
    es_reset(&es);
    mcpl_outfile_t f = mcpl_forcemerge_files_es("fout.mcpl",2,files,0,&es);
    if ( f.internal )
      test_fail("merge unexpectedly succeeded");
    print_result("forcemerge_files (NaN in input file)",&es);
    printf("  output left unfinished:\n");
    dump_file("fout.mcpl");
    remove("fout.mcpl");
  }
  //Successful forced merge, and fallback to normal merge:
  {
    const char * files[2] = { "m1.mcpl", "m3_dp.mcpl" };
    es_reset(&es);
    mcpl_outfile_t f = mcpl_forcemerge_files_es("fout.mcpl",2,files,0,&es);
    print_result("forcemerge_files (valid)",&es);
    mcpl_close_outfile(f);
    dump_file("fout.mcpl");
    remove("fout.mcpl");
    const char * files2[2] = { "m1.mcpl", "m2.mcpl" };
    es_reset(&es);
    f = mcpl_forcemerge_files_es("fout.mcpl",2,files2,0,&es);
    print_result("forcemerge_files (compatible files)",&es);
    mcpl_close_outfile(f);
    dump_file("fout.mcpl");
    remove("fout.mcpl");
  }
}

////////////////////////////////////////////////////////////////////////////////
// Merging in place

static void test_merge_inplace(void)
{
  printf("\n==> Merging in place:\n");
  mcpl_errstate_t es;
  copy_file("m1.mcpl","i1.mcpl");
  create_file("m_empty.mcpl",0,1,5.0,0);
  copy_file(mcpltests_find_data("reffmt2","reffile_1.mcpl"),"i_fmt2.mcpl");
  copy_file(mcpltests_find_data("ref","reffile_1.mcpl"),"i_fmt3.mcpl");
  copy_file("m1.mcpl","i1_gz.mcpl");
  {
    mcpl_errstate_t es2;
    es_reset(&es2);
    mcpl_gzip_file_es("i1_gz.mcpl",&es2);
  }
  struct { const char * what; const char * f1; const char * f2; } cases[] = {
    { "NULL file", "i1.mcpl", NULL },
    { "same file", "i1.mcpl", "i1.mcpl" },
    { "missing file", "i1.mcpl", "nosuchfile.mcpl" },
    { "incompatible files", "i1.mcpl", "m3_dp.mcpl" },
    { "different format versions", "i_fmt3.mcpl", "i_fmt2.mcpl" },
    { "gzipped file", "i1_gz.mcpl.gz", "m2.mcpl" },
  };
  uint64_t size_before = file_size("i1.mcpl");
  for ( unsigned i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i ) {
    char what[256];
    snprintf(what,sizeof(what),"merge_inplace (%s)",cases[i].what);
    es_reset(&es);
    mcpl_merge_inplace_es(cases[i].f1,cases[i].f2,&es);
    print_result(what,&es);
  }
  if ( file_size("i1.mcpl") != size_before )
    test_fail("file modified by failed merge_inplace");
  printf("  i1.mcpl unchanged by these errors\n");

  //File 2 truncated: errors during the transfer leave file 1 unfinished (and
  //repairable):
  es_reset(&es);
  mcpl_merge_inplace_es("i1.mcpl","m2_trunc.mcpl",&es);
  print_result("merge_inplace (truncated file 2)",&es);
  printf("  file 1 left unfinished:\n");
  dump_file("i1.mcpl");
  es_reset(&es);
  mcpl_repair_es("i1.mcpl",&es);
  print_result("  repair",&es);
  dump_file("i1.mcpl");

  //Successful merges:
  copy_file("m1.mcpl","i1.mcpl");
  es_reset(&es);
  mcpl_merge_inplace_es("i1.mcpl","m_empty.mcpl",&es);
  print_result("merge_inplace (empty file 2)",&es);
  es_reset(&es);
  mcpl_merge_inplace_es("i1.mcpl","m2.mcpl",&es);
  print_result("merge_inplace (valid)",&es);
  dump_file("i1.mcpl");
  remove("i1.mcpl");
  remove("i_fmt2.mcpl");
  remove("i_fmt3.mcpl");
  remove("i1_gz.mcpl.gz");
  remove("m_empty.mcpl");
}

////////////////////////////////////////////////////////////////////////////////
// Repairing files

static void test_repair(void)
{
  printf("\n==> Repairing files:\n");
  mcpl_errstate_t es;
  //Unfinished file (nparticles=0), plain and gzipped, and with nparticles
  //larger than the actual number:
  buffer_t b = file_load("m1.mcpl");
  uint64_t zero = 0;
  save_modified("r_unfinished.mcpl",&b,b.size-5,8,&zero,8);
  save_modified("r_unfinished2.mcpl",&b,b.size-5,8,&zero,8);
  quiet_gzip("r_unfinished2.mcpl");
  save_modified("r_truncated.mcpl",&b,b.size-5,0,NULL,0);
  free(b.data);
  struct { const char * what; const char * f; } cases[] = {
    { "NULL", NULL },
    { "missing file", "nosuchfile.mcpl" },
    { "not broken", "m1.mcpl" },
    { "gzipped and broken", "r_unfinished2.mcpl.gz" },
    { "gzipped", "m1gz.mcpl.gz" },
  };
  copy_file("m1.mcpl","m1gz.mcpl");
  quiet_gzip("m1gz.mcpl");
  for ( unsigned i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i ) {
    char what[256];
    snprintf(what,sizeof(what),"repair (%s)",cases[i].what);
    es_reset(&es);
    mcpl_repair_es(cases[i].f,&es);
    print_result(what,&es);
  }
  es_reset(&es);
  mcpl_repair_es("r_unfinished.mcpl",&es);
  print_result("repair (unfinished file)",&es);
  dump_file("r_unfinished.mcpl");
  es_reset(&es);
  mcpl_repair_es("r_truncated.mcpl",&es);
  print_result("repair (truncated file)",&es);
  dump_file("r_truncated.mcpl");
  remove("r_unfinished.mcpl");
  remove("r_unfinished2.mcpl.gz");
  remove("r_truncated.mcpl");
  remove("m1gz.mcpl.gz");
}

////////////////////////////////////////////////////////////////////////////////
// Compressing files

static void test_gzip(void)
{
  printf("\n==> Compressing files:\n");
  mcpl_errstate_t es;
  es_reset(&es);
  int rc = mcpl_gzip_file_es(NULL,&es);
  printf("  gzip_file(NULL) returned %i\n",rc);
  print_result("gzip_file(NULL)",&es);
  es_reset(&es);
  rc = mcpl_gzip_file_es("nosuchfile.mcpl",&es);
  printf("  gzip_file(nosuchfile.mcpl) returned %i\n",rc);
  print_result("gzip_file(nosuchfile.mcpl)",&es);
  if ( file_exists("nosuchfile.mcpl.gz") )
    test_fail("gz file created");
  //Directory in the way of the .gz file (the original file is kept):
  copy_file("m1.mcpl","g1.mcpl");
  make_dir("g1.mcpl.gz");
  es_reset(&es);
  rc = mcpl_gzip_file_es("g1.mcpl",&es);
  printf("  gzip_file returned %i\n",rc);
  print_result("gzip_file (directory in the way)",&es);
  remove_dir("g1.mcpl.gz");
  dump_file("g1.mcpl");
  //Successful:
  es_reset(&es);
  rc = mcpl_gzip_file_es("g1.mcpl",&es);
  printf("  gzip_file returned %i, original file %s\n",rc,
         file_exists("g1.mcpl") ? "still exists" : "removed");
  print_result("gzip_file (valid)",&es);
  dump_file("g1.mcpl.gz");
  remove("g1.mcpl.gz");
  //The legacy function reports problems without raising errors:
  rc = mcpl_gzip_file("nosuchfile.mcpl");
  printf("  legacy gzip_file(nosuchfile.mcpl) returned %i\n",rc);
}

////////////////////////////////////////////////////////////////////////////////
// Dumping open files

//Output collected from the dump functions:
typedef struct {
  char * data;
  size_t size;
  size_t capacity;
} collected_t;

static void collect( const char * msg, void * ctx )
{
  collected_t * c = (collected_t*)ctx;
  size_t n = strlen(msg);
  if ( c->size + n + 1 > c->capacity ) {
    size_t newcap = 2 * ( c->size + n + 1 );
    char * d = (char*)realloc(c->data,newcap);
    if (!d)
      test_fail("memory allocation failed");
    c->data = d;
    c->capacity = newcap;
  }
  memcpy(c->data+c->size,msg,n+1);
  c->size += n;
}

static void collected_reset( collected_t * c )
{
  c->size = 0;
  if ( c->data )
    c->data[0] = '\0';
}

//Output of mcpl_dump (via the print handler), without the first line (with the
//filename):
static void legacy_dump( collected_t * c, const char * filename, int parts,
                         uint64_t nskip, uint64_t nlimit )
{
  collected_reset(c);
  mcpl_set_print_handler_ctx(collect,c);
  mcpl_dump(filename,parts,nskip,nlimit);
  mcpl_set_print_handler(NULL);
  char * nl = strchr(c->data,'\n');
  if ( !nl || strncmp(c->data,"Opened MCPL file ",17) != 0 )
    test_fail("unexpected first line of mcpl_dump output");
  size_t n = (size_t)( nl + 1 - c->data );
  memmove(c->data,nl+1,c->size-n+1);
  c->size -= n;
}

static void test_dump(void)
{
  printf("\n==> Dumping open files:\n");
  create_file("d1.mcpl",5,1,5.0,0);
  {
    //With userdata (also shown in the dump):
    mcpl_outfile_t f = mcpl_create_outfile("d_ud.mcpl");
    mcpl_enable_userdata(f,"tag:uint16,v:float32");
    mcpl_particle_t * p = mcpl_get_empty_particle(f);
    uint8_t ud[6];
    for ( int i = 0; i < 3; ++i ) {
      fill_particle(p,i);
      mcpl_userdata_set_uint16(ud,0,(uint16_t)(100+i));
      mcpl_userdata_set_float32(ud,2,0.5f*(float)i);
      mcpl_add_particle_with_userdata(f,p,ud);
    }
    mcpl_close_outfile(f);
  }
  collected_t c = { NULL, 0, 0 };
  collected_t ref = { NULL, 0, 0 };
  mcpl_errstate_t es;

  //Same output as mcpl_dump, for all parts and some ranges:
  struct { const char * fn; int parts; unsigned nskip; unsigned nlimit; } cases[] = {
    { "d1.mcpl", 0, 0, 0 }, { "d1.mcpl", 1, 0, 0 }, { "d1.mcpl", 2, 0, 0 },
    { "d1.mcpl", 2, 1, 2 }, { "d1.mcpl", 0, 3, 1 }, { "d1.mcpl", 2, 4, 10 },
    { "d1.mcpl", 2, 5, 0 }, { "d1.mcpl", 2, 100, 0 }, { "d_ud.mcpl", 0, 0, 0 }
  };
  for ( unsigned i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i ) {
    mcpl_file_t f = mcpl_open_file(cases[i].fn);
    collected_reset(&c);
    es_reset(&es);
    mcpl_dump_file_es(f,cases[i].parts,cases[i].nskip,cases[i].nlimit,
                      collect,&c,&es);
    char what[256];
    snprintf(what,sizeof(what),"dump_file(%s,parts=%i,nskip=%u,nlimit=%u)",
             cases[i].fn,cases[i].parts,cases[i].nskip,cases[i].nlimit);
    print_result(what,&es);
    legacy_dump(&ref,cases[i].fn,cases[i].parts,cases[i].nskip,
                cases[i].nlimit);
    if ( strcmp(c.data,ref.data) != 0 ) {
      printf("%s\n----\n%s\n",c.data,ref.data);
      test_fail("output differs from mcpl_dump");
    }
    if ( i == 0 || i == 3 || i == sizeof(cases)/sizeof(cases[0]) - 1 )
      printf("%s",c.data);
    mcpl_close_file(f);
  }
  printf("  output identical to mcpl_dump in all cases\n");

  //Without output function, the output goes to the print handler:
  {
    mcpl_file_t f = mcpl_open_file("d1.mcpl");
    collected_t viaprint = { NULL, 0, 0 };
    mcpl_set_print_handler_ctx(collect,&viaprint);
    es_reset(&es);
    mcpl_dump_file_es(f,0,0,0,NULL,NULL,&es);
    mcpl_set_print_handler(NULL);
    print_result("dump_file(d1.mcpl, no output function)",&es);
    legacy_dump(&ref,"d1.mcpl",0,0,0);
    if ( strcmp(viaprint.data,ref.data) != 0 )
      test_fail("output via print handler differs from mcpl_dump");
    printf("  output via print handler identical to mcpl_dump\n");
    free(viaprint.data);
    mcpl_close_file(f);
  }

  //The position in the file is unchanged, but the last read particle is no
  //longer available:
  {
    mcpl_file_t f = mcpl_open_file("d_ud.mcpl");
    mcpl_read(f);
    mcpl_read(f);
    if ( !mcpl_last_read_userdata(f) )
      test_fail("no userdata of last read particle");
    collected_reset(&c);
    es_reset(&es);
    mcpl_dump_file_es(f,2,0,0,collect,&c,&es);
    print_result("dump_file(d_ud.mcpl,parts=2) after reading 2 particles",&es);
    const uint8_t * ud = mcpl_last_read_userdata(f);
    const mcpl_particle_t * p = mcpl_read(f);
    printf("  position afterwards: %u, last read userdata: %s,"
           " next particle x=%g\n",(unsigned)mcpl_currentposition(f)-1,
           ud ? "available" : "NULL", p ? p->position[0] : -1.0);
    //Header only: the last read particle is kept:
    collected_reset(&c);
    mcpl_dump_file_es(f,1,0,0,collect,&c,&es);
    print_result("dump_file(d_ud.mcpl,parts=1)",&es);
    printf("  last read userdata: %s\n",
           mcpl_last_read_userdata(f) ? "available" : "NULL");
    mcpl_close_file(f);
  }

  //Gzipped files:
  {
    copy_file("d1.mcpl","d1gz.mcpl");
    quiet_gzip("d1gz.mcpl");
    mcpl_file_t f = mcpl_open_file("d1gz.mcpl.gz");
    mcpl_read(f);
    collected_reset(&c);
    es_reset(&es);
    mcpl_dump_file_es(f,2,2,2,collect,&c,&es);
    print_result("dump_file(d1gz.mcpl.gz,parts=2,nskip=2,nlimit=2)",&es);
    printf("%s",c.data);
    const mcpl_particle_t * p = mcpl_read(f);
    printf("  next particle x=%g\n",p ? p->position[0] : -1.0);
    mcpl_close_file(f);
    remove("d1gz.mcpl.gz");
  }

  //Errors:
  {
    mcpl_file_t fnull;
    fnull.internal = NULL;
    collected_reset(&c);
    es_reset(&es);
    mcpl_dump_file_es(fnull,0,0,0,collect,&c,&es);
    print_result("dump_file(invalid handle)",&es);
    mcpl_file_t f = mcpl_open_file("d1.mcpl");
    int badparts[2] = { -1, 3 };
    for ( unsigned i = 0; i < 2; ++i ) {
      es_reset(&es);
      mcpl_dump_file_es(f,badparts[i],0,0,collect,&c,&es);
      char what[64];
      snprintf(what,sizeof(what),"dump_file(parts=%i)",badparts[i]);
      print_result(what,&es);
    }
    if ( c.size != 0 )
      test_fail("output for invalid arguments");
    printf("  no output for invalid arguments\n");
    //The file is still usable:
    es_reset(&es);
    mcpl_dump_file_es(f,1,0,0,collect,&c,&es);
    print_result("dump_file(parts=1) after these errors",&es);
    //mcpl_check_error does nothing without errors:
    mcpl_check_error(&es);
    mcpl_check_error(NULL);
    printf("  check_error without errors -> ok\n");
    mcpl_close_file(f);

    //Truncated data: the header can be dumped, but listing the particles
    //fails (and the file is then unusable):
    truncate_copy("d1.mcpl","d1_trunc.mcpl",10);
    f = mcpl_open_file("d1_trunc.mcpl");
    collected_reset(&c);
    es_reset(&es);
    mcpl_dump_file_es(f,1,0,0,collect,&c,&es);
    print_result("dump_file(d1_trunc.mcpl,parts=1)",&es);
    collected_reset(&c);
    es_reset(&es);
    mcpl_dump_file_es(f,2,0,0,collect,&c,&es);
    print_result("dump_file(d1_trunc.mcpl,parts=2)",&es);
    printf("%s",c.data);
    es_reset(&es);
    mcpl_dump_file_es(f,1,0,0,collect,&c,&es);
    print_result("dump_file(d1_trunc.mcpl,parts=1) afterwards",&es);
    mcpl_close_file(f);
    remove("d1_trunc.mcpl");
  }
  free(c.data);
  free(ref.data);
  remove("d1.mcpl");
  remove("d_ud.mcpl");
}

////////////////////////////////////////////////////////////////////////////////

int main( int argc, char ** argv )
{
  (void)argc;
  (void)argv;
  test_merge_files();
  test_forcemerge_files();
  test_merge_inplace();
  test_repair();
  test_gzip();
  test_dump();
  const char * tmpfiles[] = { "m1.mcpl", "m2.mcpl", "m3_dp.mcpl",
                              "m2_trunc.mcpl", "m_fmt2.mcpl", "m_nan.mcpl" };
  for ( unsigned i = 0; i < sizeof(tmpfiles)/sizeof(tmpfiles[0]); ++i )
    remove(tmpfiles[i]);
  return 0;
}
