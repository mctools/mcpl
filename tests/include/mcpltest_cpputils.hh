#ifndef mcpltest_cpputils_hh
#define mcpltest_cpputils_hh

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

//Utilities for the tests of the C++ interface (mcplcpp.h).

#include "mcplcpp.h"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>

namespace mcpltest {

  [[noreturn]] inline void fail( const std::string& msg )
  {
    std::cout << "TEST FAILURE: " << msg << std::endl;
    std::exit(1);
  }

  inline void require( bool ok, const std::string& msg )
  {
    if ( !ok )
      fail(msg);
  }

  //Describe the exception being handled (type and message):
  inline std::string describe_current_exception()
  {
    std::string res;
    try {
      throw;
    } catch ( const mcpl::IOError& e ) {
      res = std::string("mcpl::IOError: ") + e.what();
    } catch ( const mcpl::Error& e ) {
      res = std::string("mcpl::Error: ") + e.what();
    } catch ( const std::bad_alloc& ) {
      res = "std::bad_alloc";
    } catch ( const std::out_of_range& e ) {
      res = std::string("std::out_of_range: ") + e.what();
    } catch ( const std::exception& e ) {
      res = std::string("other std::exception: ") + e.what();
    } catch (...) {
      res = "unknown exception";
    }
    return res;
  }

  //Run fct, which must throw, and print the exception:
  template<class Fct>
  void expect_throw( const std::string& what, Fct&& fct )
  {
    try {
      fct();
    } catch (...) {
      std::cout << what << " -> " << describe_current_exception() << std::endl;
      return;
    }
    fail( what + " did not throw" );
  }

  //Run fct, which must not throw, and print "ok":
  template<class Fct>
  void expect_ok( const std::string& what, Fct&& fct )
  {
    try {
      fct();
    } catch (...) {
      fail( what + " threw " + describe_current_exception() );
    }
    std::cout << what << " -> ok" << std::endl;
  }

  inline std::string file_contents( const std::string& filename )
  {
    std::ifstream f( filename, std::ios::binary );
    if ( !f )
      fail("could not open " + filename);
    return std::string( std::istreambuf_iterator<char>(f),
                        std::istreambuf_iterator<char>() );
  }

  inline void write_file( const std::string& filename,
                          const std::string& contents )
  {
    std::ofstream f( filename, std::ios::binary );
    f.write( contents.data(), static_cast<std::streamsize>(contents.size()) );
    if ( !f )
      fail("could not write " + filename);
  }

  inline bool file_exists( const std::string& filename )
  {
    std::ifstream f( filename, std::ios::binary );
    return static_cast<bool>(f);
  }

  //Collect messages from MCPL (instead of printing them), while in scope:
  class CollectMessages {
  public:
    CollectMessages()
    {
      mcpl::set_print_handler( [this]( const char * msg ) { m_msgs += msg; } );
    }
    ~CollectMessages() { mcpl::set_print_handler( nullptr ); }
    CollectMessages( const CollectMessages& ) = delete;
    CollectMessages& operator=( const CollectMessages& ) = delete;
    const std::string& str() const { return m_msgs; }
    void clear() { m_msgs.clear(); }
  private:
    std::string m_msgs;
  };

}

#endif
