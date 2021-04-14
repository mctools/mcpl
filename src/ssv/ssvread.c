
/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
//  ssvread : Code for reading ASCII SSV files (space sep. values).                //
//                                                                                 //
//                                                                                 //
//  Compilation of ssvread.c can proceed via any compliant C-compiler using        //
//  -std=c99 or later, and the resulting code must always be linked with libm      //
//  (using -lm). Furthermore, the following preprocessor flags can be used         //
//  when compiling ssvread.c to fine tune the build process and the                //
//  capabilities of the resulting binary.                                          //
//                                                                                 //
//  SSVREAD_HDR_INCPATH : Specify alternative value if the ssvread header itself   //
//                        is not to be included as "ssvread.h".                    //
//                                                                                 //
// Written 2021, osiris.abbate@ib.edu.ar (Instituto Balseiro).                     //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

#ifdef SSVREAD_HDR_INCPATH
#  include SSVREAD_HDR_INCPATH
#else
#  include "ssvread.h"
#endif

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdint.h>


//Should be large enough to hold first record in all supported files:
#define SSVREAD_MAXLINESIZE 1024

void ssv_error(const char * msg) {
  printf("ERROR: %s\n",msg);
  exit(1);
}

typedef struct {
  FILE * file;
  int ncomments;
  char** comments;
  ssv_particle_t part;
  char line[SSVREAD_MAXLINESIZE];//for holding line from file
} ssv_fileinternal_t;

int ssv_get_ncomment(ssv_file_t * ff){
  ssv_fileinternal_t * f = (ssv_fileinternal_t *)ff->internal;
  assert(f);

  return f->ncomments;
}

char* ssv_get_comment(ssv_file_t * ff, int i){
  ssv_fileinternal_t * f = (ssv_fileinternal_t *)ff->internal;
  assert(f);

  if(i < f->ncomments) return f->comments[i];
  return NULL;
}

ssv_file_t ssv_open_internal( const char * filename )
{
  ssv_fileinternal_t * f = (ssv_fileinternal_t*)calloc(sizeof(ssv_fileinternal_t),1);
  assert(f);

  ssv_file_t out;
  out.internal = f;

  f->file = fopen(filename,"r");
  if (!f->file)
    ssv_error("Unable to open file!");

  // Procesar header
  f->ncomments = 0;
  f->comments = NULL;
  if(!fgets(f->line, SSVREAD_MAXLINESIZE, f->file)) ssv_error("Unexpected format in SSV file"); // SSV
  if(strcmp(f->line, "#MCPL-ASCII\n") != 0) ssv_error("Unexpected format in SSV file");
  if(!fgets(f->line, SSVREAD_MAXLINESIZE, f->file)) ssv_error("Unexpected format in SSV file"); // ASCII-FORMAT: v1
  if(!fgets(f->line, SSVREAD_MAXLINESIZE, f->file)) ssv_error("Unexpected format in SSV file"); // NPARTICLES
  if(!fgets(f->line, SSVREAD_MAXLINESIZE, f->file)) ssv_error("Unexpected format in SSV file"); // END-HEADER / NCOMMENTS
  if(strcmp(f->line, "#END-HEADER\n") != 0)
    sscanf(f->line, "#NCOMMENTS: %d", &f->ncomments);
  if(f->ncomments){
    f->comments = (char**)malloc(f->ncomments*sizeof(char*));
    int i;
    for(i=0; i<f->ncomments; i++){
      f->comments[i] = (char*)malloc(SSVREAD_MAXLINESIZE*sizeof(char*));
      if(!fgets(f->comments[i], SSVREAD_MAXLINESIZE, f->file)) ssv_error("Unexpected format in SSV file"); // COMMENT[i]
      f->comments[i][strcspn(f->comments[i], "\n")] = 0;
    }
    if(!fgets(f->line, SSVREAD_MAXLINESIZE, f->file)) ssv_error("Unexpected format in SSV file"); // END-HEADER
  }
  if(!fgets(f->line, SSVREAD_MAXLINESIZE, f->file)) ssv_error("Unexpected format in SSV file"); // Variable names

  const char * bn = strrchr(filename, '/');
  bn = bn ? bn + 1 : filename;
  printf("ssv_open_file: Opened file \"%s\":\n",bn);

  return out;
}

ssv_file_t ssv_open_file( const char * filename )
{
  if (!filename)
    ssv_error("ssv_open_file called with null string for filename");

  //Open file and initialize internal:
  ssv_file_t out = ssv_open_internal( filename );
  ssv_fileinternal_t * f = (ssv_fileinternal_t *)out.internal; assert(f);

  //Return handle:
  out.internal = f;
  return out;
}

int ssv_read(const char* line, ssv_particle_t* part){
  double aux;
  int idx, uf;
  ssv_particle_t p;
  int nreaded = sscanf(line, "%i %li %g %g %g %g %g %g %g %g %g %g %g %g %x\n",
    &idx,&p.pdgcode,&p.ekin,&p.x,&p.y,&p.z,&p.dirx,&p.diry,&p.dirz,&p.time,&p.weight,&p.polx,&p.poly,&p.polz,&p.uf);
  if (nreaded == 15){
    *part = p;
    return 1;
  }
  return 0;
}

const ssv_particle_t * ssv_load_particle(ssv_file_t ff){
  ssv_fileinternal_t * f = (ssv_fileinternal_t *)ff.internal;
  assert(f);

  double ndir, ndir2;
  while(fgets(f->line, SSVREAD_MAXLINESIZE, f->file)){
    if(ssv_read(f->line, &f->part)){
      ndir2 = f->part.dirx*f->part.dirx + f->part.diry*f->part.diry + f->part.dirz*f->part.dirz;
      if(ndir2 != 1){ // Normalization may be inexact in this format
        ndir = sqrt(ndir2);
        f->part.dirx /= ndir;
        f->part.diry /= ndir;
        f->part.dirz /= ndir;
      }
      return &f->part;
    }
  }
  return 0;
}

void ssv_close_file(ssv_file_t ff){
  ssv_fileinternal_t * f = (ssv_fileinternal_t *)ff.internal;
  assert(f);

  if (!f)
    return;
  if (f->file) {
    fclose(f->file);
    f->file = 0;
  }
  free(f);
  ff.internal = 0;
}
