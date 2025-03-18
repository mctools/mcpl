
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
#include <stdlib.h>

void mcpltests_simple_copy_file( const char * src,
                                 const char * tgt )
{
  //No error checking, not unicode support on windows!!
  char    buf[4096];
  FILE * fh_in  = fopen( src, "rb" );
  FILE * fh_out = fopen( tgt, "wb" );
  size_t  n;
  while ( (n=fread(buf,1,4096,fh_in)) != 0 )
    fwrite( buf, 1, n, fh_out );
  fclose(fh_in);
  fclose(fh_out);
}

void mcpltests_test_datafolder( const char* folder )
{
  char filename[128];
  for (unsigned count = 1;count<=16;++count) {
    sprintf(filename, "reffile_%i.mcpl",count);
    mcpl_dump(mcpltests_find_data(folder,filename),0,0,0);
  }
  mcpl_dump(mcpltests_find_data(folder,"reffile_crash.mcpl"),0,0,0);
  mcpl_dump(mcpltests_find_data(folder,"reffile_empty.mcpl"),0,0,0);

  mcpltests_simple_copy_file( mcpltests_find_data(folder,"reffile_7.mcpl"),
                              "reffile_7_copy.mcpl" );
  mcpl_merge_inplace("reffile_7_copy.mcpl",mcpltests_find_data(folder,"reffile_7.mcpl"));
  mcpl_dump("reffile_7_copy.mcpl",0,0,0);
}

int main(int argc,char**argv) {
  //Avoid unused warnings (can't simply omit the names in C):
  (void)argc;
  (void)argv;
  mcpltests_test_datafolder("ref");
  mcpltests_test_datafolder("reffmt2");
  return 0;
}
