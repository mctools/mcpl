
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
#include "mcpltestutils.h"
#include <stdio.h>


void mcpltests_custom_print_handler( const char * msg )
{
  printf("<custom>%s</custom>\n",msg);
}

int main(int argc,char**argv) {
  //Avoid unused warnings (can't simply omit the names in C):
  (void)argc;
  (void)argv;
  mcpl_set_print_handler(mcpltests_custom_print_handler);
  mcpl_dump(mcpltests_find_data("ref","reffile_1.mcpl"),0,0,10);
  mcpl_set_print_handler(NULL);
  mcpl_dump(mcpltests_find_data("ref","reffile_1.mcpl"),0,0,10);
  return 0;
}
