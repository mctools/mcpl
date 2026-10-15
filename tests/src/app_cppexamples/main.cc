
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

//Test of the C++ example in examples/example_cppmcpl.cc (of which
//example_cppmcpl.hh is a copy).

#define main main_cppmcpl
#include "example_cppmcpl.hh"
#undef main
#include <cstdio>
#include <string>

int main()
{
  //Input file with some neutrons and gammas:
  {
    mcpl::MCPLOutFile f("cppexample_in.mcpl");
    f.set_srcname("app_cppexamples");
    f.add_comment("input for the C++ example");
    auto p = f.new_particle();
    for ( int i = 0; i < 20; ++i ) {
      p.set_pdgcode( i % 3 ? 2112 : 22 );
      p.set_ekin( 0.02 * i );
      p.set_position( 1.0 * i, 0.0, -1.0 );
      p.set_direction( 0.6, 0.0, ( i % 2 ? 0.8 : -0.8 ) );
      p.set_time( 0.1 * i );
      p.set_weight( 1.0 + i );
      f.add(p);
    }
    f.close();
  }
  std::string output = "cppexample_out.mcpl";
  char * argv[3] = { const_cast<char*>("example_cppmcpl"),
                     const_cast<char*>("cppexample_in.mcpl"),
                     const_cast<char*>(output.c_str()) };
  int ec = main_cppmcpl(3,argv);
  if ( ec == 0 ) {
    std::cout << std::flush;
    mcpl_dump( output.c_str(), 0, 0, 10 );
  }
  std::remove( output.c_str() );
  //Missing input files give exceptions (reported by the example):
  char * argv2[3] = { const_cast<char*>("example_cppmcpl"),
                      const_cast<char*>("nosuchfile.mcpl"),
                      const_cast<char*>(output.c_str()) };
  std::cout << "With a missing input file:" << std::endl;
  int ec2 = main_cppmcpl(3,argv2);
  std::cout << "(exit code " << ec2 << ")" << std::endl;
  std::remove( "cppexample_in.mcpl" );
  return ( ec == 0 && ec2 == 1 ) ? 0 : 1;
}
