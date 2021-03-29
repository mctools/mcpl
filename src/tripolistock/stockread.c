
/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
//  stockread : Code for reading stock files from TRIPOLI-4 (STORAGE).             //
//                                                                                 //
//                                                                                 //
//  Compilation of stockread.c can proceed via any compliant C-compiler using      //
//  -std=c99 or later, and the resulting code must always be linked with libm      //
//  (using -lm). Furthermore, the following preprocessor flags can be used         //
//  when compiling stockread.c to fine tune the build process and the              //
//  capabilities of the resulting binary.                                          //
//                                                                                 //
//  SSWREAD_HDR_INCPATH : Specify alternative value if the stockread header itself //
//                        is not to be included as "stockread.h".                  //
//                                                                                 //
// Written 2021, osiris.abbate@ib.edu.ar (Instituto Balseiro).                     //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

#ifdef SSWREAD_HDR_INCPATH
#  include SSWREAD_HDR_INCPATH
#else
#  include "stockread.h"
#endif

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdint.h>


//Should be large enough to hold first record in all supported files:
#define STOCKREAD_MAXLINESIZE 1024

void stock_error(const char * msg) {
  printf("ERROR: %s\n",msg);
  exit(1);
}

typedef struct {
  FILE * file;
  stock_particle_t part;
  char line[STOCKREAD_MAXLINESIZE];//for holding line from file
} stock_fileinternal_t;

stock_file_t stock_open_internal( const char * filename )
{
  stock_fileinternal_t * f = (stock_fileinternal_t*)calloc(sizeof(stock_fileinternal_t),1);
  assert(f);

  stock_file_t out;
  out.internal = f;

  f->file = fopen(filename,"rb");
  if (!f->file)
    stock_error("Unable to open file!");

  // Aqui deberia procesar header
  if(!fgets(f->line, STOCKREAD_MAXLINESIZE, f->file))
    stock_error("Unexpected format in stock file");
  if(strncmp(f->line, "Storage", 7))
    stock_error("Unexpected format in stock file");

  const char * bn = strrchr(filename, '/');
  bn = bn ? bn + 1 : filename;
  printf("stock_open_file: Opened file \"%s\":\n",bn);

  return out;
}

stock_file_t stock_open_file( const char * filename )
{
  if (!filename)
    stock_error("stock_open_file called with null string for filename");

  //Open file and initialize internal:
  stock_file_t out = stock_open_internal( filename );
  stock_fileinternal_t * f = (stock_fileinternal_t *)out.internal; assert(f);

  //Return handle:
  out.internal = f;
  return out;
}

int stock_read(const char* line, stock_particle_t* part){
  if(strncmp(line,"NEUTRON",7)==0){
    part->rawtype = 1;
    part->pdgcode = conv_tripoli2pdg(part->rawtype);
    sscanf(line,"NEUTRON %lf %lf %lf %lf %lf %lf %lf %lf",
      &part->ekin, &part->x, &part->y, &part->z, &part->dirx, &part->diry, &part->dirz, &part->weight);
    return 1;
  }
  if(strncmp(line,"PHOTON",6)==0){
    part->rawtype = 2;
    part->pdgcode = conv_tripoli2pdg(part->rawtype);
    sscanf(line,"PHOTON %lf %lf %lf %lf %lf %lf %lf %lf",
      &part->ekin, &part->x, &part->y, &part->z, &part->dirx, &part->diry, &part->dirz, &part->weight);
    return 1;
  }
  return 0;
}

const stock_particle_t * stock_load_particle(stock_file_t ff){
  stock_fileinternal_t * f = (stock_fileinternal_t *)ff.internal;
  assert(f);

  double ndir, ndir2;
  while(fgets(f->line, STOCKREAD_MAXLINESIZE, f->file)){
    if(stock_read(f->line, &f->part)){
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

void stock_close_file(stock_file_t ff){
  stock_fileinternal_t * f = (stock_fileinternal_t *)ff.internal;
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

static int tripoli_codes[] = {0, 2112, 22, 11, -11};

int32_t conv_tripoli2pdg(int32_t c)
{
  if( c<0 || c>4 )
    return 0;
  return tripoli_codes[c];
}

int32_t conv_pdg2tripoli(int32_t c)
{
  int i;
  for(i=0; i<sizeof(tripoli_codes)/sizeof(tripoli_codes[0]); i++)
    if(tripoli_codes[i] == c)
      return i;
  return 0;
}
