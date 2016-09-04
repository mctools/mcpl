
///////////////////////////////////////////////////////////////////////////////////
//                                                                               //
// A small standalone example of how to one might extract a subset of particles  //
// from an existing MCPL file in order to create a new smaller file.             //
//                                                                               //
// This file can be freely used as per the terms in the LICENSE file.            //
//                                                                               //
// Written 2015-2016 by Thomas.Kittelmann@esss.se                                //
//                                                                               //
///////////////////////////////////////////////////////////////////////////////////

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
  mcpl_hdr_add_comment(fo,"Applied custom filter to select neutrons with ekin<100keV");

  //Loop over particles from input, only triggering mcpl_add_particle calls for
  //the chosen particles:

  const mcpl_particle_t* particle;
  while ( ( particle = mcpl_read(fi) ) ) {
    if ( particle->pdgcode == 2112 && particle->ekin < 0.1 )
      mcpl_add_particle(fo,particle);
  }

  //Close up files:
  mcpl_closeandgzip_outfile(fo);
  mcpl_close_file(fi);
}

