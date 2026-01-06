
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

//Test that the following mini-main code for the mcpltool also compiles with C++
//(which is less liberal regarding const-ness when passing in argv):

#include "mcpl.h"

int main ( int, char** )
{
  const char * fake_argv_const[] = { "mcpltool",  "--help" };
  int fake_argc = sizeof(fake_argv_const)/sizeof(*fake_argv_const);
  char** fake_argv = const_cast<char**>(fake_argv_const);
  return mcpl_tool(fake_argc,fake_argv);
}
