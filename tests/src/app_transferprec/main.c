
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
#include <math.h>

//Test mcpl_transfer_last_read_particle between files with different floating
//point precision and polarisation settings, which reuses the packed
//direction+ekin of the source particle when possible.

void mcpltests_write( const char * filename, int doubleprec, int pol )
{
  mcpl_outfile_t f = mcpl_create_outfile(filename);
  if (doubleprec)
    mcpl_enable_doubleprec(f);
  if (pol)
    mcpl_enable_polarisation(f);
  mcpl_particle_t * p = mcpl_get_empty_particle(f);
  const double dirs[3][3] = { { 0.0, 0.6, 0.8 },
                              { -0.48, 0.6, -0.64 },
                              { 1.0, 0.0, 0.0 } };
  for ( int i = 0; i < 3; ++i ) {
    p->position[0] = 1.0 + i;
    p->position[1] = -2.0;
    p->position[2] = 3.5;
    for ( int j = 0; j < 3; ++j )
      p->direction[j] = dirs[i][j];
    p->polarisation[0] = 0.25 * i;
    p->ekin = 2.5 * ( i + 1 );
    p->time = 0.125 * i;
    p->weight = 1.5;
    p->pdgcode = 2112;
    mcpl_add_particle(f,p);
  }
  mcpl_close_outfile(f);
}

void mcpltests_transfer( int src_doubleprec, int src_pol,
                         int tgt_doubleprec, int tgt_pol )
{
  mcpltests_write("src.mcpl",src_doubleprec,src_pol);
  mcpl_file_t fi = mcpl_open_file("src.mcpl");
  mcpl_outfile_t fo = mcpl_create_outfile("tgt.mcpl");
  if (tgt_doubleprec)
    mcpl_enable_doubleprec(fo);
  if (tgt_pol)
    mcpl_enable_polarisation(fo);
  while ( mcpl_read(fi) )
    mcpl_transfer_last_read_particle(fi,fo);
  mcpl_close_outfile(fo);
  mcpl_close_file(fi);

  printf("Transfer from %s precision%s to %s precision%s:\n",
         src_doubleprec ? "double" : "single", src_pol ? " with polarisation" : "",
         tgt_doubleprec ? "double" : "single", tgt_pol ? " with polarisation" : "");
  mcpl_file_t fa = mcpl_open_file("src.mcpl");
  mcpl_file_t fb = mcpl_open_file("tgt.mcpl");
  const mcpl_particle_t * a;
  while ( ( a = mcpl_read(fa) ) ) {
    const mcpl_particle_t * b = mcpl_read(fb);
    int ok = ( fabs( b->ekin - a->ekin ) < 1e-6 * a->ekin
               && fabs( b->direction[0] - a->direction[0] ) < 1e-6
               && fabs( b->direction[1] - a->direction[1] ) < 1e-6
               && fabs( b->direction[2] - a->direction[2] ) < 1e-6
               && b->position[0] == a->position[0]
               && b->time == a->time );
    printf("  ekin=%g dir=(%g,%g,%g) x=%g t=%g pol-x=%g : %s\n",
           b->ekin, b->direction[0], b->direction[1], b->direction[2],
           b->position[0], b->time, b->polarisation[0],
           ok ? "same as source" : "DIFFERENT FROM SOURCE");
  }
  mcpl_close_file(fa);
  mcpl_close_file(fb);
}

int main(int argc,char**argv) {
  (void)argc;
  (void)argv;
  for ( int src_dp = 0; src_dp < 2; ++src_dp )
    for ( int src_pol = 0; src_pol < 2; ++src_pol )
      for ( int tgt_dp = 0; tgt_dp < 2; ++tgt_dp )
        for ( int tgt_pol = 0; tgt_pol < 2; ++tgt_pol )
          mcpltests_transfer(src_dp,src_pol,tgt_dp,tgt_pol);
  return 0;
}
