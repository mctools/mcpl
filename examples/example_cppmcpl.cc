
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

// A small standalone example of how one might use the C++ interface of MCPL
// (mcplcpp.h, which requires C++17 or later) to read particles from an
// existing MCPL file, and to write some of them to a new file, along with
// some custom per-particle data (userdata).

#include "mcplcpp.h"
#include <cstdint>
#include <iostream>

int main( int argc, char ** argv )
{
  if ( argc != 3 ) {
    std::cout << "Please supply input and output filenames" << std::endl;
    return 1;
  }

  //Errors are reported as exceptions (mcpl::Error, or the derived
  //mcpl::IOError for problems with reading or writing files):
  try {

    //Open the input file, and show some of the information in its header:
    mcpl::MCPLFile fin( argv[1] );
    std::cout << "Input file has " << fin.nparticles() << " particles from \""
              << fin.srcname() << "\"" << std::endl;
    for ( auto comment : fin.comments() )
      std::cout << "  comment: " << comment << std::endl;

    //Create the output file. Each particle in it will also have the index of
    //the particle in the input file, and the original direction (as userdata
    //fields "index:uint64" and "origdir:float32[3]"):
    mcpl::MCPLOutFile fout( argv[2] );
    fout.set_srcname( "example_cppmcpl" );
    fout.add_comment( "Neutrons with ekin<0.1MeV, sent along the z axis" );
    auto index = fout.add_userdata_field<std::uint64_t>( "index" );
    auto origdir = fout.add_userdata_field<float,3>( "origdir" );
    auto out = fout.new_particle();

    //Loop over the particles in the input file, adding the chosen ones (after
    //changing their direction) to the output file:
    std::uint64_t i = 0;
    for ( auto p : fin ) {
      if ( p.pdgcode() == 2112 && p.ekin() < 0.1 ) {
        out.set_pdgcode( p.pdgcode() );
        out.set_ekin( p.ekin() );
        out.set_position( p.position() );
        out.set_direction( 0.0, 0.0, 1.0 );
        out.set_time( p.time() );
        out.set_weight( p.weight() );
        out.set_userdata( index, i );
        auto d = p.direction();
        out.set_userdata( origdir, { float(d[0]), float(d[1]), float(d[2]) } );
        fout.add( out );
      }
      ++i;
    }

    //Close the output file (output files which are not closed are left
    //unfinished, for instance if an exception was thrown above):
    fout.close();

    //Read the new file:
    mcpl::MCPLFile fnew( argv[2] );
    std::cout << "Output file has " << fnew.nparticles()
              << " particles with userdata \"" << fnew.userdata_layout()
              << "\". The first ones are:" << std::endl;
    auto newindex = fnew.userdata_field<std::uint64_t>( "index" );
    auto neworigdir = fnew.userdata_field<float,3>( "origdir" );
    for ( auto p : fnew ) {
      if ( fnew.current_position() > 5 )
        break;
      std::cout << "  ekin=" << p.ekin() << "MeV, particle " << newindex(p)
                << " in the input file, which had uz="
                << neworigdir(p,2) << std::endl;
    }

  } catch ( const mcpl::Error& e ) {
    std::cout << "Error: " << e.what() << std::endl;
    return 1;
  }
  return 0;
}
