
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

// A small standalone example of how to one might extract a subset of particles
// from an existing MCPL file in order to create a new smaller file.

#include "mcpl.h"
#include <stdio.h>

int main(int argc,char**argv) {

  if (argc!=3) {
    printf("Please supply input and output filenames\n");
    return 1;
  }

  const char * infilename = argv[1];
  const char * outfilename = argv[2];

  // Initialisation, open existing file and create output file handle. Transfer
  // all meta-data from existing file, and add an extra comment in the output
  // file to document the process:

  mcpl_file_t fi = mcpl_open_file(infilename);
  mcpl_outfile_t fo = mcpl_create_outfile(outfilename);
  mcpl_transfer_metadata(fi, fo);
  mcpl_hdr_add_comment( fo, "Applied filter for neutrons with ekin<0.1MeV");

  //Loop over particles from input, only adding the chosen particles to the
  //output file:
  const mcpl_particle_t* particle;
  while ( 1 ) {
    particle = mcpl_read(fi);
    if ( !particle )
      break;
    if ( particle->pdgcode == 2112 && particle->ekin < 0.1 ) {
      mcpl_add_particle(fo,particle);
      //Note that a guaranteed non-lossy alternative to mcpl_add_particle(fo,particle)
      //would be mcpl_transfer_last_read_particle(fi,fo) which can work directly on
      //the serialised on-disk particle data.
    }
  }

  //Close up files:
  mcpl_closeandgzip_outfile(fo);
  mcpl_close_file(fi);
  return 0;
}

