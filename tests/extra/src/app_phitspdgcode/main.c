
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

#include "phitsread.h"
#include <stdint.h>
#include <stdio.h>

int main( int argc, char** argv ) {
  (void)argc;
  (void)argv;

  //Pairs of { phitscode, pdgcode }. Here phitscode=0 indicate particle not
  //supported in phits and pdgcodes here includes nonsensical ones like -22 for
  //testing purposes):
  int32_t testphits[] = { 2212, 2212,
                          2112, 2112,
                          0, 2113,
                          -211, -211,
                          1000002, 1000010020,
                          2000004, 1000020040,
                          0, 1000020041,
                          0, 1010020040,
                          0, -1000020040,
                          6000012, 1000060120,
                          22, 22,
                          0, -22,
                          11, 11,
                          -11, -11,
                          -2212, -2212,
                          -2112, -2112,
                          111, 111,
                          0, -111,
                          331, 331,
                          0, -331,
                          0, 112,
                          3334, 3334,
                          -3334, -3334,
                          0, 3335,
                          0, 6,
                          0, 0,
                          0, 1,
                          0, 10 };

  for (unsigned i = 0; i < sizeof(testphits)/sizeof(*testphits)/2; ++i ) {
    int32_t code_phits = testphits[2*i];
    int32_t code_pdg = testphits[2*i+1];
    int32_t phits2pdg = conv_code_phits2pdg(code_phits);
    int32_t pdg2phits = conv_code_pdg2phits(code_pdg);
    printf("PHITS(%ld)->PDG(%ld), PDG(%ld)->PHITS(%ld)\n",
           (long)code_phits,
           (long)phits2pdg,
           (long)code_pdg,
           (long)pdg2phits);
    if (code_phits==0) {
      //Not supported in PHITS:
      if (!(phits2pdg==0))
        return 1;
      if (!(pdg2phits==0))
        return 1;
    } else {
      if (!(code_pdg!=0))
        return 1;
      if (!(pdg2phits==code_phits))
        return 1;
      if (!(phits2pdg==code_pdg))
        return 1;
    }
  }
  printf("Finished without errors!\n");

  return 0;
}
