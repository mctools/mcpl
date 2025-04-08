
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

// Test if using unicodes in filenames works OK everywhere (in particular on Windows).

#include "mcpl.h"
#include <stdio.h>
#include <stdlib.h>
//#include <memory.h>

int main(int argc,char**argv) {
  (void) argc;
  (void) argv;
  const char * filename = "r\xc3\xb8""dgr\xc3\xb8""d.mcpl";
  const char * filenamegz = "r\xc3\xb8""dgr\xc3\xb8""d.mcpl.gz";

  {
    mcpl_outfile_t f = mcpl_create_outfile(filename);
    mcpl_particle_t * particle = mcpl_get_empty_particle(f);
    particle->pdgcode = 22;
    particle->position[0] = 1.0;
    particle->position[1] = 2.0;
    particle->position[2] = 3.0;
    particle->direction[0] = 0.0;
    particle->direction[1] = 1.0;
    particle->direction[2] = 0.0;
    particle->time = 4.56;
    particle->weight = 0.123;
    mcpl_add_particle(f,particle);
    mcpl_closeandgzip_outfile(f);
  }

  //Verify that filename without .gz has disappeared:
  {
    mcpl_generic_filehandle_t fh = mcpl_generic_fopen_try(filename);
    if ( fh.internal ) {
      mcpl_generic_fclose( &fh );
      printf("ERROR: %s did not disappear upon gzip\n",filename);
      return 1;
    }
  }
  {
    mcpl_file_t f = mcpl_open_file(filenamegz);
    mcpl_close_file(f);
  }

  return 0;

}

