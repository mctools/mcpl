
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

#include "sswread.h"
#include <stdint.h>
#include <stdio.h>

//List of mcnpx itypes encoded in ssw files and corresponding pdg code:

static const int64_t known_mcnpx_mappings[] = {
  420, -211,//pi-
  20, 211,//pi+
  4, 13,//mu-
  404, -13,//mu+
  3, 11,//e-
  403, -11,//e+
  6, 12,//nu-e
  406, -12,//nu-e-bar
  26057035, 1000270570,//ion (Z,A)=(27,57)
  26060035, 1000270600,//ion (Z,A)=(27,60)
  54137035, 1000551370,//ion (Z,A)=(55,137)
  31, 1000010020,//deuteron
  33, 1000020030,//He3
  34, 1000020040,//alpha/He4
  1, 2112,//neutron
  2, 22,//gamma
  402, 22,//gamma specified as anti-gamma
  9, 2212,//proton
  401, -2112,//anti neutron
  409, -2212,//anti proton
  203, 11,//electron in some energy group
  603, -11,//positron in some energy group
  403, -11,//positron
  202, 22,//gamma in some energy group
  602, 22,//anti gamma (which is... gamma) in some energy group
  402, 22,//anti gamma (which is... gamma)
  26057235, 1000270570,//ion (Z,A)=(27,57) in some energy group
  26057435, -1000270570,//anti ion (Z,A)=(27,57)
  26057635, -1000270570,//anti ion (Z,A)=(27,57) in some energy group
};

//List of mcnp6 itypes encoded in ssw files, corresponding pdg code, and (if
//non-zero) expected/desired result of converting back to mcnp6 ssw format:

static const int64_t known_mcnp6_mappings[] = {
  70, -211, 0,//pi-
  40, 211, 0,//pi+
  8, 13, 0,//mu-
  7304, 13, 8,//mu- with corrupted AAA from having (Z,A)=(27,57) in same job.
  7688, 13, 8,//mu- with corrupted AAA from having (Z,A)=(27,60) in same job.
  17544, 13, 8,//mu- with corrupted AAA from having (Z,A)=(55,137) in same job.
  32, -13, 0,//mu+
  6, 11, 0,//e-
  7, -11, 7,//e+
  16, -11, 7,//e+ [not observed in files, but logically 16 should also mean e+]
  12, 12, 0,//nu-e
  34, -12, 0,//nu-e-bar
  14, 14, 0,//nu-mu
  36, -14, 0,//nu-mu-bar
  1776842, 1000270570, 0,//ion (Z,A)=(27,57)
  1777226, 1000270600, 0,//ion (Z,A)=(27,60)
  3622090, 1000551370, 0,//ion (Z,A)=(55,137)
  62, 1000010020, 0,//deuteron
  7358, 1000010020, 62,//deuteron with corrupted AAA from having (Z,A)=(27,57) in same job.
  7742, 1000010020, 62,//deuteron with corrupted AAA from having (Z,A)=(27,60) in same job.
  17598, 1000010020, 62,//deuteron with corrupted AAA from having (Z,A)=(55,137) in same job.
  66, 1000020030, 0,//He3
  7362, 1000020030, 66,//He3 with corrupted AAA from having (Z,A)=(27,57) in same job.
  7746, 1000020030, 66,//He3 with corrupted AAA from having (Z,A)=(27,60) in same job.
  17602, 1000020030, 66,//He3 with corrupted AAA from having (Z,A)=(55,137) in same job.
  68, 1000020040, 0,//alpha/He4
  7364, 1000020040, 68,//alpha/He4 with corrupted AAA from having (Z,A)=(27,57) in same job.
  7748, 1000020040, 68,//alpha/He4 with corrupted AAA from having (Z,A)=(27,60) in same job.
  17604, 1000020040, 68,//alpha/He4 with corrupted AAA from having (Z,A)=(55,137) in same job.
  2, 2112, 0,//neutron
  4, 22, 0,//gamma
  5, 22, 4,//gamma specified as anti-gamma
  18, 2212, 0,//proton
  10, -2112, 0,//anti neutron
  38, -2212, 0,//anti proton
};

int main(void){

  for ( unsigned i = 0;
        i < sizeof(known_mcnpx_mappings)/sizeof(known_mcnpx_mappings[0]);
        i+=2 ) {
    int64_t mcnpx = known_mcnpx_mappings[i];
    if ( mcnpx <= INT32_MIN || mcnpx >= INT32_MAX ) {
      printf("mcnpx type outside of 32bit range!\n");
      return 1;
    }
    int64_t pdgconv = conv_mcnpx_ssw2pdg((int32_t)mcnpx);
    int64_t pdg = known_mcnpx_mappings[i+1];
    printf("conv_mcnpx_ssw2pdg(%li) = %li\n",(long)mcnpx,(long)pdgconv);
    if (pdg!=pdgconv||!pdgconv) {
      printf("Conversion failed (expected %li)!\n",(long)pdg);
      return 1;
    }
    if ( pdg <= INT32_MIN || pdg >= INT32_MAX ) {
      printf("pdg code outside of 32bit range!\n");
      return 1;
    }
    int64_t mcnpxconv = conv_mcnpx_pdg2ssw((int32_t)pdg);
    if ((mcnpx%1000)/200==1 || (mcnpx%1000)/600==1)
      mcnpx -= 200;//reverse mapping can't know about energy groups
    if (mcnpx==402)
      mcnpx = 2;//reverse mapping can't know gamma was specified as anti-gamma
    if (mcnpx!=mcnpxconv) {
      printf("Reverse conversion via conv_mcnpx_pdg2ssw"
             " failed (got %li)!\n",(long)mcnpxconv);
      return 1;
    }
  }

  for ( unsigned i = 0;
        i < sizeof(known_mcnp6_mappings)/sizeof(known_mcnp6_mappings[0]);
        i+=3 ) {
    int64_t mcnp6 = known_mcnp6_mappings[i];
    int64_t pdg = known_mcnp6_mappings[i+1];
    int64_t mcnp6_desiredreverse = known_mcnp6_mappings[i+2];
    if (!mcnp6_desiredreverse)
      mcnp6_desiredreverse = mcnp6;
    if ( mcnp6 <= INT32_MIN || mcnp6 >= INT32_MAX ) {
      printf("mcnp6 type outside of 32bit range!\n");
      return 1;
    }
    int64_t pdgconv = conv_mcnp6_ssw2pdg((int32_t)mcnp6);
    printf("conv_mcnp6_ssw2pdg(%li) = %li\n",(long)mcnp6,(long)pdgconv);
    if (pdg!=pdgconv||!pdgconv) {
      printf("Conversion failed (expected %li)!\n",(long)pdg);
      return 1;
    }
    if ( pdg <= INT32_MIN || pdg >= INT32_MAX ) {
      printf("pdg code outside of 32bit range!\n");
      return 1;
    }
    int64_t mcnp6conv = conv_mcnp6_pdg2ssw((int32_t)pdg);
    if (mcnp6_desiredreverse!=mcnp6conv) {
      printf("Reverse conversion via conv_mcnp6_pdg2ssw failed (got"
             " %li, wanted %li)!\n",(long)mcnp6conv,(long)mcnp6_desiredreverse);
      return 1;
    }
  }

  return 0;
}
