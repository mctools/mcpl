
////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  This file is part of MCPL (see https://mctools.github.io/mcpl/)           //
//                                                                            //
//  Copyright 2015-2025 MCPL developers.                                      //
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

//Example creating files with statcumul.

#include "mcpl.h"
#include <stdio.h>

void create_file1(void)
{
  mcpl_outfile_t f = mcpl_create_outfile("file1.mcpl");
  mcpl_hdr_add_comment(f,"Some comment.");
  mcpl_hdr_add_statcumul( f, "nsrc", 2.0 );
  mcpl_hdr_add_comment(f,"Another comment.");
  mcpl_hdr_add_statcumul( f, "nsrc2", -1 );
  mcpl_hdr_add_comment(f,"Another comment.");
  mcpl_hdr_add_statcumul( f, "nsrc3", -1 );
  mcpl_hdr_add_comment(f,"Another comment.");
  mcpl_hdr_add_statcumul( f, "nsrc3", 2.0 );
  mcpl_close_outfile(f);
}

void mcpltests_add_particles( mcpl_outfile_t f, unsigned n )
{
  mcpl_particle_t * particle = mcpl_get_empty_particle(f);
  particle->direction[0] = 0.0;
  particle->direction[1] = 0;
  particle->direction[2] = 1.0;
  particle->ekin = 0.025;
  particle->pdgcode = 212;
  particle->weight = 0.1;
  for( unsigned i = 0; i < n; ++i )
    mcpl_add_particle(f,particle);
}

void create_file2(void)
{
  mcpl_outfile_t f = mcpl_create_outfile("file2.mcpl");
  mcpl_hdr_add_comment(f,"Some comment.");
  mcpl_hdr_add_statcumul( f, "nsrc", -1.0 );
  mcpl_hdr_add_statcumul( f, "nsrc other", 123456.123 );
  mcpl_hdr_add_statcumul( f, "nsrc other", 1234567.123 );
  mcpl_hdr_add_statcumul( f, "nsrc other2", 123456789 );
  mcpl_hdr_add_statcumul( f, "ccc", -1.0 );
  mcpl_hdr_add_statcumul( f, "aaa", 1 );
  mcpl_hdr_add_statcumul( f, "aa2", 2 );
  mcpl_hdr_add_statcumul( f, "bbb", 1 );
  mcpl_hdr_add_statcumul( f, "bb", 2 );
  mcpl_hdr_add_comment(f,"Another comment.");

  mcpl_hdr_add_statcumul( f, "nsrc", 2.123e-3 );
  mcpltests_add_particles(f, 1000);
  mcpl_hdr_add_statcumul( f, "aa2", 17 );

  mcpl_close_outfile(f);
}

void create_file3(const char * filename,double statval)
{
  static int i = 0;
  mcpl_outfile_t f = mcpl_create_outfile(filename);
  int delay = ( (i++) %2 == 0 );
  mcpl_hdr_add_statcumul( f, "nsrc", delay? -1.0 : statval );
  mcpltests_add_particles(f, 1);
  if ( delay )
    mcpl_hdr_add_statcumul( f, "nsrc", statval );
  mcpl_close_outfile(f);
  mcpl_dump(filename,0,0,1);
}


int main(int argc,char**argv) {
  (void)argc;
  (void)argv;
  create_file1();
  mcpl_dump("file1.mcpl",0,0,10);
  create_file2();
  mcpl_dump("file2.mcpl",0,0,10);

  create_file3("f3_unset.mcpl",-1.0);
  create_file3("f3_2d5.mcpl",2.5);
  create_file3("f3_17.mcpl",17);

  return 0;
}
