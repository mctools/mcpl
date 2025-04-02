#include "phitsmcpl.h"

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// phits2mcpl : a simple command line utility for converting binary PHITS dump     //
//              files to MCPL.                                                     //
//                                                                                 //
// This file can be freely used as per the terms in MCPLExport/license.txt.        //
//                                                                                 //
// However, note that usage of PHITS-related utilities might require additional    //
// permissions and licenses from third-parties, which is not within the scope of   //
// the MCPL project itself.                                                        //
//                                                                                 //
// Written 2019, thomas.kittelmann@ess.eu (European Spallation Source).            //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

int main(int argc,char** argv) {
  return phits2mcpl_app(argc,argv);
}
