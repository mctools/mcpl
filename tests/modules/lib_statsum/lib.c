
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

MCPLTEST_CTYPE_DICTIONARY
{
  return
    "void mcpltest_createstatsumfile( const char *, const char *, double,   "
    "                                 const char *, const char*, unsigned );"
    "void mcpltest_dump( const char * );"
    ;
}

MCPLTEST_CTYPES void mcpltest_createstatsumfile( const char * filename,
                                                 const char * statsumname,
                                                 double statsumvalue,
                                                 const char * customcomment1,
                                                 const char * customcomment2,
                                                 unsigned nparticles )
{
  mcpl_outfile_t f = mcpl_create_outfile( filename );
  if ( strcmp(statsumname,"<NONE>") != 0 )
    mcpl_hdr_add_stat_sum(f,statsumname,statsumvalue);
  if ( strcmp(customcomment1,"<NONE>") != 0 )
    mcpl_hdr_add_comment(f,customcomment1);
  if ( strcmp(customcomment2,"<NONE>") != 0 )
    mcpl_hdr_add_comment(f,customcomment2);

  if ( nparticles ) {
    mcpl_particle_t * particle = mcpl_get_empty_particle(f);
    particle->direction[0] = 0.0;
    particle->direction[1] = 1.0;
    particle->direction[2] = 0.0;
    particle->ekin = 0.025;
    particle->pdgcode = 212;
    particle->weight = 0.123;
    for( unsigned i = 0; i < nparticles; ++i )
      mcpl_add_particle(f,particle);
  }
  mcpl_close_outfile(f);
}

MCPLTEST_CTYPES void mcpltest_dump( const char * filename )
{
  mcpl_dump(filename,0,0,0);
}
