
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
#include <stdio.h>
#include <memory.h>

int main(int argc,char**argv) {
  (void)argc;
  (void)argv;

  //Test mpi interface with nproc=1

  mcpl_outfile_t f = mcpl_create_outfile_mpi( "foobar", 0, 1 );
  mcpl_hdr_set_srcname(f,"CustomMPITest");
  mcpl_enable_universal_pdgcode(f,2112);
  mcpl_hdr_add_comment(f,"Some comment.");
  mcpl_hdr_add_comment(f,"Another comment.");
  mcpl_hdr_add_stat_sum(f,"foostat", -1.0 );

  //mpi: add particles:
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
    particle->weight = 0.0;
    mcpl_add_particle(f,particle);
  }

  //mpi: close files
  mcpl_hdr_add_stat_sum(f,"foostat", 10.0 );
  mcpl_closeandgzip_outfile(f);

  //Merge:
  mcpl_merge_outfiles_mpi( "foobar", 1 );

  //Dump:
  mcpl_dump("foobar.mcpl.gz", 0, 0, 0);

  return 0;
}
