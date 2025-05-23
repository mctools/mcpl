
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

//Example creating files with stat:sum:.

#include "mcpl.h"
#include <stdio.h>

void create_file1(void)
{
  mcpl_outfile_t f = mcpl_create_outfile("file1.mcpl");
  mcpl_hdr_add_comment(f,"Some comment.");
  mcpl_hdr_add_stat_sum( f, "nsrc", 2.0 );
  mcpl_hdr_add_comment(f,"Another comment.");
  mcpl_hdr_add_stat_sum( f, "nsrc2", -1 );
  mcpl_hdr_add_comment(f,"Another comment.");
  mcpl_hdr_add_stat_sum( f, "nsrc3", -1 );
  mcpl_hdr_add_comment(f,"Another comment.");
  mcpl_hdr_add_stat_sum( f, "nsrc3", 2.0 );
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
  mcpl_hdr_add_stat_sum( f, "nsrc", -1.0 );
  mcpl_hdr_add_stat_sum( f, "nsrc_other", 123456.123 );
  mcpl_hdr_add_stat_sum( f, "nsrc_other", 1234567.123 );
  mcpl_hdr_add_stat_sum( f, "nsrc_other2", 123456789 );
  mcpl_hdr_add_stat_sum( f, "ccc", -1.0 );
  mcpl_hdr_add_stat_sum( f, "aaa", 1 );
  mcpl_hdr_add_stat_sum( f, "aa2", 2 );
  mcpl_hdr_add_stat_sum( f, "bbb", 1 );
  mcpl_hdr_add_stat_sum( f, "bb", 2 );
  mcpl_hdr_add_comment(f,"Another comment.");

  mcpl_hdr_add_stat_sum( f, "nsrc", 2.123e-3 );
  mcpltests_add_particles(f, 1000);
  mcpl_hdr_add_stat_sum( f, "aa2", 17 );

  mcpl_close_outfile(f);
}

void create_file3(const char * filename,double statval)
{
  static int i = 0;
  mcpl_outfile_t f = mcpl_create_outfile(filename);
  int delay = ( (i++) %2 == 0 );
  mcpl_hdr_add_stat_sum( f, "nsrc", delay? -1.0 : statval );
  mcpltests_add_particles(f, 1);
  if ( delay )
    mcpl_hdr_add_stat_sum( f, "nsrc", statval );
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
  {
    const char *fns[2] = {"f3_2d5.mcpl","f3_17.mcpl"};
    mcpl_outfile_t of = mcpl_merge_files( "f3_mergeok.mcpl", 2, fns );
    mcpl_close_outfile(of);
    mcpl_dump("f3_mergeok.mcpl",0,0,10);
  }
  {
    const char *fns[3] = {"f3_unset.mcpl","f3_2d5.mcpl","f3_17.mcpl"};
    mcpl_outfile_t of = mcpl_merge_files( "f3_mergeall.mcpl", 3, fns );
    mcpl_close_outfile(of);
    mcpl_dump("f3_mergeall.mcpl",0,0,10);
  }

  {
    //floating point fun: 1.0+1e-16+1e-16+1e-16+1e-16 is 1.0, but 1.0+4e-16 is
    //not 1.  Without using stablesum for the stats during merges, we would end
    //up with 1 and not 1.0000000000000004 like we should.
    create_file3("f4_1.mcpl",1.0);
    create_file3("f4_epsa.mcpl",1e-16);
    create_file3("f4_epsb.mcpl",1e-16);
    create_file3("f4_epsc.mcpl",1e-16);
    create_file3("f4_epsd.mcpl",1e-16);

    const char *fns[5] = {"f4_1.mcpl","f4_epsa.mcpl",
                          "f4_epsb.mcpl","f4_epsc.mcpl","f4_epsd.mcpl"};
    mcpl_outfile_t of = mcpl_merge_files( "f4_mergeall.mcpl", 5, fns );
    mcpl_close_outfile(of);
    mcpl_dump("f4_mergeall.mcpl",0,0,10);
    mcpl_file_t f = mcpl_open_file("f4_mergeall.mcpl");
    printf("mcpl_hdr_stat_sum(\"nsrc\") = %.17g\n",
           mcpl_hdr_stat_sum(f,"nsrc"));
    printf("mcpl_hdr_stat_sum(\"foo\") = %.17g\n",
           mcpl_hdr_stat_sum(f,"foo"));
    if ( mcpl_hdr_stat_sum(f,"nsrc") != 1.0 + 4e-16
         || !(mcpl_hdr_stat_sum(f,"nsrc")>1.0 ) ) {
      printf("stats were not added in stable manner\n");
      return 1;
    }

    mcpl_close_file(f);
  }


  {
    //1.7976931348623157e+308 is largest dbl which is not inf, so merging these
    //two files will overflow the FP range:
    create_file3("f5_a.mcpl",1.2e308);
    create_file3("f5_b.mcpl",1.1e308);
    const char *fns[2] = {"f5_a.mcpl","f5_b.mcpl"};
    mcpl_outfile_t of = mcpl_merge_files( "f5_merge.mcpl", 2, fns );
    mcpl_close_outfile(of);
    mcpl_dump("f5_merge.mcpl",0,0,10);
  }

  {
    //Like previous test, but slightly smaller so should be in range:
    create_file3("f6_a.mcpl",0.8e308);
    create_file3("f6_b.mcpl",0.9e308);
    const char *fns[2] = {"f6_a.mcpl","f6_b.mcpl"};
    mcpl_outfile_t of = mcpl_merge_files( "f6_merge.mcpl", 2, fns );
    mcpl_close_outfile(of);
    mcpl_dump("f6_merge.mcpl",0,0,10);
  }



  return 0;
}
