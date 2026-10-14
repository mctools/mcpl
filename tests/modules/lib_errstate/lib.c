
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

//Representative errors, raised both by the functions with an error state
//(the _es variants) and by the functions without _es, which call the error
//handler (used by tests/scripts/errstate_legacy.py, which runs the latter in
//subprocesses).

MCPLTEST_CTYPE_DICTIONARY
{
  return
    "void mcpltest_es_setup();"
    "void mcpltest_es_case( const char *, int );"
    ;
}

static void mcpltest_es_fill( mcpl_particle_t * p, int i )
{
  memset(p,0,sizeof(*p));
  p->position[0] = 1.0 + i;
  p->direction[2] = 1.0;
  p->ekin = 0.001 * ( i + 1 );
  p->weight = 1.0;
  p->pdgcode = 2112;
}

static void mcpltest_es_write( const char * filename, int doubleprec )
{
  mcpl_outfile_t f = mcpl_create_outfile(filename);
  if ( doubleprec )
    mcpl_enable_doubleprec(f);
  mcpl_particle_t * p = mcpl_get_empty_particle(f);
  for ( int i = 0; i < 3; ++i ) {
    mcpltest_es_fill(p,i);
    mcpl_add_particle(f,p);
  }
  mcpl_close_outfile(f);
}

//Copy of the first nkeep bytes of a file (all but the last -nkeep bytes for
//negative nkeep), using the file utilities of MCPL:
static void mcpltest_es_truncated_copy( const char * src, const char * dest,
                                        int64_t nkeep )
{
  uint64_t n;
  char * buf;
  mcpl_read_file_to_buffer( src, 0, 0, &n, &buf );
  mcpl_generic_wfilehandle_t fh = mcpl_generic_wfopen( dest );
  mcpl_generic_fwrite( &fh, buf, nkeep >= 0 ? (uint64_t)nkeep
                                            : n - (uint64_t)(-nkeep) );
  mcpl_generic_fwclose( &fh );
  free(buf);
}

MCPLTEST_CTYPES void mcpltest_es_setup(void)
{
  mcpltest_es_write("es_a.mcpl",0);
  mcpltest_es_write("es_b.mcpl",1);
  mcpltest_es_truncated_copy("es_a.mcpl","es_hdr.mcpl",20);
  mcpltest_es_truncated_copy("es_a.mcpl","es_data.mcpl",-10);
}

//Runs the case, with the _es variant (printing the error), or with the
//function without _es:
MCPLTEST_CTYPES void mcpltest_es_case( const char * name, int use_es )
{
  mcpl_errstate_t es_storage;
  mcpl_errstate_t * es = use_es ? &es_storage : NULL;
  if ( es )
    es->code = 0;
  mcpl_particle_t p;
  mcpltest_es_fill(&p,0);
  const char * files[2] = { "es_a.mcpl", "es_b.mcpl" };
  if ( strcmp(name,"open_missing") == 0 ) {
    mcpl_close_file( mcpl_open_file_es("es_nosuchfile.mcpl",es) );
  } else if ( strcmp(name,"open_truncated_header") == 0 ) {
    mcpl_close_file( mcpl_open_file_es("es_hdr.mcpl",es) );
  } else if ( strcmp(name,"read_truncated_data") == 0 ) {
    mcpl_file_t f = mcpl_open_file("es_data.mcpl");
    while ( mcpl_read_es(f,es) ) {}
    mcpl_close_file(f);
  } else if ( strcmp(name,"comment_index") == 0 ) {
    mcpl_file_t f = mcpl_open_file("es_a.mcpl");
    mcpl_hdr_comment_es(f,5,es);
    mcpl_close_file(f);
  } else if ( strcmp(name,"create_empty_name") == 0 ) {
    mcpl_close_outfile( mcpl_create_outfile_es("",es) );
  } else if ( strcmp(name,"add_nan_particle") == 0 ) {
    mcpl_outfile_t f = mcpl_create_outfile("es_out1.mcpl");
    p.ekin = strtod("nan",NULL);
    mcpl_add_particle_es(f,&p,es);
    mcpl_close_outfile(f);
  } else if ( strcmp(name,"srcname_too_late") == 0 ) {
    mcpl_outfile_t f = mcpl_create_outfile("es_out2.mcpl");
    mcpl_add_particle(f,&p);
    mcpl_hdr_set_srcname_es(f,"x",es);
    mcpl_close_outfile(f);
  } else if ( strcmp(name,"transfer_before_read") == 0 ) {
    mcpl_file_t fin = mcpl_open_file("es_a.mcpl");
    mcpl_outfile_t f = mcpl_create_outfile("es_out3.mcpl");
    mcpl_transfer_last_read_particle_es(fin,f,es);
    mcpl_close_outfile(f);
    mcpl_close_file(fin);
  } else if ( strcmp(name,"merge_incompatible") == 0 ) {
    mcpl_close_outfile( mcpl_merge_files_es("es_out4.mcpl",2,files,es) );
  } else if ( strcmp(name,"merge_inplace_same_file") == 0 ) {
    mcpl_merge_inplace_es("es_a.mcpl","es_a.mcpl",es);
  } else if ( strcmp(name,"repair_not_broken") == 0 ) {
    mcpl_repair_es("es_a.mcpl",es);
  } else {
    printf("unknown case: %s\n",name);
    exit(1);
  }
  if ( es ) {
    if ( es->code )
      printf("Got error from _es variant: %s\n",es->msg);
    else
      printf("No error from _es variant\n");
  }
  fflush(stdout);
}
