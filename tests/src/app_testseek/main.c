
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

#include "mcpl.h"
#include "mcpltestutils.h"
#include <stdio.h>
#include <string.h>

void ppos(mcpl_file_t f)
{
  printf("  position is now: %llu\n",(unsigned long long)mcpl_currentposition(f));

}
void pp(mcpl_file_t f,const mcpl_particle_t*p)
{
  if (!p)
    printf("  got particle(NULL)!\n");
  else
    printf("  got particle(z=%g)\n",p->position[2]);
  ppos(f);
}

void testskip(const char * filename)
{
  mcpl_file_t f = mcpl_open_file(filename);
  unsigned long np = mcpl_hdr_nparticles(f);
  const mcpl_particle_t* p = 0;

  const char * bn = strrchr(filename, '/');
  bn = bn ? bn + 1 : filename;

  printf("**** Opened file %s with %lu particles\n",bn,np);
  ppos(f);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_skipforward 2 -> %i\n",mcpl_skipforward(f,2));
  ppos(f);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_rewind -> %i\n",mcpl_rewind(f));
  ppos(f);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_seek np-3 -> %i\n",mcpl_seek(f,np<3?0:np-3));
  ppos(f);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_rewind -> %i\n",mcpl_rewind(f));
  ppos(f);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_skipforward 9999999 -> %i\n",mcpl_skipforward(f,9999999));
  ppos(f);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_seek np-1 -> %i\n",mcpl_seek(f,np<1?0:np-1));
  ppos(f);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_seek %lu -> %i\n",np/2,mcpl_seek(f,np/2));
  ppos(f);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);
  printf("::mcpl_read\n");p=mcpl_read(f);
  pp(f,p);

  mcpl_close_file(f);
}

int mcpltests_testseek( const char * folder )
{
  testskip(mcpltests_find_data(folder,"reffile_1.mcpl"));
  testskip(mcpltests_find_data(folder,"reffile_skip123.mcpl"));
  testskip(mcpltests_find_data(folder,"reffile_skip123.mcpl.gz"));
  testskip(mcpltests_find_data(folder,"reffile_crash.mcpl"));
  testskip(mcpltests_find_data(folder,"reffile_empty.mcpl"));
}

int main(int argc,char**argv) {
  //Avoid unused warnings (can't simply omit the names in C):
  (void)argc;
  (void)argv;
  mcpltests_testseek("ref");
  mcpltests_testseek("reffmt2");
  return 0;

}
