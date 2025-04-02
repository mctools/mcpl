
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
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <string.h>

double mcpltests_random_double( unsigned long* rngstate ) {
  //Simple LCG:
  *rngstate = (1103515245 * (*rngstate) + 12345) % 2147483648;
  const double f = 1.0 / 2147483648;
  return (*rngstate) * f;
}

void mcpltests_randisotropic(double * dir, unsigned long* rngstate)
{
  //Very fast method (Marsaglia 1972) for generating points uniformly on the
  //unit sphere, costing approximately ~2.54 calls to rand() and 1 call to
  //sqrt().
  double x0,x1,s;
  do {
    x0 = 2.0*mcpltests_random_double(rngstate)-1.0;
    x1 = 2.0*mcpltests_random_double(rngstate)-1.0;
    s = x0*x0 + x1*x1;
  } while (!s||s>=1);
  double t = 2.0*sqrt(1-s);
  dir[0] = x0*t;
  dir[1] = x1*t;
  dir[2] = 1.0-2.0*s;
}

int mcpltests_genisotrop(int argc,char**argv) {


  if (argc!=3&&argc!=4) {
    printf("Usage:\n\n");
    printf("%s <nstat> <outfilename> [OPTIONS]\n\n",argv[0]);
    printf("OPTIONS is a string consisting of chars, each chars enabling a given option:\n");
    printf("   'e' : Add \"challenging\" (ascii, utf-8, binary data) comments and binary blobs\n");
    printf("   'f' : Enable userflags (all will be 0xdeadbeaf)\n");
    printf("   'i' : Enable userflags (all will be identical to file position)\n");
    printf("   'w' : Enable universal weight (will be 1.0)\n");
    printf("   'n' : Non-unit weights\n");
    printf("   'u' : Enable universal pdg code (2112, otherwise flips between 2112 and 22)\n");
    printf("   'p' : Enable polarisation.\n");
    printf("   'd' : Enable double precision.\n");
    printf("   'g' : gzip output file.\n");
    printf("   'c' : Simulate crash - dont close the file.\n");
    return 1;
  }
  int opt_enc = 0, opt_uf = 0, opt_uw = 0, opt_updg = 0, opt_pol = 0,
    opt_dp = 0, opt_crash = 0, opt_gzip = 0, opt_nonunitw = 0, opt_uf_idx = 0;
  if (argc==4) {
    for(size_t i = 0;i<strlen(argv[3]); ++i) {
      switch(argv[3][i]) {
      case 'e': opt_enc = 1; continue;
      case 'f': opt_uf = 1; continue;
      case 'i': opt_uf_idx = 1; continue;
      case 'w': opt_uw = 1; continue;
      case 'n': opt_nonunitw = 1; continue;
      case 'u': opt_updg = 1; continue;
      case 'p': opt_pol = 1; continue;
      case 'd': opt_dp = 1; continue;
      case 'g': opt_gzip = 1; continue;
      case 'c': opt_crash = 1; continue;
      default:
        printf("Unrecognised option\n");
        return 1;
      }
    }
  }

  if (opt_nonunitw&&opt_uw) {
    printf("Can not specify both w and n\n");
    return 1;
  }
  if (opt_uf&&opt_uf_idx) {
    printf("Can not specify both f and i\n");
    return 1;
  }
  long long nstat_raw = atoll(argv[1]);
  if ( nstat_raw < 0 ) {
    printf("negative nstat\n");
    return 1;
  }
  unsigned long long nstat = (unsigned long long)nstat_raw;
  const char * filename = argv[2];
  srand(117);
  mcpl_outfile_t f = mcpl_create_outfile(filename);
  mcpl_hdr_set_srcname(f,opt_enc ? "mctools/mcplt\xc3\xb8sts/genis\xc3\xb8""tr\xc3\xb8""p"
                       :"mctools/mcpltests/genisotrop" );
  mcpl_hdr_add_comment(f,"A simple file with isotropically generated particles.");

  if (opt_enc) {
    mcpl_hdr_add_comment(f,"A comment with utf8 chars: r\xc3\xb8""dgr\xc3\xb8""d med fl\xc3\xb8""de.");
    //\xff (255) and \xfe (254) can not appear in correct utf-8 strings:
    mcpl_hdr_add_comment(f,"A comment which contains bytes not valid in utf8: Bad bytes are \"\xff""\" and \"\xfe""\".");
    mcpl_hdr_add_data(f, "asciidata",31, "Just plain ascii.\nSecond line.\n");//data md5sum d3475b3d8393e4041df7fa22ade054d3
    mcpl_hdr_add_data(f, "asciidata_empty",0, "");//data md5sum d41d8cd98f00b204e9800998ecf8427e
    mcpl_hdr_add_data(f, "utf8data",22, "R\xc3\xb8""dgr\xc3\xb8""d med\nfl\xc3\xb8""de.\n");//data md5sum de7a6d4a3a291d0d67b3657e62ffcb37
    mcpl_hdr_add_data(f, "binarydata",9, "A\x00\x05\n\rBla\x7f");//data md5sum a04637816e7436951f0512d38d48f212
    mcpl_hdr_add_data(f, "utf8bl\xc3""\xb8""bkey",9, "A\x00\x05\n\rBla\x7f");//same
    mcpl_hdr_add_data(f, "notutf8key_\xff\xfe""_",9, "A\x00\x05\n\rBla\x7f");//same
    mcpl_hdr_add_comment(f,"md5sums of blobs: d3475b3d8393e4041df7fa22ade054d3,d41d8cd98f00b204e9800998ecf8427e,de7a6d4a3a291d0d67b3657e62ffcb37,a04637816e7436951f0512d38d48f212(*3)");

  }
  if (opt_updg)
    mcpl_enable_universal_pdgcode(f,2112);
  if (opt_uf||opt_uf_idx)
    mcpl_enable_userflags(f);
  if (opt_dp)
    mcpl_enable_doubleprec(f);
  if (opt_pol)
    mcpl_enable_polarisation(f);
  if (opt_uw)
    mcpl_enable_universal_weight(f,1.0);

  unsigned long rngstate = 1789569706;
  mcpltests_random_double(&rngstate);
  mcpltests_random_double(&rngstate);
  mcpltests_random_double(&rngstate);

  mcpl_particle_t * particle = mcpl_get_empty_particle(f);

  particle->weight = 1.0;
  particle->ekin = 0.0;
  particle->userflags = 0xdeadbeaf;
  particle->polarisation[2] = 0.5;
  if (opt_uf_idx)
    particle->userflags = 0;
  while(nstat--) {
    if (opt_uf_idx)
      particle->userflags += 1;
    mcpltests_randisotropic(particle->direction,&rngstate);
    if (!opt_updg)
      particle->pdgcode = (nstat%2?22:2112);
    if (opt_nonunitw)
      particle->weight = 10.0/(nstat+1);
    mcpl_add_particle(f,particle);
  }
  const char * ofntmp = mcpl_outfile_filename(f);
  size_t nn = strlen(ofntmp);
  char * ofn = (char*)malloc(nn+1);
  memcpy(ofn,ofntmp,nn+1);
  if (!opt_crash)
    mcpl_close_outfile(f);
  if (opt_gzip)
    mcpl_gzip_file(ofn);
  free(ofn);
  return 0;
}

int main(int argc,char**argv) {
  (void)argc;
  (void)argv;
  const char * fake_argv[4];
  fake_argv[0] = "mcpltests_genisotop";
  fake_argv[1] = "100";
  fake_argv[2] = "out.mcpl";
  fake_argv[3] = "efwupdg";
  if ( mcpltests_genisotrop(4,(char**)fake_argv) != 0 )
    return 1;
  mcpl_dump("out.mcpl.gz",0,0,10);

  fake_argv[2] = "out2.mcpl";
  fake_argv[3] = "in";
  if ( mcpltests_genisotrop(4,(char**)fake_argv) != 0 )
    return 1;
  mcpl_dump("out2.mcpl",0,0,10);

  return 0;
}
