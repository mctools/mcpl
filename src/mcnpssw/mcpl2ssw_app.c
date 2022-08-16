#include "sswmcpl.h"

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// mcpl2ssw : a simple command line utility for converting MCPL to SSW.            //
//                                                                                 //
// This file can be freely used as per the terms in the LICENSE file.              //
//                                                                                 //
// However, note that usage of MCNP(X)-related utilities might require additional  //
// permissions and licenses from third-parties, which is not within the scope of   //
// the MCPL project itself.                                                        //
//                                                                                 //
// Written 2015-2016, thomas.kittelmann@ess.eu (European Spallation Source).       //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

int main(int argc,char** argv) {
  return mcpl2ssw_app(argc,argv);
}
