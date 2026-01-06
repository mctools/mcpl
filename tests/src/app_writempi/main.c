
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

#include "mcpl.h"
#include <stdlib.h>
#include <stdio.h>
#include <memory.h>
#include <string.h>

void mcpltest_name_helper( const char * fn, char mode, const char * expected)
{
  static int i = 0;
  i += 1;
  char * res = mcpl_name_helper( fn, mode );
  if ( strcmp( res, expected ) != 0 ) {
    printf("mcpltest_name_helper test failure (test %i)\n",i);
    exit(1);
  }
  free(res);
}

int main(int argc,char**argv) {
  (void)argc;
  (void)argv;

  //Pretend MPI (but actually run in one process:

#define MCPLTEST_NPROC 4
  const unsigned long nproc = MCPLTEST_NPROC;

  //mpi: init files:
  //init all mpi procs:
  mcpl_outfile_t outhandles[MCPLTEST_NPROC];
  for ( unsigned long iproc = 0; iproc < nproc; ++iproc ) {

    //It makes no difference if the filename argument is "foobar", "foobar.mcpl"
    //or "foobar.mcpl.gz". Unit test this:
    const char * userfn;
    if ( iproc % 3 == 0 )
      userfn = "foobar";
    else if ( iproc % 3 == 1 )
      userfn = "foobar.mcpl";
    else
      userfn = "foobar.mcpl.gz";

    mcpl_outfile_t f = mcpl_create_outfile_mpi( userfn, iproc, nproc );
    outhandles[iproc] = f;
    mcpl_hdr_set_srcname(f,"CustomMPITest");
    mcpl_enable_universal_pdgcode(f,2112);
    mcpl_hdr_add_comment(f,"Some comment.");
    mcpl_hdr_add_comment(f,"Another comment.");
    mcpl_hdr_add_stat_sum(f,"foostat", -1.0 );
  }

  //mpi: add particles:
  for ( unsigned long iproc = 0; iproc < nproc; ++iproc ) {
    mcpl_outfile_t f = outhandles[iproc];
    mcpl_particle_t * particle = mcpl_get_empty_particle(f);
    for (int i = 0; i < 2; ++i) {
      particle->position[0] = i*1.0;
      particle->position[1] = i*2.0;
      particle->position[2] = i*3.0;
      particle->ekin = i*0.1;
      particle->direction[0] = 0.0;
      particle->direction[1] = 0.0;
      particle->direction[2] = 1.0;
      particle->time = i*0.01;
      particle->weight = (double)iproc;
      mcpl_add_particle(f,particle);
    }
  }

  //mpi: close files
  for ( unsigned long iproc = 0; iproc < nproc; ++iproc ) {
    mcpl_outfile_t f = outhandles[iproc];
    mcpl_hdr_add_stat_sum(f,"foostat", 10.0 + iproc );
    mcpl_closeandgzip_outfile(f);
  }

  //Merge:
  mcpl_merge_outfiles_mpi( "foobar", nproc );

  //Dump:
  mcpl_dump("foobar.mcpl.gz", 0, 0, 0);

  mcpltest_name_helper( "bla", 'm', "bla.mcpl" );
  mcpltest_name_helper( "bla", 'g', "bla.mcpl.gz" );
  mcpltest_name_helper( "bla", 'b', "bla" );
  mcpltest_name_helper( "bla.mcpl", 'm', "bla.mcpl" );
  mcpltest_name_helper( "bla.mcpl", 'g', "bla.mcpl.gz" );
  mcpltest_name_helper( "bla.mcpl", 'b', "bla" );
  mcpltest_name_helper( "bla.mcpl.gz", 'm', "bla.mcpl" );
  mcpltest_name_helper( "bla.mcpl.gz", 'g', "bla.mcpl.gz" );
  mcpltest_name_helper( "bla.mcpl.gz", 'b', "bla" );

  char * absfn = mcpl_name_helper( "foobar", 'G' );
  mcpl_dump(absfn, 0, 0, 0);
  free(absfn);
  return 0;
}
