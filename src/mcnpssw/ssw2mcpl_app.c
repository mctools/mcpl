#include "sswmcpl.h"

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// ssw2mcpl : a simple command line utility for converting SSW to MCPL.            //
//                                                                                 //
// This file can be freely used as per the terms in the LICENSE file.              //
//                                                                                 //
// However, note that usage of MCNP(X)-related utilities might require additional  //
// permissions and licenses from third-parties, which is not within the scope of   //
// the MCPL project itself.                                                        //
//                                                                                 //
// Written 2015-2016, thomas.kittelmann@esss.se (European Spallation Source).      //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

int main(int argc,char** argv) {
  return ssw2mcpl_app(argc,argv);
}
