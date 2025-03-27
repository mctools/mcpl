
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

#include "sswmcpl.h"

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// ssw2mcpl : a simple command line utility for converting SSW to MCPL.            //
//                                                                                 //
// This file can be freely used as per the terms in MCPLExport/license.txt.        //
//                                                                                 //
// However, note that usage of MCNP(X)-related utilities might require additional  //
// permissions and licenses from third-parties, which is not within the scope of   //
// the MCPL project itself.                                                        //
//                                                                                 //
// Written 2015-2016, thomas.kittelmann@ess.eu (European Spallation Source).       //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

//FIXME wmain for windows
int main(int argc,char** argv) {
  return ssw2mcpl_app(argc,argv);
}
