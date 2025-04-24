---
title: Using MCPL from C or C++
navtitle: C/C++
weight: 10
underconstruction: false
---

- two magic lines for toc
{:toc}

It is possible for advanced users to interact directly with MCPL files from C or
C++ code, by including the header file {% include linkfile.html file="mccp_core/include/mcpl.h" linkname="mcpl.h" %} and making sure the resulting library or application
is linked with the code in the {% include linkfile.html file="mcpl_core/src/mcpl.c" %} file. This is described in more detail in {% include linkpaper.html subsection=2.2
%} and the API is documented in detail in {% include linkpaper.html section=9 linkname="the MCPL paper (appendix C)"
%}.

However, notice that most end-users should not have to write such code. Rather,
they should be able to use pre-existing converters or plugins for their Monte
Carlo applications (c.f. [hooks](LOCAL:hooks/)).

## Code examples for C or C++ code

For inspiration, please find here a few code examples dealing with MCPL files. Note that units on the fields  of the  `mcpl_particle_t` struct are MeV (ekin), cm (position) and milliseconds (time). The particle type is given by the pdgcode field, which must follow the [PDG code standard](http://pdg.lbl.gov/2014/reviews/rpp2014-rev-monte-carlo-numbering.pdf) (2112=neutron, 22=gamma, etc.).

Also note that the code below should normally be compiled and linked with appropriate flags, in order to include the mcpl.h header and link against the MCPL library. One simple way to do that in CMake based projects are (assuming MCPL was installed via CMake and your example programme is in a file called `mymcplapp.c`), to use a small CMakeLists.txt file (in the same dir):

```c
 cmake_minimum_required(VERSION 3.16...3.31)
 project(MyExampleProject LANGUAGES C)
 if( NOT DEFINED "MCPL_DIR" )
   execute_process(
     COMMAND mcpl-config --show cmakedir
     OUTPUT_VARIABLE "MCPL_DIR" OUTPUT_STRIP_TRAILING_WHITESPACE
   )
 endif()
 find_package(MCPL 2.0.0 REQUIRED)
 add_executable(mymcplapp "${PROJECT_SOURCE_DIR}/mymcplapp.c")
 target_link_libraries( mymcplapp MCPL::MCPL )
 install( TARGETS mymcplapp RUNTIME DESTINATION bin )
```

The call to `execute_process(..)` above is only needed in order to be able to work with MCPL installed from Python wheels (e.g. after a `pip install mcpl`).

### Reading MCPL files

```c
#include "mcpl.h"
void example()
{
  mcpl_file_t f = mcpl_open_file("myfile.mcpl");
  const mcpl_particle_t* p;
  while ( ( p = mcpl_read(f) ) ) {
    /* Particle properties can here be accessed
       through the pointer "p":
       p->pdgcode
       p->position[k] (k=0,1,2)
       p->direction[k] (k=0,1,2)
       p->polarisation[k] (k=0,1,2)
       p->ekin
       p->time
       p->weight
       p->userflags
    */
  }
  mcpl_close_file(f);
}
```

### Creating MCPL files

```c
#include "mcpl.h"
void example()
{
  mcpl_outfile_t f = mcpl_create_outfile("myfile.mcpl");
  mcpl_hdr_set_srcname(f,"MyAppName-1.0");

  /* Tune file options or add custom comments or
     binary data into the header:

     mcpl_enable_userflags(f);
     mcpl_enable_polarisation(f);
     mcpl_enable_doubleprec(f);
     mcpl_enable_universal_pdgcode(f,myglobalpdgcode);
     mcpl_enable_universal_weight(f,myglobalweight);
     mcpl_hdr_add_comment(f,"Some comment.");
     mcpl_hdr_add_data(f,"mydatakey",
                       my_datalength, my_databuf)
  */

  mcpl_particle_t * p = mcpl_get_empty_particle(f);

  int i;
  for ( i = 0; i < 1000; ++i ) {

    /* The following particle properties must
       always be set here:

       p->position[k] (k=0,1,2)
       p->direction[k] (k=0,1,2)
       p->ekin
       p->time

       These should also be set when required by
       file options:

       p->pdgcode
       p->weight
       p->userflags
       p->polarisation[k] (k=0,1,2)
    */

    mcpl_add_particle(f,p);
  }

  mcpl_close_outfile(f);
}
```

### Extracting subset of particles from file

The example below shows a small C-programme which can be used to extract just
neutrons ([pdgcode](http://pdg.lbl.gov/2014/reviews/rpp2014-rev-monte-carlo-numbering.pdf) 2112) with EKin<0.1MeV from an existing MCPL file into a new one:

```c

#include "mcpl.h"
#include <stdio.h>

int main(int argc,char**argv) {

  if (argc!=3) {
    printf("Please supply input and output filenames\n");
    return 1;
  }

  const char * infilename = argv[1];
  const char * outfilename = argv[2];

  // Initialisation, open existing file and create output file
  // handle. Transfer all meta-data from existing file, and add
  // an extra comment in the output file to document the process:

  mcpl_file_t fi = mcpl_open_file(infilename);
  mcpl_outfile_t fo = mcpl_create_outfile(outfilename);
  mcpl_transfer_metadata(fi, fo);
  mcpl_hdr_add_comment( fo,
                        "Applied custom filter to select"
                        " neutrons with ekin<0.1MeV" );

  //Loop over particles from input, only triggering mcpl_add_particle
  //calls for the chosen particles:

  const mcpl_particle_t* particle;
  while ( ( particle = mcpl_read(fi) ) ) {
    if ( particle->pdgcode == 2112 && particle->ekin < 0.1 ) {
      mcpl_add_particle(fo,particle);
      //Note that a guaranteed non-lossy alternative to
      //mcpl_add_particle(fo,particle) would be
      //mcpl_transfer_last_read_particle(fi,fo) which can
      //work directly on the serialised on-disk particle data.
    }

  }

  //Close up files:
  mcpl_close_outfile(fo);
  mcpl_close_file(fi);
}
```

### Example project with C code and CMake configuration

The `mcpl` repository contains two small but complete examples of how to make a CMake-based project using the MCPL C API. Please find the example in the [examples/downstream_cmake]({{"/tree/path_to_mcpl2/examples/downstream_cmake" | prepend: site.github.repository_url }}) folder.
