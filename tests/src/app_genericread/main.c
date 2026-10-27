
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

//The position in files read with the mcpl_generic_* functions (current_pos)
//is the same for plain and gzipped files, also when reading more than the
//size of the chunks in which they are read internally.

#include "mcpl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void create_file( const char * filename )
{
  mcpl_outfile_t f = mcpl_create_outfile(filename);
  mcpl_particle_t * p = mcpl_get_empty_particle(f);
  p->pdgcode = 2112;
  p->direction[2] = 1.0;
  p->weight = 1.0;
  for ( int i = 0; i < 5000; ++i ) {
    p->ekin = 1.0 + i;
    mcpl_add_particle(f,p);
  }
  mcpl_close_outfile(f);
}

int main(void)
{
  create_file("plain.mcpl");
  create_file("gz.mcpl");
  mcpl_gzip_file("gz.mcpl");
  const char * fns[2] = { "plain.mcpl", "gz.mcpl.gz" };
  const unsigned nreads[3] = { 100, 100000, 40000 };
  char * buf = (char*)malloc(100000);
  uint64_t pos[2][3];
  for ( int i = 0; i < 2; ++i ) {
    mcpl_generic_filehandle_t fh = mcpl_generic_fopen(fns[i]);
    for ( int j = 0; j < 3; ++j ) {
      mcpl_generic_fread(&fh,buf,nreads[j]);
      pos[i][j] = fh.current_pos;
    }
    mcpl_generic_fclose(&fh);
  }
  free(buf);
  int ok = 1;
  for ( int j = 0; j < 3; ++j ) {
    printf("after reading %u bytes: current_pos %lu (plain) and %lu (gzipped)\n",
           nreads[j],(unsigned long)pos[0][j],(unsigned long)pos[1][j]);
    if ( pos[0][j] != pos[1][j] )
      ok = 0;
  }
  remove("plain.mcpl");
  remove("gz.mcpl.gz");
  printf(ok ? "Positions agree\n" : "ERROR: positions differ\n");
  return ok ? 0 : 1;
}
