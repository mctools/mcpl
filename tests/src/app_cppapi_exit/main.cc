
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

//Messages from MCPL while static objects are destroyed at program exit (the
//handler of mcpl::set_print_handler must stay alive while file objects exist,
//and must be freed eventually, for clean leak checks).

#include "mcpltest_cpputils.hh"

namespace {

  //Static object without MCPL files, created before the others (and therefore
  //destroyed after them), which compresses a file when destroyed. The handler
  //is gone by then, so the message goes to standard output:
  struct LateCompression {
    ~LateCompression()
    {
      std::cout << "LateCompression destructor" << std::endl;
      mcpl::gzip_file("late.mcpl");
      std::remove("late.mcpl.gz");
    }
  };
  LateCompression late_compression;

  //Static object with an output file, compressed when destroyed:
  struct GlobalWriter {
    mcpl::MCPLOutFile out{ "global.mcpl" };
    ~GlobalWriter()
    {
      std::cout << "GlobalWriter destructor" << std::endl;
      out.close_and_gzip();
      std::remove("global.mcpl.gz");
    }
  };
  GlobalWriter global_writer;

  void create_file( const char * filename )
  {
    mcpl::MCPLOutFile out( filename );
    auto p = out.new_particle();
    p.set_pdgcode(2112);
    p.set_ekin(1.0);
    p.set_direction(0,0,1);
    p.set_weight(1.0);
    out.add(p);
    out.close();
  }

}

int main()
{
  create_file("late.mcpl");
  mcpl::set_print_handler( []( const char * msg )
                           { std::cout << "[handler] " << msg; } );
  {
    auto p = global_writer.out.new_particle();
    p.set_pdgcode(2112);
    p.set_ekin(1.0);
    p.set_direction(0,0,1);
    p.set_weight(1.0);
    global_writer.out.add(p);
  }
  std::cout << "end of main" << std::endl;
  return 0;
}
