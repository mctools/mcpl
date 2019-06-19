#include "phitsmcpl.h"

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// mcpl2phits : a simple command line utility for converting MCPL to binary
//              PHITS dump files.                                                  //
//                                                                                 //
// This file can be freely used as per the terms in the LICENSE file.              //
//                                                                                 //
// However, note that usage of PHITS-related utilities might require additional    //
// permissions and licenses from third-parties, which is not within the scope of   //
// the MCPL project itself.                                                        //
//                                                                                 //
// Written 2019, thomas.kittelmann@esss.se (European Spallation Source).           //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

int main(int argc,char** argv) {
  return mcpl2phits_app(argc,argv);
}
