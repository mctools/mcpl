---
title: Using MCPL from C or C++
underconstruction: true
navtitle: C/C++
---

This page has yet to be completed. For now refer to the almost complete
information in: {% include linkpaper.html subsection=2.2 %}.


{% if false %}

bla mcpl.h, mcpl.c

## Reading MCPL files with custom C or C++ code

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

## Creating MCPL files with custom C or C++ code

```c
#include "mcpl.h"
#include <stdlib.h>

void example()
{
  mcpl_outfile_t f = mcpl_create_outfile("myfile.mcpl");
  mcpl_hdr_set_srcname(f,"MyAppName-1.0");

  /* Tune file options or add custom comments or
     binary data into the header:

     mcpl_enable_universal_pdgcode(f,myglobalpdgcode);
     mcpl_enable_userflags(f);
     mcpl_enable_polarisation(f);
     mcpl_enable_doubleprec(f);
     mcpl_hdr_add_comment(f,"Some comment.");
     mcpl_hdr_add_data(f,"mydatakey",
                       my_datalength, my_databuf)
  */


  mcpl_particle_t * p;
  p = (mcpl_particle_t*)calloc(sizeof(mcpl_particle_t),1);

  int i;
  for ( i = 0; i < 1000; ++i ) {

    /* The following particle properties must
       always be set here:

       p->position[k] (k=0,1,2)
       p->direction[k] (k=0,1,2)
       p->ekin
       p->time
       p->weight

       These should also be set when required by
       file options:

       p->pdgcode
       p->userflags
       p->polarisation[k] (k=0,1,2)
    */

    mcpl_add_particle(f,p);
  }

  mcpl_close_outfile(f);
  free(p);
}
```
{% endif %}
