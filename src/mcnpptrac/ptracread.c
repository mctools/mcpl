
/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
//  ptracread : Code for reading PTRAC files from MCNP(X)                          //
//                                                                                 //
//                                                                                 //
//  Compilation of ptracread.c can proceed via any compliant C-compiler using      //
//  -std=c99 or later, and the resulting code must always be linked with libm      //
//  (using -lm). Furthermore, the following preprocessor flags can be used         //
//  when compiling ptracread.c to fine tune the build process and the              //
//  capabilities of the resulting binary.                                          //
//                                                                                 //
//  SSWREAD_HDR_INCPATH : Specify alternative value if the ptracread header itself //
//                        is not to be included as "ptracread.h".                  //
//                                                                                 //
// Written 2021, osiris.abbate@ib.edu.ar (Instituto Balseiro).                     //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

#ifdef SSWREAD_HDR_INCPATH
#  include SSWREAD_HDR_INCPATH
#else
#  include "ptracread.h"
#endif

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdint.h>


//Should be large enough to hold first record in all supported files:
#define PTRACREAD_MAXLINESIZE 1024

void ptrac_error(const char * msg) {
  printf("ERROR: %s\n",msg);
  exit(1);
}

typedef struct {
  FILE * file;
  ptrac_particle_t part;
  char line[PTRACREAD_MAXLINESIZE];//for holding line from file

  int rawtype;//global raw particle type encoding
  long pdgcode;//global rawtype converted to PDG codes.
} ptrac_fileinternal_t;

long ptrac_get_pdgcode(ptrac_file_t * ff){
  ptrac_fileinternal_t * f = (ptrac_fileinternal_t *)ff->internal;
  assert(f);

  return f->pdgcode;
}

ptrac_file_t ptrac_open_internal( const char * filename )
{
  ptrac_fileinternal_t * f = (ptrac_fileinternal_t*)calloc(sizeof(ptrac_fileinternal_t),1);
  assert(f);

  ptrac_file_t out;
  out.internal = f;

  f->file = fopen(filename,"rb");
  if (!f->file)
    ptrac_error("Unable to open file!");

  // Procesar header
  if(!fgets(f->line, PTRACREAD_MAXLINESIZE, f->file)) // -1
    ptrac_error("Unexpected format in PTRAC file");
  int minus_one;
  sscanf(f->line, "%d", &minus_one);
  if(minus_one != -1)
    ptrac_error("Unexpected format in PTRAC file");
  if(!fgets(f->line, PTRACREAD_MAXLINESIZE, f->file)) // KOD, VER, LODDAT, IDTM
    ptrac_error("Unexpected format in PTRAC file");
  if(!fgets(f->line, PTRACREAD_MAXLINESIZE, f->file)) // AID
    ptrac_error("Unexpected format in PTRAC file");
  double m, n, V; // Process input of PTRAC card
  int i, j, ret;
  ret=fscanf(f->file, "%lf", &m); // Number of keywords
  for(i=0; i<m; i++){ // Loop over keywords
    ret=fscanf(f->file, "%lf", &n);
    for(j=0; j<n; j++)
      ret=fscanf(f->file, "%lf", &V);
    if( i == 10 ){ // TYPE keyword
      if((int)n!=1 || (int)V < 1)
        ptrac_error("TYPE keyword must be set to only one particle");
      f->rawtype = (int)V;
      f->pdgcode = conv_mcnp2pdg(f->rawtype);
    }
    if( i == 12 ) // WRITE keyword
      if((int)n!=1 || (int)V != 2)
        ptrac_error("WRITE keyword must be ALL");
  }
  if(!fgets(f->line, PTRACREAD_MAXLINESIZE, f->file)) // End input line
    ptrac_error("Unexpected format in PTRAC file");

  const char * bn = strrchr(filename, '/');
  bn = bn ? bn + 1 : filename;
  printf("ptrac_open_file: Opened file \"%s\":\n",bn);

  return out;
}

ptrac_file_t ptrac_open_file( const char * filename )
{
  if (!filename)
    ptrac_error("ptrac_open_file called with null string for filename");

  //Open file and initialize internal:
  ptrac_file_t out = ptrac_open_internal( filename );
  ptrac_fileinternal_t * f = (ptrac_fileinternal_t *)out.internal; assert(f);

  //Return handle:
  out.internal = f;
  return out;
}

int ptrac_read(const char* line, ptrac_particle_t* part){
  double aux;
  ptrac_particle_t buf;
  int nreaded = sscanf(line, "%le %le %le %le %le %le %le %le %le %le",
    &buf.x, &buf.y, &buf.z, &buf.dirx, &buf.diry, &buf.dirz, &buf.ekin, &buf.weight, &buf.time, &aux);
  if (nreaded == 9){
    *part = buf;
    return 1;
  }
  return 0;
}

const ptrac_particle_t * ptrac_load_particle(ptrac_file_t ff){
  ptrac_fileinternal_t * f = (ptrac_fileinternal_t *)ff.internal;
  assert(f);

  double ndir, ndir2;
  while(fgets(f->line, PTRACREAD_MAXLINESIZE, f->file)){
    if(ptrac_read(f->line, &f->part)){
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

void ptrac_close_file(ptrac_file_t ff){
  ptrac_fileinternal_t * f = (ptrac_fileinternal_t *)ff.internal;
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

// Revisar mcnp code

static int mcnp_codes[] = {0, 2112, 22, 11, 13, -2112, 12, 14, -11, 2212};//...

int32_t conv_mcnp2pdg(int32_t c)
{
  if( c<0 || c>9 )
    return 0;
  return mcnp_codes[c];
}

int32_t conv_pdg2mcnp(int32_t c)
{
  int i;
  for(i=0; i<sizeof(mcnp_codes)/sizeof(mcnp_codes[0]); i++)
    if(mcnp_codes[i] == c)
      return i;
  return 0;
}
