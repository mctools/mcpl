
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


#include "mcpl.h"
#include <stdio.h>
#include <stdlib.h>
#include <memory.h>

int fakerandfct(void);
#define FAKE_RAND_MAX 1000

#ifdef RAND_MAX
#  undef RAND_MAX
#endif
#define RAND_MAX FAKE_RAND_MAX
#define rand fakerandfct

#ifdef main
#  undef main
#endif
#define main main_readmcpl
#include "example_readmcpl.h"
#undef main
#define main main_writemcpl
#include "example_writemcpl.h"
#undef main
#define main main_filtermcpl
#include "example_filtermcpl.h"
#undef main

#include <string.h>

void setstr( char ** dest, const char * str )
{
  size_t n = strlen(str) + 1;
  char * ptr = malloc( n );
  if ( !ptr )
    exit( 2 );
  memcpy(ptr,str,n);
  *dest = ptr;
}

void do_readmcpl( const char * filename )
{
  printf("do_readmcpl( \"%s\" )\n", filename );
  char * argv[2];
  setstr(&argv[0],"appreadmcpl");
  setstr(&argv[1],filename);
  int ec = main_readmcpl(2,(char**)argv);
  free(argv[0]);
  free(argv[1]);
  if ( ec != 0 )
    exit(1);
}

void do_writemcpl( const char * filename )
{
  printf("do_writemcpl( \"%s\" )\n", filename );
  char * argv[2];
  setstr(&argv[0],"appwritemcpl");
  setstr(&argv[1],filename);
  int ec = main_writemcpl(2,(char**)argv);
  free(argv[0]);
  free(argv[1]);
  if ( ec != 0 )
    exit(1);
}

void do_filtermcpl( const char * filename, const char * outfilename )
{
  printf("do_filtermcpl( \"%s\", \"%s\" )\n", filename, outfilename );
  char * argv[3];
  setstr(&argv[0],"appfiltermcpl");
  setstr(&argv[1],filename);
  setstr(&argv[2],outfilename);
  int ec = main_filtermcpl(3,(char**)argv);
  free(argv[0]);
  free(argv[1]);
  free(argv[2]);
  if ( ec != 0 )
    exit(1);
}

int main( int argc, char ** argv )
{
  (void)argc;
  (void)argv;

  do_writemcpl("dummy.mcpl");
  mcpl_dump("dummy.mcpl.gz", 0, 0, 10);
  do_readmcpl("dummy.mcpl.gz");
  do_filtermcpl("dummy.mcpl.gz","dummyfiltered");
  mcpl_dump("dummyfiltered.mcpl.gz", 0, 0, 10);
  do_readmcpl("dummyfiltered.mcpl.gz");

  return 0;
}

int fakerandfct(void)
{
  //Worst RNG, but that is not the point for this test:
  static int i = 113;
  i += 293;
  i = i % (FAKE_RAND_MAX+1);
  return i;
}
