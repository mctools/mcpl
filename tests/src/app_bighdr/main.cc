
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

#include <cstdio>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <iostream>
#include "mcpl.h"

namespace {
  struct FileDeleter {
    ~FileDeleter()
    {
      //Make sure we do not leave such large files around after the test.
      std::remove("test.mcpl");
      std::remove("test.mcpl.gz");
    }
  };

#ifdef _MSC_VER
#  pragma warning( push )
#  pragma warning( disable : 4996 )
#endif
  bool mcpltest_file_exist( const char * fn )
  {
    FILE * fh = fopen(fn,"rb");
    if ( fh ) {
      fclose(fh);
      return true;
    }
    return false;
  }
#ifdef _MSC_VER
#  pragma warning( pop )
#endif

int do_test()
{
  FileDeleter guard;
  constexpr std::uint64_t nparticles = 1000;
  constexpr std::uint64_t bytes_per_particle = 96; //mcpl_hdr_particle_size
  constexpr std::uint64_t nblobs = 50; //mcpl_hdr_header_size
  constexpr std::uint64_t blobs_bytes = 4400000000; //mcpl_hdr_header_size
  constexpr std::uint64_t header_bytes = 4400000749; //mcpl_hdr_header_size
  constexpr std::uint64_t file_size = nparticles*bytes_per_particle + header_bytes;
  constexpr std::uint64_t val_uint32_max = std::numeric_limits<std::uint32_t>::max();

  static_assert( header_bytes > val_uint32_max,
                 "Test header large enough to exceed 32bit file positions" );
  static_assert( file_size > val_uint32_max,
                 "Test file large enough to exceed 32bit file positions" );
  static_assert( file_size < 2*val_uint32_max,
                 "Test file unnecessarily large" );

  static_assert(blobs_bytes%nblobs == 0, "" );
  constexpr std::uint64_t blobsize = blobs_bytes/nblobs;
  char * blob_buffer = (char*)malloc(blobsize);
  {
    for ( uint64_t i = 0; i < blobsize; ++i )
      blob_buffer[i] = (char)((unsigned char)(i%256)-128);
  }

  //copy vars trick to appease all compilers:
  uint64_t blobsize_copy = blobsize;
  uint64_t nblobs_copy = nblobs;
  auto validate_file_blobs = [&blob_buffer,
                              blobsize_copy,
                              nblobs_copy](const char * filename)
  {
    std::cout<<"Validating blob contents of "<<filename<<std::endl;
    mcpl_file_t f = mcpl_open_file(filename);
    int nb = mcpl_hdr_nblobs(f);
    if ( (uint64_t)nb != nblobs_copy )
      throw std::runtime_error("invalid mcpl_hdr_nblobs");
    for ( int i = 0; i < nb; ++i ) {
      char key[128];
      snprintf(key,sizeof(key),"blob%i",(int)i);
      uint32_t ldata;
      const char * data;
      if (!mcpl_hdr_blob(f, key, &ldata, &data) )
        throw std::runtime_error("could not retrieve blob");
      if ( ldata != blobsize_copy )
        throw std::runtime_error("blob has invalid size");
      for ( uint64_t j = 0; j < blobsize_copy; ++j )
        if ( blob_buffer[j] != data[j] )
          throw std::runtime_error("Unexpected blob contents");
    }
    mcpl_close_file(f);
    std::cout<<"Validated blob contents DONE"<<std::endl;
  };

  //Create file:
  {
    mcpl_outfile_t f = mcpl_create_outfile("test.mcpl");
    mcpl_particle_t* p =  mcpl_get_empty_particle(f);
    for ( std::uint64_t i = 0; i < nblobs; ++i ) {
      char key[128];
      snprintf(key,sizeof(key),"blob%i",(int)i);
      mcpl_hdr_add_data(f,key,blobsize,blob_buffer);
    }
    mcpl_enable_userflags(f);
    mcpl_enable_polarisation(f);
    mcpl_enable_doubleprec(f);
    p->direction[0] = 1.0;
    p->polarisation[0] = 1.0;
    p->ekin = 0.025;
    p->pdgcode = 2112;
    p->weight = 1.0;
    for ( std::uint64_t i = 0; i < nparticles; ++i )
      mcpl_add_particle(f,p);
    mcpl_close_outfile(f);
    mcpl_dump("test.mcpl", 0, 0, 10);
  }
  //Verify file:
  {
    mcpl_file_t f = mcpl_open_file("test.mcpl");

    if ( mcpl_hdr_header_size(f) != header_bytes )
      throw std::runtime_error("written file reports wrong header_size");
    if ( mcpl_hdr_nparticles(f) != nparticles )
      throw std::runtime_error("written file reports wrong nparticles");
    if ( mcpl_hdr_particle_size(f) != bytes_per_particle )
      throw std::runtime_error("written file reports wrong nparticles");
    std::uint64_t np_actual(0);
    while ( 1 ) {
      const mcpl_particle_t* p = mcpl_read(f);
      if (!p)
        break;
      ++np_actual;
    }
    if ( np_actual != nparticles )
      throw std::runtime_error("written file produced wrong nparticles");
    mcpl_close_file(f);
  }

  {
    //Dump file:
    mcpl_dump("test.mcpl", 0, 0, 10);
    mcpl_dump("test.mcpl", 0, nparticles-10, 1000 );
    validate_file_blobs("test.mcpl");
  }
  //Gzip file:
  {
    if (!mcpl_gzip_file("test.mcpl"))
      throw std::runtime_error("Could not gzip test.mcpl file");
    if ( mcpltest_file_exist("test.mcpl") )
      throw std::runtime_error("test.mcpl file did not disappear after being"
                               " compressed to test.mcpl.gz");
  }
  //Verify file:
  {
    mcpl_file_t f = mcpl_open_file("test.mcpl.gz");
    if ( mcpl_hdr_header_size(f) != header_bytes )
      throw std::runtime_error("written file reports wrong header_size");
    if ( mcpl_hdr_nparticles(f) != nparticles )
      throw std::runtime_error("written file reports wrong nparticles");
    if ( mcpl_hdr_particle_size(f) != bytes_per_particle )
      throw std::runtime_error("written file reports wrong nparticles");
    std::uint64_t np_actual(0);
    while ( 1 ) {
      const mcpl_particle_t* p = mcpl_read(f);
      if (!p)
        break;
      ++np_actual;
    }
    if ( np_actual != nparticles )
      throw std::runtime_error("written file produced wrong nparticles");
    mcpl_close_file(f);
  }
  {
    //Dump file:
    mcpl_dump("test.mcpl.gz", 0, 0, 10);
    mcpl_dump("test.mcpl.gz", 0, nparticles-10, 1000 );
    validate_file_blobs("test.mcpl.gz");
  }

  free(blob_buffer);
  return 0;
}

}//fixme in all files

int main( int, char** )
{
  int ec(1);
  {
    try {
      std::cout<< "Starting tests"<<std::endl;
      ec = do_test();
      std::cout<< "Tests done"<<std::endl;
    } catch( std::runtime_error& e ) {
      std::cout<< "ERROR: "<<e.what()<<std::endl;
      ec = 1;
      FileDeleter guard;
    }
  }
  {
    if ( mcpltest_file_exist("test.mcpl") )
      throw std::runtime_error("test.mcpl not cleaned up!");
  }
  {
    if ( mcpltest_file_exist("test.mcpl.gz") )
      throw std::runtime_error("test.mcpl.gz not cleaned up!");
  }
  return ec;
}
