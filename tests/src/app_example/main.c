
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
#include "mcpltestutils.h"
#include <stdio.h>
#include <memory.h>
#include <math.h>

static int count = 0;
void my_write_file(const char * filename, int pol, int uf, int sp, int updg, int nparticles, int crash)
{
  count += 1;
  printf("========================= NEW FILE %s (count=%i) ==========================\n",filename,count);
  mcpl_outfile_t f = mcpl_create_outfile(filename);
  if (count%7!=0) {
    printf("  ==> mcpl_hdr_set_srcname(\"MyMCApp\")\n");
    mcpl_hdr_set_srcname(f,"MyMCApp");
  }
  if ((count+1)%3==0||count%12==0) {
    printf("  ==> mcpl_hdr_add_data(\"BlaData\",20,\"0123456789\\012345678\")\n");
    mcpl_hdr_add_data(f, "BlaData", 20, "0123456789""\0""12345678");
  }
  if (count%6==0) {
    printf("  ==> mcpl_hdr_add_data(\"LalaData\",6,\"01234\")\n");
    mcpl_hdr_add_data(f, "LalaData", 6, "01234");
  }
  if (count%3==0) {
    printf("  ==> mcpl_hdr_add_comment(\"Some comment.\")\n");
    mcpl_hdr_add_comment(f,"Some comment.");
    if (count%6==0) {
      printf("  ==> mcpl_hdr_add_comment(\"Some comment2.\")\n");
      mcpl_hdr_add_comment(f,"Some comment2.");
      printf("  ==> mcpl_hdr_add_comment(\"Some comment3.\")\n");
      mcpl_hdr_add_comment(f,"Some comment3.");
      printf("  ==> mcpl_hdr_add_comment(\"Some comment4444.\")\n");
      mcpl_hdr_add_comment(f,"Some comment4444.");
    }
  }

  if (pol) {
    printf("  ==> mcpl_enable_polarisation\n");
    mcpl_enable_polarisation(f);
  }
  if (uf) {
    printf("  ==> mcpl_enable_userflags\n");
    mcpl_enable_userflags(f);
  }
  if (!sp) {
    printf("  ==> mcpl_enable_doubleprec\n");
    mcpl_enable_doubleprec(f);
  }
  if (updg) {
    printf("  ==> mcpl_enable_universal_pdgcode(2112)\n");
    mcpl_enable_universal_pdgcode(f,2112);
  }

  //"Event loop":
  mcpl_particle_t p;
  memset(&p,0,sizeof(p));
  p.weight = 1.0;
  p.pdgcode = 2112;
  p.userflags=0xdeadbeef;
  printf("  ==> adding %i particles\n",nparticles);
  for ( int i = 0; i < nparticles; ++i ) {
    if (crash&&crash==i) {
      printf("  ==> \"crashing\"\n");
      fflush(0);
#if _WIN32
      _fcloseall();
#endif
      return;
    }
    p.ekin = (i%2==0?1.234:0.0);
    p.polarisation[0]=-0.01*i;
    p.position[2]=i*0.01;
    p.direction[0] = fmin(1.0,0.01*i);
    p.direction[1] = p.direction[2] = 0.0;
    p.direction[(i%3==0?1:2)] = sqrt(1.0-p.direction[0]*p.direction[0]) * (1 - 2 * (i%2));
    mcpl_add_particle(f,&p);
  }

  //finish:
  printf("  ==> closing file\n");
  mcpl_close_outfile(f);
  printf("  ==> done\n");

}

int main(int argc,char**argv) {
  //Avoid unused warnings (can't simply omit the names in C):
  (void)argc;
  (void)argv;

  char filename[65];
  for (int pol = 0; pol<=1; ++pol) {
    for (int sp = 0; sp<=1; ++sp) {
      for (int uf = 0; uf<=1; ++uf) {
        for (int updg = 0; updg<=1; ++updg) {
          snprintf(filename, sizeof(filename),"test_%i.mcpl",count+1);
          my_write_file(filename,pol,sp,uf,updg,5,0);
          mcpl_dump(filename,0,0,0);
        }
      }
    }
  }

  //empty file:
  my_write_file("test_empty.mcpl",1,1,0,0,0,0);
  mcpl_dump("test_empty.mcpl",0,0,0);

  //file improperly closed:
  my_write_file("test_crash.mcpl",0,0,0,0,5,4);
  mcpl_dump("test_crash.mcpl",0,0,0);

  //  return 0;

  //Merging:
  my_write_file("test_m1.mcpl",0,0,0,0,100,0);
  --count;
  my_write_file("test_m2.mcpl",0,0,0,0,123,0);
  --count;
  my_write_file("test_m3.mcpl",0,0,0,0,0,0);
  if (!mcpl_can_merge("test_m1.mcpl","test_m2.mcpl"))
    return 1;
  if (!mcpl_can_merge("test_m1.mcpl","test_m3.mcpl"))
    return 1;
  if (mcpl_can_merge("test_1.mcpl","test_2.mcpl"))
    return 2;
  mcpl_merge_inplace("test_m1.mcpl","test_m2.mcpl");
  mcpl_merge_inplace("test_m1.mcpl","test_m3.mcpl");
  mcpl_dump("test_m1.mcpl",1,0,0);
  mcpl_dump("test_m2.mcpl",1,0,0);
  mcpl_dump("test_m3.mcpl",1,0,0);
  mcpl_dump("test_m1.mcpl",2,0,6);
  mcpl_dump("test_m1.mcpl",2,100-3,6);
  mcpl_dump("test_m1.mcpl",2,223-3,0);

  //merge a fresh file with a reference file:
  mcpl_merge_inplace("test_3.mcpl",mcpltests_find_data("ref","reffile_3.mcpl"));
  mcpl_dump("test_3.mcpl",0,0,0);

  //Support (for a while) the obsolete version of mcpl_merge_inplace (which
  //prints warning):
  mcpl_merge("test_m1.mcpl","test_m2.mcpl");
  mcpl_dump("test_m1.mcpl",1,0,0);

  return 0;
}
