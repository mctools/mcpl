
///////////////////////////////////////////////////////////////////////////////////
//                                                                               //
// A small standalone example of how to one might output an MCPL file from a     //
// given programme.                                                              //
//                                                                               //
// This file can be freely used as per the terms in the LICENSE file.            //
//                                                                               //
// Written 2015-2016 by Thomas.Kittelmann@ess.eu                                 //
//                                                                               //
///////////////////////////////////////////////////////////////////////////////////


#include "mcpl.h"
#include <stdio.h>
#include <stdlib.h>
#include <memory.h>


double randuniform(double a, double b)
{
  return a + rand() * (b-a) / RAND_MAX;
}

int main(int argc,char**argv) {

  if (argc!=2) {
    printf("Please supply output filename\n");
    return 1;
  }

  const char * filename = argv[1];

  // Initialisation, create output file handle, embed name of source application
  // in the header and declare that this is a neutron-only file. Note that an
  // ".mcpl" extension will be added to the filename if it doesn't have it
  // already:

  mcpl_outfile_t f = mcpl_create_outfile(filename);
  mcpl_hdr_set_srcname(f,"my_cool_program_name");

  // By default, floating point numbers will be stored in single precision and
  // neither polarisation nor user-flags will be stored in the file. These
  // defaults can be modified by one or more of the following calls (perhaps
  // they could be options to your McStas component):
  //
  //    mcpl_enable_userflags(f);
  //    mcpl_enable_polarisation(f);
  //    mcpl_enable_doubleprec(f);

  // If all particles will be of the same type, optimise the file a bit by:
  //
  //    mcpl_enable_universal_pdgcode(f,2112);//all particles are neutrons

  //We can add comments (strings) to the header. It is always a good idea to add
  //comments explaining things like coordinate system, contents of user-flags
  //(if any), and what the values in the "weight" field means exactly.:
  mcpl_hdr_add_comment(f,"Some comment.");
  mcpl_hdr_add_comment(f,"Another comment.");

  //It is also possible to add binary data with mcpl_hdr_add_data, if desired
  //(can be indexed by strings). So for instance, custom persistified
  //configuration meta-data could be added (or perhaps just a text file used by
  //configuration by your programme, if appropriate).

  //Allocate the particle structure we will use during the simulation loop
  //to register particle data in the output file:
  mcpl_particle_t * particle = mcpl_get_empty_particle(f);

  //Simulation loop, modify the particle struct and add to the file as many
  //times as needed (here everything will simply be filled with some stupid
  //random numbers):
  int i;
  for (i = 0; i < 1000; ++i) {
    //particle type:
    if (rand()%2)
      particle->pdgcode = 2112;//50% neutrons
    else
      particle->pdgcode = 22;//50% gammas
    //position in centimeters:
    particle->position[0] = randuniform(-100,100);
    particle->position[1] = randuniform(-100,100);
    particle->position[2] = randuniform(-100,100);
    //kinetic energy in MeV:
    particle->ekin = randuniform(0.001,10);
    //momentum direction (unit vector):
    particle->direction[0] = 0.0;
    particle->direction[1] = 0;
    particle->direction[2] = 1.0;
    //time in milliseconds:
    particle->time = randuniform(0,100);
    //weight in unspecified units:
    particle->weight = randuniform(0.01,10);
    //modify userflags and polarisation (what units?) as well, if enabled.

    //Finally, add the particle to the file:
    mcpl_add_particle(f,particle);
  }

  //At the end, remember to properly close the output file (and cleanup mem if desired):
  mcpl_closeandgzip_outfile(f);

  //Note: By calling mcpl_closeandgzip_outfile rather than mcpl_close_outfile,
  //the output file will (in most cases) end up being gzipped, resulting in a
  //smaller file. Such files can be read directly if mcpl is compiled with zlib
  //support (if not, users will have to gunzip it before using it).
}

