
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

// The errors of mcplcpp.h (std::runtime_error) thrown in a library built with
// hidden symbols by default (lib_cppthrow, as many plugins are), which this
// program loads like a plugin, are caught as such here.

#include "mcplcpp.h"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#ifdef _WIN32
#  include <windows.h>
#else
#  include <dlfcn.h>
#endif

namespace {
  //The file of the test module (as for the Python tests):
  std::string testmod_file( const char * name )
  {
    std::string dir(".");
#ifdef _MSC_VER
    //(getenv gives a warning with MSVC):
    char * buf = nullptr;
    std::size_t n = 0;
    if ( _dupenv_s(&buf,&n,"MCTOOLS_TESTMODULES_LOCDIR") == 0 && buf )
      dir = buf;
    std::free(buf);
#else
    if ( const char * e = std::getenv("MCTOOLS_TESTMODULES_LOCDIR") )
      dir = e;
#endif
    std::ifstream f( dir + "/module_loc_TestMod_" + name + ".txt" );
    std::string path;
    std::getline(f,path);
    return path;
  }
}

int main()
{
  using thrower_t = void(*)(int);
  using getter_t = thrower_t(*)(void);
  const std::string lib = testmod_file("cppthrow");
  getter_t getter = nullptr;
#ifdef _WIN32
  HMODULE h = LoadLibraryA(lib.c_str());
  if ( h )
    getter = reinterpret_cast<getter_t>(GetProcAddress(h,"mcpltest_cppthrow_fct"));
#else
  void * h = dlopen(lib.c_str(),RTLD_NOW|RTLD_LOCAL);
  if ( h )
    getter = reinterpret_cast<getter_t>(dlsym(h,"mcpltest_cppthrow_fct"));
#endif
  if ( !getter ) {
    std::printf("could not load lib_cppthrow\n");
    return 1;
  }
  const char * what[] = { "opening a missing file", "empty output file name" };
  for ( int which = 0; which < 2; ++which ) {
    std::string res;
    try {
      getter()(which);
      res = "nothing thrown";
    } catch ( const std::runtime_error& e ) {
      res = std::string("caught as std::runtime_error: ") + e.what();
    } catch ( const std::exception& e ) {
      res = std::string("caught only as std::exception: ") + e.what();
    }
    std::printf("%s: %s\n",what[which],res.c_str());
  }
  return 0;
}
