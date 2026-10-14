
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
//when writing files. All errors are checked in-process, and also checked to
//be identical when raised through the error handler by the functions without
//_es (see mcpltest_errstate.h). Invalid arguments must leave files unchanged,
//which is checked by reading the files back. Errors while writing data (e.g.
//full disks) are tested in app_errstate_diskfull.

#include "mcpltest_errstate.h"
#ifdef _WIN32
#  include <direct.h>
#else
#  include <sys/stat.h>
#  include <unistd.h>
#endif

static mcpl_outfile_t legacy_of;//(static, to not be clobbered by longjmp)

////////////////////////////////////////////////////////////////////////////////
// Utilities

static void fill_particle( mcpl_particle_t * p, int i )
{
  memset(p,0,sizeof(*p));
  p->position[0] = 1.0 + i;
  p->position[1] = 2.0 * i;
  p->position[2] = -3.0 - i;
  p->direction[0] = 0.0;
  p->direction[1] = 0.6;
  p->direction[2] = 0.8;
  p->polarisation[0] = 0.5;
  p->ekin = 0.001 * ( i + 1 );
  p->time = 0.1 * i;
  p->weight = 1.0 + 0.5 * i;
  p->pdgcode = ( i % 2 ) ? 22 : 2112;
  p->userflags = (uint32_t)( 1000 + i );
}

static void print_es( const char * what, mcpl_errstate_t * es )
{
  print_result(what,es);
}

//Call statement (an _es function using es), print the result, and compare any
//error with the legacy statement (which is only run in case of errors, since
//repeating successful calls would change the file):
#define CHECK( what, es_statement, legacy_statement ) do {             \
    es_reset(&es);                                                      \
    es_statement;                                                       \
    print_es( what, &es );                                              \
    if ( es_failed(&es) )                                               \
      LEGACY_CHECK( &es, legacy_statement );                            \
  } while (0)

//Likewise, without comparison with a legacy statement:
#define CHECK_ES( what, es_statement ) do {                            \
    es_reset(&es);                                                      \
    es_statement;                                                       \
    print_es( what, &es );                                              \
  } while (0)

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
  printf("  file %s: nparticles=%u srcname=\"%s\" userflags=%i"
         " polarisation=%i doubleprec=%i universal pdgcode=%i weight=%g"
         " userdata layout=%s\n",
         filename,(unsigned)mcpl_hdr_nparticles(f),mcpl_hdr_srcname(f),
         mcpl_hdr_has_userflags(f),mcpl_hdr_has_polarisation(f),
         mcpl_hdr_has_doubleprec(f),(int)mcpl_hdr_universal_pdgcode(f),
         mcpl_hdr_universal_weight(f),
         mcpl_hdr_userdata_layout(f) ? mcpl_hdr_userdata_layout(f) : "none");
  for ( unsigned i = 0; i < mcpl_hdr_ncomments(f); ++i )
    printf("    comment %u: \"%.80s\"\n",i,mcpl_hdr_comment(f,i));
  const char ** keys = mcpl_hdr_blobkeys(f);
  for ( int i = 0; i < mcpl_hdr_nblobs(f); ++i ) {
    uint32_t ldata;
    const char * data;
    mcpl_hdr_blob(f,keys[i],&ldata,&data);
    printf("    blob \"%s\": %u bytes\n",keys[i],(unsigned)ldata);
  }
  const mcpl_particle_t * p;
  const uint8_t * ud;
  while ( ( p = mcpl_read_with_userdata_es(f,&ud,&es) ) )
    printf("    particle x=%g pdgcode=%i weight=%g userflags=%u%s\n",
           p->position[0],(int)p->pdgcode,p->weight,(unsigned)p->userflags,
           ud ? " (with userdata)" : "");
  print_result("  reading back",&es);
  mcpl_close_file(f);
}

////////////////////////////////////////////////////////////////////////////////
// Creating files

static void test_create(void)
{
  printf("\n==> Creating files:\n");
  mcpl_errstate_t es;
  char longname[5000];
  memset(longname,'x',4097);
  longname[4097] = '\0';
  const char * names[] = { NULL, "", ".mcpl", longname,
                           "nosuchdir/nosuchsubdir/file.mcpl" };
  const char * labels[] = { "NULL", "\"\"", "\".mcpl\"", "<4097 chars>",
                            "\"nosuchdir/nosuchsubdir/file.mcpl\"" };
  for ( unsigned i = 0; i < sizeof(names)/sizeof(names[0]); ++i ) {
    char what[256];
    snprintf(what,sizeof(what),"create_outfile(%s)",labels[i]);
    es_reset(&es);
    mcpl_outfile_t f = mcpl_create_outfile_es(names[i],&es);
    if ( f.internal )
      test_fail("create_outfile succeeded");
    print_es(what,&es);
    mcpl_close_outfile(f);//does nothing for f.internal==NULL
    mcpl_errstate_t es2;
    es_reset(&es2);
    mcpl_close_outfile_es(f,&es2);
    if ( es2.code != 0 )
      test_fail("closing invalid handle gave an error");
    LEGACY_CHECK( &es, legacy_of = mcpl_create_outfile(names[i]) );
  }
  //".mcpl" is appended if missing:
  es_reset(&es);
  mcpl_outfile_t f = mcpl_create_outfile_es("created",&es);
  printf("create_outfile(\"created\") -> filename \"%s\"\n",
         mcpl_outfile_filename(f));
  print_es("create_outfile(\"created\")",&es);
  mcpl_close_outfile_es(f,&es);
  print_es("close_outfile",&es);
  dump_file("created.mcpl");
  remove("created.mcpl");
}

////////////////////////////////////////////////////////////////////////////////
// Invalid file objects

static void test_invalid_handles(void)
{
  printf("\n==> Functions called with invalid file objects (internal NULL):\n");
  mcpl_errstate_t es;
  mcpl_outfile_t of;
  of.internal = NULL;
  mcpl_file_t fin;
  fin.internal = NULL;
  mcpl_particle_t p;
  fill_particle(&p,0);
  CHECK("hdr_set_srcname",mcpl_hdr_set_srcname_es(of,"x",&es),
        mcpl_hdr_set_srcname(of,"x"));
  CHECK("hdr_add_comment",mcpl_hdr_add_comment_es(of,"x",&es),
        mcpl_hdr_add_comment(of,"x"));
  CHECK("hdr_add_data",mcpl_hdr_add_data_es(of,"k",1,"x",&es),
        mcpl_hdr_add_data(of,"k",1,"x"));
  CHECK("enable_userflags",mcpl_enable_userflags_es(of,&es),
        mcpl_enable_userflags(of));
  CHECK("enable_polarisation",mcpl_enable_polarisation_es(of,&es),
        mcpl_enable_polarisation(of));
  CHECK("enable_doubleprec",mcpl_enable_doubleprec_es(of,&es),
        mcpl_enable_doubleprec(of));
  CHECK("enable_universal_pdgcode",mcpl_enable_universal_pdgcode_es(of,22,&es),
        mcpl_enable_universal_pdgcode(of,22));
  CHECK("enable_universal_weight",mcpl_enable_universal_weight_es(of,1.0,&es),
        mcpl_enable_universal_weight(of,1.0));
  CHECK("enable_userdata",mcpl_enable_userdata_es(of,"a:int8",&es),
        mcpl_enable_userdata(of,"a:int8"));
  CHECK("hdr_add_stat_sum",mcpl_hdr_add_stat_sum_es(of,"k",1.0,&es),
        mcpl_hdr_add_stat_sum(of,"k",1.0));
  CHECK("hdr_scale_stat_sums",mcpl_hdr_scale_stat_sums_es(of,2.0,&es),
        mcpl_hdr_scale_stat_sums(of,2.0));
  es_reset(&es);
  mcpl_particle_t * pe = mcpl_get_empty_particle_es(of,&es);
  if ( pe )
    test_fail("get_empty_particle returned non-NULL");
  print_es("get_empty_particle",&es);
  LEGACY_CHECK( &es, mcpl_get_empty_particle(of) );
  CHECK("add_particle",mcpl_add_particle_es(of,&p,&es),
        mcpl_add_particle(of,&p));
  CHECK("add_particle_with_userdata",
        mcpl_add_particle_with_userdata_es(of,&p,NULL,&es),
        mcpl_add_particle_with_userdata(of,&p,NULL));
  CHECK("transfer_metadata",mcpl_transfer_metadata_es(fin,of,&es),
        mcpl_transfer_metadata(fin,of));
  CHECK("transfer_last_read_particle",
        mcpl_transfer_last_read_particle_es(fin,of,&es),
        mcpl_transfer_last_read_particle(fin,of));
  es_reset(&es);
  int rc = mcpl_closeandgzip_outfile_es(of,&es);
  printf("  closeandgzip_outfile returned %i\n",rc);
  print_es("closeandgzip_outfile (does nothing)",&es);
  es_reset(&es);
  mcpl_close_outfile_es(of,&es);
  print_es("close_outfile (does nothing)",&es);
}

////////////////////////////////////////////////////////////////////////////////
// Invalid arguments and calls (which must not change the file)

static void test_usage_errors(void)
{
  printf("\n==> Invalid arguments and calls before writing the header:\n");
  mcpl_errstate_t es;
  es_reset(&es);
  //(variables used with LEGACY_CHECK are static, to not be clobbered by
  //longjmp):
  static mcpl_outfile_t f;
  f = mcpl_create_outfile_es("usage.mcpl",&es);
  print_es("create_outfile",&es);

  char * longstr = (char*)malloc(65536);
  memset(longstr,'x',65535);
  longstr[65535] = '\0';
  char longkey[80];
  memset(longkey,'k',70);
  longkey[70] = '\0';

  CHECK("hdr_set_srcname(NULL)",mcpl_hdr_set_srcname_es(f,NULL,&es),
        mcpl_hdr_set_srcname(f,NULL));
  CHECK("hdr_set_srcname(<65535 chars>)",mcpl_hdr_set_srcname_es(f,longstr,&es),
        mcpl_hdr_set_srcname(f,longstr));
  CHECK("hdr_set_srcname(\"errstate_write\")",
        mcpl_hdr_set_srcname_es(f,"errstate_write",&es),
        mcpl_hdr_set_srcname(f,"errstate_write"));

  CHECK("hdr_add_comment(NULL)",mcpl_hdr_add_comment_es(f,NULL,&es),
        mcpl_hdr_add_comment(f,NULL));
  CHECK("hdr_add_comment(<65535 chars>)",mcpl_hdr_add_comment_es(f,longstr,&es),
        mcpl_hdr_add_comment(f,longstr));
  CHECK("hdr_add_comment(\"stat:foo\")",mcpl_hdr_add_comment_es(f,"stat:foo",&es),
        mcpl_hdr_add_comment(f,"stat:foo"));
  CHECK("hdr_add_comment(\"stat:sum:bad\")",
        mcpl_hdr_add_comment_es(f,"stat:sum:bad",&es),
        mcpl_hdr_add_comment(f,"stat:sum:bad"));
  CHECK("hdr_add_comment(\"a comment\")",mcpl_hdr_add_comment_es(f,"a comment",&es),
        mcpl_hdr_add_comment(f,"a comment"));

  CHECK("hdr_add_stat_sum(NULL,1)",mcpl_hdr_add_stat_sum_es(f,NULL,1.0,&es),
        mcpl_hdr_add_stat_sum(f,NULL,1.0));
  CHECK("hdr_add_stat_sum(\"\",1)",mcpl_hdr_add_stat_sum_es(f,"",1.0,&es),
        mcpl_hdr_add_stat_sum(f,"",1.0));
  CHECK("hdr_add_stat_sum(<70 chars>,1)",mcpl_hdr_add_stat_sum_es(f,longkey,1.0,&es),
        mcpl_hdr_add_stat_sum(f,longkey,1.0));
  CHECK("hdr_add_stat_sum(\"1abc\",1)",mcpl_hdr_add_stat_sum_es(f,"1abc",1.0,&es),
        mcpl_hdr_add_stat_sum(f,"1abc",1.0));
  CHECK("hdr_add_stat_sum(\"a:b\",1)",mcpl_hdr_add_stat_sum_es(f,"a:b",1.0,&es),
        mcpl_hdr_add_stat_sum(f,"a:b",1.0));
  {
    const char * labels[4] = { "NaN", "+inf", "-inf", "-2" };
    double v[4];
    v[0] = mcpltest_nan();
    v[1] = mcpltest_inf();
    v[2] = -mcpltest_inf();
    v[3] = -2.0;
    for ( int i = 0; i < 4; ++i ) {
      char what[128];
      snprintf(what,sizeof(what),"hdr_add_stat_sum(\"key\",%s)",labels[i]);
      CHECK(what,mcpl_hdr_add_stat_sum_es(f,"key",v[i],&es),
            mcpl_hdr_add_stat_sum(f,"key",v[i]));
    }
    for ( int i = 0; i < 4; ++i ) {
      const char * l = ( i == 3 ? "-0.5" : labels[i] );
      static double s;
      s = ( i == 3 ? -0.5 : v[i] );
      char what[128];
      snprintf(what,sizeof(what),"hdr_scale_stat_sums(%s)",l);
      CHECK(what,mcpl_hdr_scale_stat_sums_es(f,s,&es),
            mcpl_hdr_scale_stat_sums(f,s));
    }
    CHECK("hdr_scale_stat_sums(0)",mcpl_hdr_scale_stat_sums_es(f,0.0,&es),
          mcpl_hdr_scale_stat_sums(f,0.0));
    CHECK("hdr_add_stat_sum(\"nevents\",-1)",
          mcpl_hdr_add_stat_sum_es(f,"nevents",-1.0,&es),
          mcpl_hdr_add_stat_sum(f,"nevents",-1.0));
    CHECK("hdr_add_stat_sum(\"eventsum\",10)",
          mcpl_hdr_add_stat_sum_es(f,"eventsum",10.0,&es),
          mcpl_hdr_add_stat_sum(f,"eventsum",10.0));
    CHECK("hdr_add_comment(\"stat:sum:eventsum:   1\")",
          mcpl_hdr_add_comment_es(f,"stat:sum:eventsum:   1",&es),
          mcpl_hdr_add_comment(f,"stat:sum:eventsum:   1"));
    CHECK("hdr_scale_stat_sums(3)",mcpl_hdr_scale_stat_sums_es(f,3.0,&es),
          mcpl_hdr_scale_stat_sums(f,3.0));
  }

  CHECK("hdr_add_data(NULL,...)",mcpl_hdr_add_data_es(f,NULL,3,"abc",&es),
        mcpl_hdr_add_data(f,NULL,3,"abc"));
  CHECK("hdr_add_data(\"k\",3,NULL)",mcpl_hdr_add_data_es(f,"k",3,NULL,&es),
        mcpl_hdr_add_data(f,"k",3,NULL));
  CHECK("hdr_add_data(<65535 chars>,...)",mcpl_hdr_add_data_es(f,longstr,3,"abc",&es),
        mcpl_hdr_add_data(f,longstr,3,"abc"));
  CHECK("hdr_add_data(\"blob1\",3,\"abc\")",mcpl_hdr_add_data_es(f,"blob1",3,"abc",&es),
        mcpl_hdr_add_data(f,"blob1",3,"abc"));
  CHECK("hdr_add_data(\"blob1\",2,\"de\")",mcpl_hdr_add_data_es(f,"blob1",2,"de",&es),
        mcpl_hdr_add_data(f,"blob1",2,"de"));
  CHECK("hdr_add_data(\"empty\",0,NULL)",mcpl_hdr_add_data_es(f,"empty",0,NULL,&es),
        mcpl_hdr_add_data(f,"empty",0,NULL));

  CHECK("enable_universal_pdgcode(0)",mcpl_enable_universal_pdgcode_es(f,0,&es),
        mcpl_enable_universal_pdgcode(f,0));
  CHECK("enable_universal_pdgcode(2112)",mcpl_enable_universal_pdgcode_es(f,2112,&es),
        mcpl_enable_universal_pdgcode(f,2112));
  CHECK("enable_universal_pdgcode(2112) again",
        mcpl_enable_universal_pdgcode_es(f,2112,&es),
        mcpl_enable_universal_pdgcode(f,2112));
  CHECK("enable_universal_pdgcode(22)",mcpl_enable_universal_pdgcode_es(f,22,&es),
        mcpl_enable_universal_pdgcode(f,22));
  {
    const char * labels[4] = { "0", "-1", "+inf", "NaN" };
    double ww[4];
    ww[0] = 0.0;
    ww[1] = -1.0;
    ww[2] = mcpltest_inf();
    ww[3] = mcpltest_nan();
    for ( int i = 0; i < 4; ++i ) {
      char what[128];
      snprintf(what,sizeof(what),"enable_universal_weight(%s)",labels[i]);
      CHECK(what,mcpl_enable_universal_weight_es(f,ww[i],&es),
            mcpl_enable_universal_weight(f,ww[i]));
    }
  }
  CHECK("enable_universal_weight(2)",mcpl_enable_universal_weight_es(f,2.0,&es),
        mcpl_enable_universal_weight(f,2.0));
  CHECK("enable_universal_weight(3)",mcpl_enable_universal_weight_es(f,3.0,&es),
        mcpl_enable_universal_weight(f,3.0));

  CHECK("enable_userdata(NULL)",mcpl_enable_userdata_es(f,NULL,&es),
        mcpl_enable_userdata(f,NULL));
  CHECK("enable_userdata(\"a:int9\")",mcpl_enable_userdata_es(f,"a:int9",&es),
        mcpl_enable_userdata(f,"a:int9"));
  CHECK("enable_userdata(\"temp:float32\")",
        mcpl_enable_userdata_es(f,"temp:float32",&es),
        mcpl_enable_userdata(f,"temp:float32"));
  CHECK("enable_userdata(\"temp:float32\") again",
        mcpl_enable_userdata_es(f,"temp:float32",&es),
        mcpl_enable_userdata(f,"temp:float32"));
  CHECK("enable_userdata(\"temp:float64\")",
        mcpl_enable_userdata_es(f,"temp:float64",&es),
        mcpl_enable_userdata(f,"temp:float64"));
  CHECK("enable_userflags",mcpl_enable_userflags_es(f,&es),
        mcpl_enable_userflags(f));

  es_reset(&es);
  static mcpl_particle_t * p;//(static, see above)
  p = mcpl_get_empty_particle_es(f,&es);
  print_es("get_empty_particle",&es);
  es_reset(&es);
  mcpl_particle_t * p2 = mcpl_get_empty_particle_es(f,&es);
  printf("  second get_empty_particle returned %s\n",p2?"non-NULL":"NULL");
  print_es("get_empty_particle again",&es);
  LEGACY_CHECK( &es, mcpl_get_empty_particle(f) );

  printf("\n==> Invalid particles:\n");
  fill_particle(p,0);
  p->weight = 2.0;
  CHECK("add_particle (file has userdata)",mcpl_add_particle_es(f,p,&es),
        mcpl_add_particle(f,p));
  CHECK("add_particle_with_userdata(NULL particle)",
        mcpl_add_particle_with_userdata_es(f,NULL,NULL,&es),
        mcpl_add_particle_with_userdata(f,NULL,NULL));
  {
    double nan = mcpltest_nan();
    double inf = mcpltest_inf();
    struct { const char * what; int field; double value; } cases[] = {
      { "NaN position", 0, 0.0 }, { "infinite position", 0, 1.0 },
      { "NaN direction", 1, 0.0 }, { "NaN polarisation (not stored)", 2, 0.0 },
      { "NaN ekin", 3, 0.0 }, { "infinite time", 4, 1.0 },
      { "NaN weight (universal weight)", 5, 0.0 },
      { "non-unit direction", 6, 0.0 }, { "negative ekin", 7, 0.0 },
      { "position too large for single precision", 8, 0.0 },
      { "polarisation too large for single precision (not stored)", 9, 0.0 },
      { "ekin too large for single precision", 10, 0.0 },
      { "time too large for single precision", 11, 0.0 },
    };
    static unsigned i;
    for ( i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i ) {
      fill_particle(p,0);
      p->weight = 2.0;
      double v = ( cases[i].value ? inf : nan );
      switch ( cases[i].field ) {
      case 0: p->position[1] = v; break;
      case 1: p->direction[2] = v; break;
      case 2: p->polarisation[0] = v; break;
      case 3: p->ekin = v; break;
      case 4: p->time = v; break;
      case 5: p->weight = v; break;
      case 6: p->direction[2] = 0.9; break;
      case 7: p->ekin = -1.0; break;
      case 8: p->position[0] = 1e39; break;
      case 9: p->polarisation[1] = 1e39; break;
      case 10: p->ekin = 1e39; break;
      case 11: p->time = 1e39; break;
      }
      char what[128];
      snprintf(what,sizeof(what),"add_particle_with_userdata(%s)",cases[i].what);
      CHECK(what,mcpl_add_particle_with_userdata_es(f,p,NULL,&es),
            mcpl_add_particle_with_userdata(f,p,NULL));
    }
  }
  float temp = 300.0f;
  for ( int i = 0; i < 3; ++i ) {
    fill_particle(p,i);
    p->pdgcode = 2112;
    p->weight = 2.0;
    uint8_t ud[4];
    memcpy(ud,&temp,4);
    CHECK("add_particle_with_userdata (valid)",
          mcpl_add_particle_with_userdata_es(f,p,ud,&es),
          mcpl_add_particle_with_userdata(f,p,ud));
  }

  printf("\n==> Invalid calls after writing the header:\n");
  CHECK("hdr_set_srcname",mcpl_hdr_set_srcname_es(f,"x",&es),
        mcpl_hdr_set_srcname(f,"x"));
  CHECK("hdr_add_comment",mcpl_hdr_add_comment_es(f,"x",&es),
        mcpl_hdr_add_comment(f,"x"));
  CHECK("hdr_add_data",mcpl_hdr_add_data_es(f,"k",1,"x",&es),
        mcpl_hdr_add_data(f,"k",1,"x"));
  CHECK("enable_userflags (already enabled)",mcpl_enable_userflags_es(f,&es),
        mcpl_enable_userflags(f));
  CHECK("enable_polarisation",mcpl_enable_polarisation_es(f,&es),
        mcpl_enable_polarisation(f));
  CHECK("enable_doubleprec",mcpl_enable_doubleprec_es(f,&es),
        mcpl_enable_doubleprec(f));
  CHECK("enable_userdata (other layout)",mcpl_enable_userdata_es(f,"a:int8",&es),
        mcpl_enable_userdata(f,"a:int8"));
  CHECK("hdr_add_stat_sum(\"newkey\",1)",mcpl_hdr_add_stat_sum_es(f,"newkey",1.0,&es),
        mcpl_hdr_add_stat_sum(f,"newkey",1.0));
  CHECK("hdr_add_stat_sum(\"nevents\",NaN)",
        mcpl_hdr_add_stat_sum_es(f,"nevents",mcpltest_nan(),&es),
        mcpl_hdr_add_stat_sum(f,"nevents",mcpltest_nan()));
  CHECK("hdr_add_stat_sum(\"nevents\",1000) (updates the file)",
        mcpl_hdr_add_stat_sum_es(f,"nevents",1000.0,&es),
        mcpl_hdr_add_stat_sum(f,"nevents",1000.0));
  CHECK("hdr_scale_stat_sums(-3)",mcpl_hdr_scale_stat_sums_es(f,-3.0,&es),
        mcpl_hdr_scale_stat_sums(f,-3.0));
  CHECK("hdr_scale_stat_sums(0.5) (updates the file)",
        mcpl_hdr_scale_stat_sums_es(f,0.5,&es),
        mcpl_hdr_scale_stat_sums(f,0.5));
  es_reset(&es);
  mcpl_close_outfile_es(f,&es);
  print_es("close_outfile",&es);
  printf("  Reading back (with none of the invalid data):\n");
  dump_file("usage.mcpl");

  //A file without userdata:
  printf("\n==> File without userdata:\n");
  es_reset(&es);
  f = mcpl_create_outfile_es("usage2.mcpl",&es);
  mcpl_particle_t pp;
  fill_particle(&pp,0);
  const uint8_t ud[1] = { 0 };
  CHECK("add_particle_with_userdata (with userdata)",
        mcpl_add_particle_with_userdata_es(f,&pp,ud,&es),
        mcpl_add_particle_with_userdata(f,&pp,ud));
  CHECK("add_particle_with_userdata (NULL userdata)",
        mcpl_add_particle_with_userdata_es(f,&pp,NULL,&es),
        mcpl_add_particle_with_userdata(f,&pp,NULL));
  CHECK("enable_universal_pdgcode (too late)",
        mcpl_enable_universal_pdgcode_es(f,22,&es),
        mcpl_enable_universal_pdgcode(f,22));
  CHECK("enable_universal_weight (too late)",
        mcpl_enable_universal_weight_es(f,1.0,&es),
        mcpl_enable_universal_weight(f,1.0));
  CHECK("enable_userflags (too late)",mcpl_enable_userflags_es(f,&es),
        mcpl_enable_userflags(f));
  es_reset(&es);
  mcpl_close_outfile_es(f,&es);
  print_es("close_outfile",&es);
  dump_file("usage2.mcpl");
  remove("usage2.mcpl");

  //Particles with too large values for single precision, in a file with
  //polarisation and without universal weight:
  printf("\n==> Values too large for single precision:\n");
  es_reset(&es);
  f = mcpl_create_outfile_es("usage3.mcpl",&es);
  mcpl_enable_polarisation(f);
  fill_particle(&pp,0);
  pp.polarisation[2] = 1e39;
  CHECK("add_particle (polarisation too large)",mcpl_add_particle_es(f,&pp,&es),
        mcpl_add_particle(f,&pp));
  fill_particle(&pp,0);
  pp.weight = 1e39;
  CHECK("add_particle (weight too large)",mcpl_add_particle_es(f,&pp,&es),
        mcpl_add_particle(f,&pp));
  fill_particle(&pp,0);
  pp.weight = mcpltest_nan();
  CHECK("add_particle (NaN weight)",mcpl_add_particle_es(f,&pp,&es),
        mcpl_add_particle(f,&pp));
  CHECK_ES("close_outfile",mcpl_close_outfile_es(f,&es));
  dump_file("usage3.mcpl");
  remove("usage3.mcpl");

  //Scaling stat:sum: values beyond the floating point range (giving -1),
  //before and after writing the header:
  printf("\n==> Scaling stat:sum: values beyond the floating point range:\n");
  es_reset(&es);
  f = mcpl_create_outfile_es("usage4.mcpl",&es);
  mcpl_hdr_add_stat_sum(f,"big",1e300);
  mcpl_hdr_add_stat_sum(f,"big2",1e300);
  mcpl_hdr_add_stat_sum(f,"unavail",-1.0);
  mcpl_hdr_add_stat_sum(f,"small",1.0);
  CHECK_ES("hdr_scale_stat_sums(1e10)",mcpl_hdr_scale_stat_sums_es(f,1e10,&es));
  mcpl_hdr_add_stat_sum(f,"big2",1e300);
  fill_particle(&pp,0);
  mcpl_add_particle(f,&pp);
  CHECK_ES("hdr_scale_stat_sums(1e10) after writing the header",
           mcpl_hdr_scale_stat_sums_es(f,1e10,&es));
  CHECK_ES("close_outfile",mcpl_close_outfile_es(f,&es));
  dump_file("usage4.mcpl");
  remove("usage4.mcpl");
  free(longstr);
}

////////////////////////////////////////////////////////////////////////////////
// Transferring metadata and particles

static void create_source_files(void)
{
  //Files to transfer from (with all options, or just the defaults):
  mcpl_outfile_t f = mcpl_create_outfile("src_all.mcpl");
  mcpl_hdr_set_srcname(f,"source");
  mcpl_hdr_add_comment(f,"source comment");
  mcpl_hdr_add_stat_sum(f,"nevents",123.0);
  mcpl_hdr_add_data(f,"srcblob",4,"data");
  mcpl_enable_userflags(f);
  mcpl_enable_polarisation(f);
  mcpl_enable_doubleprec(f);
  mcpl_enable_universal_pdgcode(f,2112);
  mcpl_enable_universal_weight(f,2.0);
  mcpl_enable_userdata(f,"temp:float32");
  mcpl_particle_t * p = mcpl_get_empty_particle(f);
  for ( int i = 0; i < 3; ++i ) {
    fill_particle(p,i);
    p->pdgcode = 2112;
    p->weight = 2.0;
    mcpl_add_particle_with_userdata(f,p,NULL);
  }
  mcpl_close_outfile(f);
  f = mcpl_create_outfile("src_plain.mcpl");
  p = mcpl_get_empty_particle(f);
  for ( int i = 0; i < 3; ++i ) {
    fill_particle(p,i);
    mcpl_add_particle(f,p);
  }
  mcpl_close_outfile(f);
  //With a NaN value in the second particle (single precision, weight at
  //float index 7, after position and packed direction and ekin and time):
  buffer_t b = file_load("src_plain.mcpl");
  mcpl_file_t fin = mcpl_open_file("src_plain.mcpl");
  size_t pos = (size_t)mcpl_hdr_header_size(fin) + 1 * mcpl_hdr_particle_size(fin)
    + 7 * sizeof(float);
  mcpl_close_file(fin);
  const unsigned char fnan[4] = { 0x00, 0x00, 0xc0, 0x7f };//little endian NaN
  save_modified("src_nan.mcpl",&b,b.size,pos,fnan,4);
  free(b.data);
}

static void test_transfers(void)
{
  printf("\n==> Transferring metadata:\n");
  create_source_files();
  mcpl_errstate_t es;
  //(variables used with LEGACY_CHECK are static, to not be clobbered by
  //longjmp):
  static mcpl_file_t fin;
  static mcpl_outfile_t f;
  fin = mcpl_open_file("src_all.mcpl");
  es_reset(&es);
  f = mcpl_create_outfile_es("tr1.mcpl",&es);
  CHECK_ES("transfer_metadata",mcpl_transfer_metadata_es(fin,f,&es));
  mcpl_close_outfile(f);
  dump_file("tr1.mcpl");
  remove("tr1.mcpl");
  //Errors in transfer_metadata leave the target unusable (since part of the
  //metadata might have been transferred):
  f = mcpl_create_outfile_es("tr2.mcpl",&es);
  mcpl_hdr_add_data(f,"srcblob",1,"x");//clash
  mcpl_hdr_add_comment(f,"comment in target");
  CHECK_ES("transfer_metadata (with clashing blob key)",
        mcpl_transfer_metadata_es(fin,f,&es));
  mcpl_particle_t p;
  fill_particle(&p,0);
  CHECK_ES("add_particle after failed transfer_metadata",
        mcpl_add_particle_es(f,&p,&es));
  CHECK_ES("hdr_add_comment after failed transfer_metadata",
        mcpl_hdr_add_comment_es(f,"x",&es));
  es_reset(&es);
  mcpl_close_outfile_es(f,&es);
  print_es("close_outfile (frees, leaves the file unfinished)",&es);
  dump_file("tr2.mcpl");
  remove("tr2.mcpl");
  //Legacy comparison of the error itself:
  legacy_of = mcpl_create_outfile("tr3.mcpl");
  mcpl_hdr_add_data(legacy_of,"srcblob",1,"x");
  es_reset(&es);
  mcpl_transfer_metadata_es(fin,legacy_of,&es);
  mcpl_close_outfile(legacy_of);
  legacy_of = mcpl_create_outfile("tr4.mcpl");
  mcpl_hdr_add_data(legacy_of,"srcblob",1,"x");
  LEGACY_CHECK( &es, mcpl_transfer_metadata(fin,legacy_of) );
  remove("tr3.mcpl");
  mcpl_close_file(fin);

  printf("\n==> Transferring particles:\n");
  fin = mcpl_open_file("src_all.mcpl");
  mcpl_file_t fplain = mcpl_open_file("src_plain.mcpl");
  f = mcpl_create_outfile_es("tr5.mcpl",&es);
  CHECK("transfer_last_read_particle (nothing read)",
        mcpl_transfer_last_read_particle_es(fin,f,&es),
        mcpl_transfer_last_read_particle(fin,f));
  mcpl_read(fin);
  mcpl_read(fplain);
  mcpl_enable_universal_pdgcode(f,22);
  CHECK("transfer_last_read_particle (pdgcode differs from universal one)",
        mcpl_transfer_last_read_particle_es(fin,f,&es),
        mcpl_transfer_last_read_particle(fin,f));
  mcpl_close_outfile(f);
  f = mcpl_create_outfile_es("tr5.mcpl",&es);
  mcpl_enable_universal_weight(f,3.0);
  CHECK("transfer_last_read_particle (weight differs from universal one)",
        mcpl_transfer_last_read_particle_es(fin,f,&es),
        mcpl_transfer_last_read_particle(fin,f));
  mcpl_close_outfile(f);
  f = mcpl_create_outfile_es("tr5.mcpl",&es);
  mcpl_enable_userdata(f,"temp:float32");
  CHECK("transfer_last_read_particle (source without userdata)",
        mcpl_transfer_last_read_particle_es(fplain,f,&es),
        mcpl_transfer_last_read_particle(fplain,f));
  mcpl_close_outfile(f);
  f = mcpl_create_outfile_es("tr5.mcpl",&es);
  mcpl_enable_userdata(f,"temp:float64");
  CHECK("transfer_last_read_particle (different userdata layout)",
        mcpl_transfer_last_read_particle_es(fin,f,&es),
        mcpl_transfer_last_read_particle(fin,f));
  mcpl_close_outfile(f);
  {
    mcpl_file_t fnan = mcpl_open_file("src_nan.mcpl");
    mcpl_read(fnan);
    mcpl_read(fnan);
    f = mcpl_create_outfile_es("tr5.mcpl",&es);
    CHECK("transfer_last_read_particle (NaN weight)",
          mcpl_transfer_last_read_particle_es(fnan,f,&es),
          mcpl_transfer_last_read_particle(fnan,f));
    mcpl_close_outfile(f);
    mcpl_close_file(fnan);
  }
  {
    //Source file unusable after an error:
    buffer_t b = file_load("src_plain.mcpl");
    file_save("src_trunc.mcpl",b.data,b.size-10);
    free(b.data);
    mcpl_file_t ftr = mcpl_open_file("src_trunc.mcpl");
    mcpl_read(ftr);
    mcpl_read(ftr);
    mcpl_errstate_t es2;
    es_reset(&es2);
    mcpl_read_es(ftr,&es2);
    f = mcpl_create_outfile_es("tr5.mcpl",&es);
    {
    //(static, to not be clobbered by longjmp):
    static mcpl_file_t fnull;
    static mcpl_outfile_t fo;
    fnull.internal = NULL;
    fo = mcpl_create_outfile("tr7.mcpl");
    CHECK("transfer_metadata (invalid source)",
          mcpl_transfer_metadata_es(fnull,fo,&es),
          mcpl_transfer_metadata(fnull,fo));
    mcpl_close_outfile(fo);
    fo = mcpl_create_outfile("tr7.mcpl");
    CHECK("transfer_last_read_particle (invalid source)",
          mcpl_transfer_last_read_particle_es(fnull,fo,&es),
          mcpl_transfer_last_read_particle(fnull,fo));
    mcpl_close_outfile(fo);
    remove("tr7.mcpl");
  }
  CHECK_ES("transfer_last_read_particle (source failed to read)",
          mcpl_transfer_last_read_particle_es(ftr,f,&es));
    mcpl_close_outfile(f);
    mcpl_close_file(ftr);
    remove("src_trunc.mcpl");
  }
  //Valid transfers:
  f = mcpl_create_outfile_es("tr5.mcpl",&es);
  mcpl_transfer_metadata(fin,f);
  CHECK("transfer_last_read_particle (same settings)",
        mcpl_transfer_last_read_particle_es(fin,f,&es),
        mcpl_transfer_last_read_particle(fin,f));
  CHECK_ES("close_outfile",mcpl_close_outfile_es(f,&es));
  dump_file("tr5.mcpl");
  f = mcpl_create_outfile_es("tr6.mcpl",&es);
  mcpl_enable_doubleprec(f);
  CHECK("transfer_last_read_particle (other settings)",
        mcpl_transfer_last_read_particle_es(fplain,f,&es),
        mcpl_transfer_last_read_particle(fplain,f));
  CHECK_ES("close_outfile",mcpl_close_outfile_es(f,&es));
  dump_file("tr6.mcpl");
  mcpl_close_file(fin);
  mcpl_close_file(fplain);
  remove("tr5.mcpl");
  remove("tr6.mcpl");
  remove("src_all.mcpl");
  remove("src_plain.mcpl");
  remove("src_nan.mcpl");
}

////////////////////////////////////////////////////////////////////////////////
// Closing and compressing

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

static void test_closeandgzip(void)
{
  printf("\n==> Closing and compressing files:\n");
  mcpl_errstate_t es;
  mcpl_particle_t p;
  fill_particle(&p,0);
  es_reset(&es);
  mcpl_outfile_t f = mcpl_create_outfile_es("gz1.mcpl",&es);
  mcpl_add_particle(f,&p);
  es_reset(&es);
  int rc = mcpl_closeandgzip_outfile_es(f,&es);
  printf("  closeandgzip_outfile returned %i\n",rc);
  print_es("closeandgzip_outfile",&es);
  dump_file("gz1.mcpl.gz");
  remove("gz1.mcpl.gz");

  //Compression fails if the .gz file can not be created (here a directory
  //is in the way), but the file is closed properly:
  make_dir("gz2.mcpl.gz");
  f = mcpl_create_outfile_es("gz2.mcpl",&es);
  mcpl_add_particle(f,&p);
  mcpl_add_particle(f,&p);
  es_reset(&es);
  rc = mcpl_closeandgzip_outfile_es(f,&es);
  printf("  closeandgzip_outfile returned %i\n",rc);
  print_es("closeandgzip_outfile (directory in the way)",&es);
  dump_file("gz2.mcpl");
  remove("gz2.mcpl");
  //The legacy function reports the problem without raising an error:
  f = mcpl_create_outfile("gz2.mcpl");
  mcpl_add_particle(f,&p);
  rc = mcpl_closeandgzip_outfile(f);
  printf("  legacy closeandgzip_outfile returned %i\n",rc);
  remove("gz2.mcpl");
  remove_dir("gz2.mcpl.gz");
}

////////////////////////////////////////////////////////////////////////////////

int main( int argc, char ** argv )
{
  (void)argc;
  (void)argv;
  if ( getenv("MCPLTEST_NO_LEGACY") )
    legacy_enabled = 0;
  test_create();
  test_invalid_handles();
  test_usage_errors();
  test_transfers();
  test_closeandgzip();
  remove("usage.mcpl");
  remove("tr4.mcpl");
  legacy_remove_copies();
  return 0;
}
