
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

// NEEDS: C++17

//The library throwing exceptions of mcplcpp.h for app_cppexceptions, which loads
//it like a plugin (it is built with hidden symbols by default, as most plugins
//are).

#include "mcpltestmodutils.h"
#include "mcplcpp.h"

namespace {
  void throw_mcpl_error( int which )
  {
    if ( which == 0 ) {
      //(an I/O error, as the file does not exist):
      mcpl::MCPLFile f("no_such_file.mcpl");
    }
    //(an error which is not an I/O error, as the name is empty):
    mcpl::MCPLOutFile f("");
  }
}

//The function throwing, found by its name (it has C++ linkage itself, as
//exceptions pass through it):
using mcpltest_thrower_t = void(*)(int);
MCPLTEST_CTYPES mcpltest_thrower_t mcpltest_cppthrow_fct(void)
{
  return &throw_mcpl_error;
}
