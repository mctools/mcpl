
/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
//  Monte Carlo Particle Lists : MCPL                                              //
//                                                                                 //
//  Utilities for reading and writing .mcpl files: A binary format with lists of   //
//  particle state information, for interchanging and reshooting events between    //
//  various Monte Carlo simulation applications.                                   //
//                                                                                 //
//  Client code including mcpl.h does not need any special build flags and can     //
//  be compiled with any complient compiler and any current C or C++ standard.     //
//                                                                                 //
//  Compilation of mcpl.c on the other hand is currently not supported for C89,    //
//  although this could be revisited. Thus, compilation of mcpl.c can proceed      //
//  using any complient C-compiler using -std=c99 or -std=c11 or any complient     //
//  C++ compiler using any version of the C++ standard, and the resulting code     //
//  must always be linked with libm (using -lm). Furthermore, the following        //
//  preprocessor flags can be used when compiling mcpl.c to fine tune the build    //
//  process and the capabilities of the resulting binary.                          //
//                                                                                 //
//  MCPL_HASZLIB        : Define if compiling and linking with zlib, to allow      //
//                        direct reading of .mcpl.gz files.                        //
//  MCPL_ZLIB_INCPATH   : Specify alternative value if the zlib header is not to   //
//                        be included as "zlib.h".                                 //
//  MCPL_HEADER_INCPATH : Specify alternative value if the MCPL header itself is   //
//                        not to be included as "mcpl.h".                          //
//  MCPL_NO_EXT_GZIP    : Define to make sure that mcpl_gzip_file will never       //
//                        compress via a separate process running a system-        //
//                        provided gzip executable.                                //
//  MCPL_NO_CUSTOM_GZIP : Define to make sure that mcpl_gzip_file will never       //
//                        compress via custom zlib-based code.                     //
//                                                                                 //
//  This file can be freely used as per the terms in the LICENSE file.             //
//                                                                                 //
//  Find more information and updates at https://mctools.github.io/mcpl/           //
//                                                                                 //
//  Written by Thomas Kittelmann, 2015-2017.                                       //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////


/////////////////////////////////////////////////////////////////////////////////////
//  MCPL_FORMATVERSION history:                                                    //
//                                                                                 //
//  3: Current version. Changed packing of unit vectors from octahedral to         //
//     the better performing "Adaptive Projection Packing".                        //
//  2: First public release.                                                       //
//  1: Format used during early development. No longer supported.                  //
/////////////////////////////////////////////////////////////////////////////////////

//Rough platform detection (could be much more fine-grained):
#if defined(__unix__) || defined(__unix) || (defined(__APPLE__) && defined(__MACH__))
#  define MCPL_THIS_IS_UNIX
#endif
#if defined(MSDOS) || defined(OS2) || defined(WIN32) || defined(_WIN32) || defined(__CYGWIN__)
#  ifdef MCPL_THIS_IS_UNIX
#    undef MCPL_THIS_IS_UNIX
#  endif
#  define MCPL_THIS_IS_MS
#endif

//Before including mcpl.h, we attempt to get PRIu64 defined in a relatively
//robust manner by enabling feature test macros for gcc and including relevant
//headers:
#ifndef __STDC_FORMAT_MACROS
#  define __STDC_FORMAT_MACROS
#endif
#ifndef _POSIX_C_SOURCE
#  define _POSIX_C_SOURCE 1
#endif
#include <inttypes.h>
#include <stdio.h>
#ifndef PRIu64//bad compiler - fallback to guessing
#  if defined(_MSC_VER) && (_MSC_VER<1900)
#    define PRIu64 "I64u"
#  else
#    if defined(__WORDSIZE) && (__WORDSIZE==64)
#      define PRIu64 "lu"
#    else
#      define PRIu64 "llu"
#    endif
#  endif
#endif

#ifdef MCPL_HEADER_INCPATH
#  include MCPL_HEADER_INCPATH
#else
#  include "mcpl.h"
#endif

#ifdef MCPL_HASZLIB
#  ifdef MCPL_ZLIB_INCPATH
#    include MCPL_ZLIB_INCPATH
#  else
#    include "zlib.h"
#  endif
#endif

#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>
#include <unistd.h>
#include <limits.h>
#ifdef MCPL_THIS_IS_MS
#  include <fcntl.h>
#  include <io.h>
#endif

#define MCPLIMP_NPARTICLES_POS 8
#define MCPLIMP_MAX_PARTICLE_SIZE 96

int mcpl_platform_is_little_endian() {
  // return 0 for big endian, 1 for little endian.
  volatile uint32_t i=0x01234567;
  return (*((uint8_t*)(&i))) == 0x67;
}

void mcpl_default_error_handler(const char * msg) {
  printf("MCPL ERROR: %s\n",msg);
  exit(1);
}

static void (*mcpl_error_handler)(const char *) = &mcpl_default_error_handler;

void mcpl_error(const char * msg) {
  mcpl_error_handler(msg);
  //Error handler should not return, but in case it does anyway, we at least
  //ensure a hard exit!
  mcpl_default_error_handler("Handler given to mcpl_set_error_handler returns"
                             " to calling code which is not allowed!");
}

void mcpl_set_error_handler(void (*handler)(const char *))
{
  mcpl_error_handler = handler;
}

void mcpl_store_string(char** dest, const char * src)
{
  size_t n = strlen(src);
  if (n>65535) n = 65535;
  if (*dest)
    free(*dest);
  *dest = (char*)calloc(n+1,1);
  assert(*dest);
  strncpy( *dest,src,n );
  (*dest)[n] = '\0';
  return;
}

void mcpl_write_buffer(FILE* f, uint32_t n, const char * data, const char * errmsg)
{
  size_t nb = fwrite(&n, 1, sizeof(n), f);
  if (nb!=sizeof(n))
    mcpl_error(errmsg);
  nb = fwrite(data, 1, n, f);
  if (nb!=n)
    mcpl_error(errmsg);
}
void mcpl_write_string(FILE* f, const char * str, const char * errmsg)
{
  size_t n = strlen(str);
  mcpl_write_buffer(f,n,str,errmsg);//nb: we don't write the terminating null-char
}

typedef struct {
  char * filename;
  FILE * file;
  char * hdr_srcprogname;
  uint32_t ncomments;
  char ** comments;
  uint32_t nblobs;
  char ** blobkeys;
  uint32_t * bloblengths;
  char ** blobs;
  int opt_userflags;
  int opt_polarisation;
  int opt_singleprec;
  int32_t opt_universalpdgcode;
  double opt_universalweight;
  int header_notwritten;
  uint64_t nparticles;
  unsigned particle_size;
  mcpl_particle_t* puser;
  unsigned opt_signature;
  char particle_buffer[MCPLIMP_MAX_PARTICLE_SIZE];
} mcpl_outfileinternal_t;

#define MCPLIMP_OUTFILEDECODE mcpl_outfileinternal_t * f = (mcpl_outfileinternal_t *)of.internal; assert(f)

void mcpl_recalc_psize(mcpl_outfile_t of)
{
  MCPLIMP_OUTFILEDECODE;
  unsigned fp = f->opt_singleprec ? sizeof(float) : sizeof(double);
  f->particle_size = 7*fp;
  if (f->opt_polarisation)
    f->particle_size += 3*fp;
  if (!f->opt_universalpdgcode)
    f->particle_size += sizeof(int32_t);
  if (!f->opt_universalweight)
    f->particle_size += fp;
  if (f->opt_userflags)
    f->particle_size += sizeof(uint32_t);
  assert(f->particle_size<=MCPLIMP_MAX_PARTICLE_SIZE);
  f->opt_signature = 0
    + 1 * f->opt_singleprec
    + 2 * f->opt_polarisation
    + 4 * f->opt_universalpdgcode
    + 8 * (f->opt_universalweight?1:0)
    + 16 * f->opt_userflags;
}

void mcpl_platform_compatibility_check() {
  static int first = 1;
  if (!first)
    return;
  first = 0;

  if (CHAR_BIT!=8)
    mcpl_error("Platform compatibility check failed (bytes are not 8 bit)");

  if (sizeof(float)!=4)
    mcpl_error("Platform compatibility check failed (float is not 4 bytes)");

  if (sizeof(double)!=8)
    mcpl_error("Platform compatibility check failed (double is not 8 bytes)");

  int32_t m1_32 = -1;
  int32_t not0_32 = ~0;
  int64_t m1_64 = -1;
  int64_t not0_64 = ~0;
  if ( m1_32 != not0_32 || m1_64 != not0_64 )
    mcpl_error("Platform compatibility check failed (integers are not two's complement)");


  if (copysign(1.0, -0.0) != -1.0)
    mcpl_error("Platform compatibility check failed (floating point numbers do not have signed zero)");

  mcpl_particle_t pd;
  if ( (char*)&(pd.userflags)-(char*)&(pd) != 12*sizeof(double)+sizeof(uint32_t) )
    mcpl_error("Platform compatibility check failed (unexpected padding in mcpl_particle_t)");

}

mcpl_outfile_t mcpl_create_outfile(const char * filename)
{
  //Sanity check chosen filename and append ".mcpl" if missing to help people
  //who forgot to add the extension (in the hope of higher consistency).
  if (!filename)
    mcpl_error("mcpl_create_outfile called with null string.");
  size_t n = strlen(filename);
  if (!n)
    mcpl_error("mcpl_create_outfile called with empty string.");
  if (n>4096)
    mcpl_error("mcpl_create_outfile called with too long string.");
  const char * lastdot = strrchr(filename, '.');
  if (lastdot==filename && n==5)
    mcpl_error("mcpl_create_outfile called with string with no basename part (\".mcpl\").");

  //Initialise data structures and open file:
  mcpl_platform_compatibility_check();

  mcpl_outfile_t out;
  out.internal = 0;

  mcpl_outfileinternal_t * f = (mcpl_outfileinternal_t*)calloc(sizeof(mcpl_outfileinternal_t),1);
  assert(f);

  if (!lastdot || strcmp(lastdot, ".mcpl") != 0) {
    f->filename = (char*)malloc(n+6);
    f->filename[0] = '\0';
    strcat(f->filename,filename);
    strcat(f->filename,".mcpl");
  } else {
    f->filename = (char*)malloc(n+1);
    f->filename[0] = '\0';
    strcat(f->filename,filename);
  }

  f->hdr_srcprogname = 0;
  f->ncomments = 0;
  f->comments = 0;
  f->nblobs = 0;
  f->blobkeys = 0;
  f->bloblengths = 0;
  f->blobs = 0;
  f->opt_userflags = 0;
  f->opt_polarisation = 0;
  f->opt_singleprec = 1;
  f->opt_universalpdgcode = 0;
  f->opt_universalweight = 0.0;
  f->header_notwritten = 1;
  f->nparticles = 0;
  f->file = fopen(f->filename,"wb");
  if (!f->file)
    mcpl_error("Unable to open output file!");

  out.internal = f;
  mcpl_recalc_psize(out);
  return out;
}

const char * mcpl_outfile_filename(mcpl_outfile_t of) {
  MCPLIMP_OUTFILEDECODE;
  return f->filename;
}

void mcpl_hdr_set_srcname(mcpl_outfile_t of,const char * spn)
{
  MCPLIMP_OUTFILEDECODE;
  if (!f->header_notwritten)
    mcpl_error("mcpl_hdr_set_srcname.");
  mcpl_store_string(&(f->hdr_srcprogname),spn);
}

void mcpl_hdr_add_comment(mcpl_outfile_t of,const char *comment)
{
  MCPLIMP_OUTFILEDECODE;
  if (!f->header_notwritten)
    mcpl_error("mcpl_hdr_add_comment called too late.");
  size_t oldn = f->ncomments;
  f->ncomments += 1;
  if (oldn)
    f->comments = (char **)realloc(f->comments,f->ncomments * sizeof(char*) );
  else
    f->comments = (char **)calloc(f->ncomments,sizeof(char*));
  f->comments[oldn] = 0;
  mcpl_store_string(&(f->comments[oldn]),comment);
}

void mcpl_hdr_add_data(mcpl_outfile_t of, const char * key,
                       uint32_t ldata, const char * data)
{
  MCPLIMP_OUTFILEDECODE;
  if (!f->header_notwritten)
    mcpl_error("mcpl_hdr_add_data called too late.");
  size_t oldn = f->nblobs;
  f->nblobs += 1;
  //Check that key is unique
  unsigned i;
  for (i =0; i<oldn; ++i) {
    if (strcmp(f->blobkeys[i],key)==0)
      mcpl_error("mcpl_hdr_add_data got duplicate key");
  }
  //store key:
  if (oldn)
    f->blobkeys = (char **)realloc(f->blobkeys,f->nblobs * sizeof(char*) );
  else
    f->blobkeys = (char **)calloc(f->nblobs,sizeof(char*));
  f->blobkeys[oldn] = 0;
  mcpl_store_string(&(f->blobkeys[oldn]),key);
  //store blob-lengths:
  if (oldn)
    f->bloblengths = (uint32_t*)realloc(f->bloblengths,f->nblobs * sizeof(uint32_t) );
  else
    f->bloblengths = (uint32_t *)calloc(f->nblobs,sizeof(uint32_t));
  f->bloblengths[oldn] = ldata;

  //store data:
  if (oldn)
    f->blobs = (char **)realloc(f->blobs,f->nblobs * sizeof(char*) );
  else
    f->blobs = (char **)calloc(f->nblobs,sizeof(char*));
  f->blobs[oldn] = (char *)malloc(ldata);
  memcpy(f->blobs[oldn],data,ldata);
}

void mcpl_enable_userflags(mcpl_outfile_t of)
{
  MCPLIMP_OUTFILEDECODE;
  if (f->opt_userflags)
    return;
  if (!f->header_notwritten)
    mcpl_error("mcpl_enable_userflags called too late.");
  f->opt_userflags = 1;
  mcpl_recalc_psize(of);
}

void mcpl_enable_polarisation(mcpl_outfile_t of)
{
  MCPLIMP_OUTFILEDECODE;
  if (f->opt_polarisation)
    return;
  if (!f->header_notwritten)
    mcpl_error("mcpl_enable_polarisation called too late.");
  f->opt_polarisation = 1;
  mcpl_recalc_psize(of);
}

void mcpl_enable_doubleprec(mcpl_outfile_t of)
{
  MCPLIMP_OUTFILEDECODE;
  if (!f->opt_singleprec)
    return;
  if (!f->header_notwritten)
    mcpl_error("mcpl_enable_doubleprec called too late.");
  f->opt_singleprec = 0;
  mcpl_recalc_psize(of);
}

void mcpl_enable_universal_pdgcode(mcpl_outfile_t of, int32_t pdgcode)
{
  MCPLIMP_OUTFILEDECODE;
  if (pdgcode==0)
    mcpl_error("mcpl_enable_universal_pdgcode must be called with non-zero pdgcode.");
  if (f->opt_universalpdgcode) {
    if (f->opt_universalpdgcode!=pdgcode)
      mcpl_error("mcpl_enable_universal_pdgcode called multiple times");
    return;
  }
  if (!f->header_notwritten)
    mcpl_error("mcpl_enable_universal_pdgcode called too late.");
  f->opt_universalpdgcode = pdgcode;
  mcpl_recalc_psize(of);
}

void mcpl_enable_universal_weight(mcpl_outfile_t of, double w)
{
  MCPLIMP_OUTFILEDECODE;
  if (w<=0.0||isinf(w)||isnan(w))
    mcpl_error("mcpl_enable_universal_weight must be called with positive but finite weight.");
  if (f->opt_universalweight) {
    if (f->opt_universalweight!=w)
      mcpl_error("mcpl_enable_universal_weight called multiple times");
    return;
  }
  if (!f->header_notwritten)
    mcpl_error("mcpl_enable_universal_weight called too late.");
  f->opt_universalweight = w;
  mcpl_recalc_psize(of);
}

void mcpl_write_header(mcpl_outfile_t of)
{
  MCPLIMP_OUTFILEDECODE;
  if (!f->header_notwritten)
    mcpl_error("Logical error!");

  const char * errmsg="Errors encountered while attempting to write file header.";
  //Always start the file with an unsigned char-array (for endian agnosticity)
  //containing magic word (MCPL), file format version ('001'-'999') and
  //endianness used in the file ('L' or 'B'):
  unsigned char start[8] = {'M','C','P','L','0','0','0','L'};
  start[4] = (MCPL_FORMATVERSION/100)%10 + '0';
  start[5] = (MCPL_FORMATVERSION/10)%10 + '0';
  start[6] = MCPL_FORMATVERSION%10 + '0';
  if (!mcpl_platform_is_little_endian())
    start[7] = 'B';
  size_t nb = fwrite(start, 1, sizeof(start), f->file);
  if (nb!=sizeof(start))
    mcpl_error(errmsg);

  //Right after the initial 8 bytes, we put the number of particles (0 for now,
  //but important that position is fixed so we can seek and update it later).:
  long int nparticles_pos = ftell(f->file);
  if (nparticles_pos!=MCPLIMP_NPARTICLES_POS)
    mcpl_error(errmsg);
  nb = fwrite(&f->nparticles, 1, sizeof(f->nparticles), f->file);
  if (nb!=sizeof(f->nparticles))
    mcpl_error(errmsg);

  //Then a bunch of numbers:
  uint32_t arr[8];
  arr[0] = f->ncomments;
  arr[1] = f->nblobs;
  arr[2] = f->opt_userflags;
  arr[3] = f->opt_polarisation;
  arr[4] = f->opt_singleprec;
  arr[5] = f->opt_universalpdgcode;
  arr[6] = f->particle_size;
  arr[7] = (f->opt_universalweight?1:0);
  assert(sizeof(arr)==32);
  nb = fwrite(arr, 1, sizeof(arr), f->file);
  if (nb!=sizeof(arr))
    mcpl_error(errmsg);

  if (f->opt_universalweight) {
    assert(sizeof(f->opt_universalweight)==8);
    nb = fwrite((void*)(&(f->opt_universalweight)), 1, sizeof(f->opt_universalweight), f->file);
    if (nb!=sizeof(f->opt_universalweight))
      mcpl_error(errmsg);
  }

  //strings:
  mcpl_write_string(f->file,f->hdr_srcprogname?f->hdr_srcprogname:"unknown",errmsg);
  uint32_t i;
  for (i = 0; i < f->ncomments; ++i)
    mcpl_write_string(f->file,f->comments[i],errmsg);

  //blob keys:
  for (i = 0; i < f->nblobs; ++i)
    mcpl_write_string(f->file,f->blobkeys[i],errmsg);

  //blobs:
  for (i = 0; i < f->nblobs; ++i)
    mcpl_write_buffer(f->file, f->bloblengths[i], f->blobs[i],errmsg);

  //Free up acquired memory only needed for header writing:
  free(f->hdr_srcprogname);
  f->hdr_srcprogname = 0;
  if (f->ncomments) {
    for (i = 0; i < f->ncomments; ++i)
      free(f->comments[i]);
    free(f->comments);
    f->comments=0;
    f->ncomments=0;
  }
  if (f->nblobs) {
    for (i = 0; i < f->nblobs; ++i)
      free(f->blobkeys[i]);
    free(f->blobkeys);
    f->blobkeys = 0;
    for (i = 0; i < f->nblobs; ++i)
      free(f->blobs[i]);
    free(f->blobs);
    f->blobs = 0;
    free(f->bloblengths);
    f->bloblengths = 0;
    f->nblobs = 0;
  }
  f->header_notwritten = 0;
}

#ifndef INFINITY
//Missing in ICC 12 C99 compilation:
#  define  INFINITY (__builtin_inf())
#endif

void mcpl_unitvect_pack_adaptproj(const double* in, double* out) {

  //Precise packing of unit vector into 2 floats + 1 bit using the "Adaptive
  //Projection Packing" method (T. Kittelmann, 2017).
  //
  //The Adaptive Projection Packing method is a variant on the traditional projection
  //method where one would store (x,y,sign(z)) and upon unpacking recover the
  //magnitude of z with |z|=sqrt(1-x^2-y^2), a formula which suffers from
  //numerical precision issues when |z| is small. In this improved version, one
  //gets rid of the precision issues by always storing the components that are
  //smallest in magnitude (the last one must then have a magnitude in the
  //interval [1/sqrt(3),1] = [0.577,1.0] which is never small). This just leaves
  //the issue of being able to recognise the coordinate choices again upon
  //unpacking. Since all components are at most of unit magnitude, this is
  //achieved by storing 1/z rather than z and replacing either x or y as
  //needed (infinity when z=0). Thus, the packed data will contain:
  //
  //              ( 1/z,  y, sign(x) ) when |x|>|y|,|z|
  //              ( x,  1/z, sign(y) ) when |y|>|x|,|z|
  //              ( x,    y, sign(z) ) when |z|>|x|,|y|
  //
  //The unpacking code can determine which of the three scenarios is used to
  //encode a given piece of data by checking if the first or second field is
  //greater than unity.
  //
  //Note that the arrays "in" and "out" are both of dimension 3, however out[2]
  //will contain only binary information, in the form of the sign of the
  //component which was projected away (-1.0 or 1.0).
  const double absx = fabs(in[0]);
  const double absy = fabs(in[1]);
  if ( fabs(in[2]) < fmax(absx,absy) ) {
    const double invz = ( in[2] ? (1.0/in[2]) : INFINITY );
    if (absx>=absy) {
      //output (1/z,y,sign(x))
      out[0] = invz; out[1] = in[1]; out[2] = in[0];
    } else {
      //output (x,1/z,sign(y))
      out[0] = in[0]; out[1] = invz; out[2] = in[1];
    }
  } else {
    //output (x,y,sign(z))
    out[0] = in[0]; out[1] = in[1]; out[2] = in[2];
  }
  out[2] = copysign(1.0,out[2]);
}

void mcpl_unitvect_unpack_adaptproj( const double* in, double* out ) {

  //Unpacking for the "Adaptive Projection Packing" method (T. Kittelmann, 2017).
  //See mcpl_unitvect_pack_adaptproj for more information.
  //
  //Note that the arrays "in" and "out" are both of dimension 3, however in[2]
  //will contain only binary information, in the form of the sign of the
  //component which was projected away.

  assert(in[2]==1.0||in[2]==-1.0);
  if (fabs(in[0]) > 1.0) {
    //input is (1/z,y,sign(x))
    out[1] = in[1]; out[2] = 1.0 / in[0];
    out[0] = in[2] * sqrt( fmax( 0.0, 1.0 - ( in[1]*in[1] + out[2]*out[2] ) ) );
  } else if (fabs(in[1])>1.0) {
    //input is (x,1/z,sign(y))
    out[0] = in[0]; out[2] = 1.0 / in[1];
    out[1] = in[2] * sqrt( fmax ( 0.0, 1.0 - ( in[0]*in[0] + out[2]*out[2] ) ) );
  } else {
    //input is (x,y,sign(z))
    out[0] = in[0]; out[1] = in[1];
    out[2] = in[2] * sqrt( fmax( 0.0, 1.0 - ( in[0]*in[0] + in[1]*in[1] ) ) );
  }
}

void mcpl_unitvect_unpack_oct(const double* in, double* out) {

  //Octahedral packing inspired by http://jcgt.org/published/0003/02/01/
  //
  //and:
  //
  //Octahedron Environment Maps, T. Engelhardt & C. Dachsbacher, Conference:
  //Proceedings of the Vision, Modeling, and Visualization Conference 2008, VMV
  //2008, Konstanz, Germany, October 8-10, 2008
  //
  //Note: Octahedral packing was used for the MCPL-2 format, which we are no
  //longer writing, only reading. Thus, we only keep the unpacking function in
  //the code.

  //restore z-coord of octahedron:
  out[2] = 1.0 - fabs(in[0]) - fabs(in[1]);
  if (out[2]<0) {
    //lower hemisphere
    out[0] = ( 1.0 - fabs( in[1] ) ) * ( in[0] >= 0.0 ? 1.0 : -1.0 );
    out[1] = ( 1.0 - fabs( in[0] ) ) * ( in[1] >= 0.0 ? 1.0 : -1.0 );
  } else {
    //upper hemisphere
    out[0] = in[0];
    out[1] = in[1];
  }
  //project from octahedron to unit sphere:
  double n = 1.0 / sqrt(out[0]*out[0]+out[1]*out[1]+out[2]*out[2]);
  out[0] *= n; out[1] *= n; out[2] *= n;
}

void mcpl_add_particle(mcpl_outfile_t of,const mcpl_particle_t* particle)
{
  MCPLIMP_OUTFILEDECODE;
  if (f->header_notwritten)
    mcpl_write_header(of);
  f->nparticles += 1;

  //Sanity check (add more??):
  double dirsq = particle->direction[0] * particle->direction[0]
    + particle->direction[1] * particle->direction[1]
    + particle->direction[2] * particle->direction[2];
  if (fabs(dirsq-1.0)>1.0e-5)
    mcpl_error("attempting to add particle with non-unit direction vector");
  if (particle->ekin<0.0)
    mcpl_error("attempting to add particle with negative kinetic energy");

  //direction and ekin are packed into 3 doubles:
  double pack_ekindir[3];
  mcpl_unitvect_pack_adaptproj(particle->direction,pack_ekindir);
  //pack_ekindir[2] is now just a sign(1.0 or -1.0), so we can store the
  //ekin in that field as well (since it must be non-negative). We use copysign
  //to be sure the signbit is set also if ekin=0:
  pack_ekindir[2] = copysign(particle->ekin,pack_ekindir[2]);

  //serialise particle object to buffer:
  unsigned ibuf = 0;
  char * pbuf = &(f->particle_buffer[0]);
  int i;
  if (f->opt_singleprec) {
    if (f->opt_polarisation) {
      for (i=0;i<3;++i) {
        *(float*)&pbuf[ibuf] = (float)particle->polarisation[i];
        ibuf += sizeof(float);
      }
    }
    for (i=0;i<3;++i) {
      *(float*)&pbuf[ibuf] = (float)particle->position[i];
      ibuf += sizeof(float);
    }
    for (i=0;i<3;++i) {
      *(float*)&pbuf[ibuf] = (float)pack_ekindir[i];
      ibuf += sizeof(float);
    }
    *(float*)&pbuf[ibuf] = (float)particle->time;
    ibuf += sizeof(float);
    if (!f->opt_universalweight) {
      *(float*)&pbuf[ibuf] = (float)particle->weight;
      ibuf += sizeof(float);
    }
  } else {
    if (f->opt_polarisation) {
      for (i=0;i<3;++i) {
        *(double*)&pbuf[ibuf] = particle->polarisation[i];
        ibuf += sizeof(double);
      }
    }
    for (i=0;i<3;++i) {
      *(double*)&pbuf[ibuf] = particle->position[i];
      ibuf += sizeof(double);
    }
    for (i=0;i<3;++i) {
      *(double*)&pbuf[ibuf] = pack_ekindir[i];
      ibuf += sizeof(double);
    }
    *(double*)&pbuf[ibuf] = particle->time;
    ibuf += sizeof(double);
    if (!f->opt_universalweight) {
      *(double*)&pbuf[ibuf] = particle->weight;
      ibuf += sizeof(double);
    }
  }
  if (!f->opt_universalpdgcode) {
    *(int32_t*)&pbuf[ibuf] = particle->pdgcode;
    ibuf += sizeof(int32_t);
  }
  if (f->opt_userflags) {
    *(uint32_t*)&pbuf[ibuf] = particle->userflags;
    ibuf += sizeof(uint32_t);
  }
  assert(ibuf==f->particle_size);

  //Write buffer to file:
  size_t nb;
  nb = fwrite(pbuf, 1, f->particle_size, f->file);
  if (nb!=f->particle_size)
    mcpl_error("Errors encountered while attempting to write particle data.");
}

void mcpl_update_nparticles(FILE* f, uint64_t n)
{
  //Seek and update nparticles at correct location in header:
  const char * errmsg = "Errors encountered while attempting to update number of particles in file.";
  int64_t savedpos = ftell(f);
  if (savedpos<0)
    mcpl_error(errmsg);
  if (fseek( f, MCPLIMP_NPARTICLES_POS, SEEK_SET ))
    mcpl_error(errmsg);
  size_t nb = fwrite(&n, 1, sizeof(n), f);
  if (nb != sizeof(n))
    mcpl_error(errmsg);
  if (fseek( f, savedpos, SEEK_SET ))
    mcpl_error(errmsg);
}

mcpl_particle_t* mcpl_get_empty_particle(mcpl_outfile_t of)
{
  MCPLIMP_OUTFILEDECODE;
  if (f->puser) {
    //Calling more than once. This could be innocent, or it could indicate
    //problems in multi-threaded user-code. Better disallow and give an error:
    mcpl_error("mcpl_get_empty_particle must not be called more than once per output file");
  } else {
    f->puser = (mcpl_particle_t*)calloc(sizeof(mcpl_particle_t),1);
  }
  return f->puser;
}

void mcpl_close_outfile(mcpl_outfile_t of)
{
  MCPLIMP_OUTFILEDECODE;
  if (f->header_notwritten)
    mcpl_write_header(of);
  if (f->nparticles)
    mcpl_update_nparticles(f->file,f->nparticles);
  fclose(f->file);
  free(f->filename);
  free(f->puser);
  free(f);
}

void mcpl_transfer_metadata(mcpl_file_t source, mcpl_outfile_t target)
{
  //Note that MCPL format version 2 and 3 have the same meta-data in the header,
  //except of course the version number itself.

  if (mcpl_hdr_little_endian(source) != mcpl_platform_is_little_endian())
    mcpl_error("mcpl_transfer_metadata can only work on files with same endianness as current platform.");

  mcpl_hdr_set_srcname(target,mcpl_hdr_srcname(source));
  unsigned i;
  for (i = 0; i < mcpl_hdr_ncomments(source); ++i)
    mcpl_hdr_add_comment(target,mcpl_hdr_comment(source,i));
  const char** blobkeys = mcpl_hdr_blobkeys(source);
  if (blobkeys) {
    int nblobs = mcpl_hdr_nblobs(source);
    uint32_t ldata;
    const char * data;
    int ii;
    for (ii = 0; ii < nblobs; ++ii) {
      int res = mcpl_hdr_blob(source,blobkeys[ii],&ldata,&data);
      assert(res);//key must exist
      (void)res;
      mcpl_hdr_add_data(target, blobkeys[ii], ldata, data);
    }
  }
  if (mcpl_hdr_has_userflags(source))
    mcpl_enable_userflags(target);
  if (mcpl_hdr_has_polarisation(source))
    mcpl_enable_polarisation(target);
  if (mcpl_hdr_has_doubleprec(source))
    mcpl_enable_doubleprec(target);
  int32_t updg = mcpl_hdr_universal_pdgcode(source);
  if (updg)
    mcpl_enable_universal_pdgcode(target,updg);
  double uw = mcpl_hdr_universal_weight(source);
  if (uw)
    mcpl_enable_universal_weight(target,uw);
}

int mcpl_closeandgzip_outfile_rc(mcpl_outfile_t of)
{
    printf("MCPL WARNING: Usage of function mcpl_closeandgzip_outfile_rc is obsolete as"
         " mcpl_closeandgzip_outfile now also returns the status. Please update your code"
           " to use mcpl_closeandgzip_outfile instead.\n");
    return mcpl_closeandgzip_outfile(of);
}

int mcpl_closeandgzip_outfile(mcpl_outfile_t of)
{
  MCPLIMP_OUTFILEDECODE;
  char * filename = f->filename;
  f->filename = 0;//prevent free in mcpl_close_outfile
  mcpl_close_outfile(of);
  int rc = mcpl_gzip_file(filename);
  free(filename);
  return rc;
}

typedef struct {
  FILE * file;
#ifdef MCPL_HASZLIB
  gzFile filegz;
#else
  void * filegz;
#endif
  char * hdr_srcprogname;
  unsigned format_version;
  int opt_userflags;
  int opt_polarisation;
  int opt_singleprec;
  int32_t opt_universalpdgcode;
  double opt_universalweight;
  int is_little_endian;
  uint64_t nparticles;
  uint32_t ncomments;
  char ** comments;
  uint32_t nblobs;
  char ** blobkeys;
  uint32_t * bloblengths;
  char ** blobs;
  unsigned particle_size;
  uint64_t first_particle_pos;
  uint64_t current_particle_idx;
  mcpl_particle_t* particle;
  unsigned opt_signature;
  char particle_buffer[MCPLIMP_MAX_PARTICLE_SIZE];
} mcpl_fileinternal_t;

#define MCPLIMP_FILEDECODE mcpl_fileinternal_t * f = (mcpl_fileinternal_t *)ff.internal; assert(f)

void mcpl_read_buffer(mcpl_fileinternal_t* f, unsigned* n, char ** buf, const char * errmsg)
{
  size_t nb;
#ifdef MCPL_HASZLIB
  if (f->filegz)
    nb = gzread(f->filegz, n, sizeof(*n));
  else
#endif
    nb = fread(n, 1, sizeof(*n), f->file);
  if (nb!=sizeof(*n))
    mcpl_error(errmsg);
  *buf = (char*)calloc(*n,1);
#ifdef MCPL_HASZLIB
  if (f->filegz)
    nb = gzread(f->filegz, *buf, *n);
  else
#endif
    nb = fread(*buf, 1, *n, f->file);
  if (nb!=*n)
    mcpl_error(errmsg);
}

void mcpl_read_string(mcpl_fileinternal_t* f, char ** dest, const char* errmsg)
{
  size_t nb;
  uint32_t n;
#ifdef MCPL_HASZLIB
  if (f->filegz)
    nb = gzread(f->filegz, &n, sizeof(n));
  else
#endif
    nb = fread(&n, 1, sizeof(n), f->file);
  if (nb!=sizeof(n))
    mcpl_error(errmsg);
  char * s = (char*)calloc(n+1,1);
#ifdef MCPL_HASZLIB
  if (f->filegz)
    nb = gzread(f->filegz, s, n);
  else
#endif
    nb = fread(s, 1, n, f->file);
  if (nb!=n)
    mcpl_error(errmsg);
  s[n] = '\0';
  *dest = s;
}

mcpl_file_t mcpl_actual_open_file(const char * filename, int * repair_status)
{
  int caller_is_mcpl_repair = *repair_status;
  *repair_status = 0;//file not broken

  if (!filename)
    mcpl_error("mcpl_open_file called with null string");

  mcpl_platform_compatibility_check();

  mcpl_file_t out;
  out.internal = 0;

  mcpl_fileinternal_t * f = (mcpl_fileinternal_t*)calloc(sizeof(mcpl_fileinternal_t),1);
  assert(f);

  //open file (with gzopen if filename ends with .gz):
  f->file = 0;
  f->filegz = 0;
  const char * lastdot = strrchr(filename, '.');
  if (lastdot && strcmp(lastdot, ".gz") == 0) {
#ifdef MCPL_HASZLIB
    f->filegz = gzopen(filename,"rb");
    if (!f->filegz)
      mcpl_error("Unable to open file!");
#else
    mcpl_error("This installation of MCPL was not built with zlib support and can not read compressed (.gz) files directly.");
#endif
  } else {
    f->file = fopen(filename,"rb");
    if (!f->file)
      mcpl_error("Unable to open file!");
  }

  //First read and check magic word, format version and endianness.
  unsigned char start[8];// = {'M','C','P','L','0','0','0','L'};
  size_t nb;
#ifdef MCPL_HASZLIB
  if (f->filegz)
    nb = gzread(f->filegz, start, sizeof(start));
  else
#endif
    nb = fread(start, 1, sizeof(start), f->file);
  if (nb>=4&&(start[0]!='M'||start[1]!='C'||start[2]!='P'||start[3]!='L'))
    mcpl_error("File is not an MCPL file!");
  if (nb!=sizeof(start))
    mcpl_error("Error while reading first bytes of file!");
  f->format_version = (start[4]-'0')*100 + (start[5]-'0')*10 + (start[6]-'0');
  if (f->format_version!=2&&f->format_version!=3)
    mcpl_error("File is in an unsupported MCPL version!");
  f->is_little_endian = mcpl_platform_is_little_endian();
  if (start[7]!=(f->is_little_endian?'L':'B'))
    mcpl_error("Endian-ness of current platform is different than the one used to write the file.");

  //proceed reading header, knowing we have a consistent version and endian-ness.
  const char * errmsg = "Errors encountered while attempting to read header";

  uint64_t np;
#ifdef MCPL_HASZLIB
  if (f->filegz)
    nb = gzread(f->filegz, &np, sizeof(np));
  else
#endif
    nb = fread(&np, 1, sizeof(np), f->file);
  if (nb!=sizeof(np))
    mcpl_error(errmsg);
  f->nparticles = np;

  uint32_t arr[8];
  assert(sizeof(arr)==32);
#ifdef MCPL_HASZLIB
  if (f->filegz)
    nb = gzread(f->filegz, arr, sizeof(arr));
  else
#endif
    nb=fread(arr, 1, sizeof(arr), f->file);
  if (nb!=sizeof(arr))
    mcpl_error(errmsg);

  f->ncomments = arr[0];
  f->nblobs = arr[1];
  f->opt_userflags = arr[2];
  f->opt_polarisation = arr[3];
  f->opt_singleprec = arr[4];
  f->opt_universalpdgcode = arr[5];
  f->particle_size = arr[6];//We could check consistency here with the calculated value.
  assert(f->particle_size<=MCPLIMP_MAX_PARTICLE_SIZE);

  if (arr[7]) {
    //file has universal weight
#ifdef MCPL_HASZLIB
    if (f->filegz)
      nb = gzread(f->filegz, (void*)&(f->opt_universalweight), sizeof(f->opt_universalweight));
    else
#endif
      nb=fread((void*)&(f->opt_universalweight), 1, sizeof(f->opt_universalweight), f->file);
    assert(nb==sizeof(f->opt_universalweight));
    if (nb!=sizeof(f->opt_universalweight))
      mcpl_error(errmsg);
  }

  f->opt_signature = 0
    + 1 * f->opt_singleprec
    + 2 * f->opt_polarisation
    + 4 * f->opt_universalpdgcode
    + 8 * (f->opt_universalweight?1:0)
    + 16 * f->opt_userflags;

  //Then some strings:
  mcpl_read_string(f,&f->hdr_srcprogname,errmsg);
  f->comments = f->ncomments ? (char **)calloc(f->ncomments,sizeof(char*)) : 0;
  uint32_t i;
  for (i = 0; i < f->ncomments; ++i)
    mcpl_read_string(f,&(f->comments[i]),errmsg);

  f->blobkeys = 0;
  f->bloblengths = 0;
  f->blobs = 0;
  if (f->nblobs) {
    f->blobs = (char **)calloc(f->nblobs,sizeof(char*));
    f->blobkeys = (char **)calloc(f->nblobs,sizeof(char*));
    f->bloblengths = (uint32_t *)calloc(f->nblobs,sizeof(uint32_t));
    for (i =0; i < f->nblobs; ++i)
      mcpl_read_string(f,&(f->blobkeys[i]),errmsg);
    for (i =0; i < f->nblobs; ++i)
      mcpl_read_buffer(f, &(f->bloblengths[i]), &(f->blobs[i]), errmsg);
  }
  f->particle = (mcpl_particle_t*)calloc(sizeof(mcpl_particle_t),1);

  //At first event now:
  f->current_particle_idx = 0;
  int64_t tellpos = -1;
#ifdef MCPL_HASZLIB
  if (f->filegz)
    tellpos = gztell(f->filegz);
  else
#endif
    tellpos = ftell(f->file);
  if (tellpos<0)
    mcpl_error(errmsg);
  f->first_particle_pos = tellpos;

  if (f->nparticles==0) {
    //Although empty files are permitted, it is possible that the file was never
    //closed properly (maybe the writing program ended prematurely). Let us
    //check to possibly recover usage of the file.
    if (f->filegz) {
      //SEEK_END is not supported by zlib, and there is no reliable way to get
      //the input size. Thus, all we can do is to uncompress the whole thing,
      //which we won't since it might stall operations for a long time. But we
      //can at least try to check whether the file is indeed empty or not, and
      //give an error in the latter case:
#ifdef MCPL_HASZLIB
      char testbuf[4];
      nb = gzread(f->filegz, testbuf, sizeof(testbuf));
      if (nb>0) {
        if (caller_is_mcpl_repair) {
          *repair_status = 1;//file broken but can't recover since gzip.
        } else {
          mcpl_error("Input file appears to not have been closed properly and data recovery is disabled for gzipped files.");
        }
      }
      gzseek( f->filegz, f->first_particle_pos, SEEK_SET );
#endif
    } else {
      if (f->file && !fseek( f->file, 0, SEEK_END )) {//SEEK_END is not guaranteed to always work, so we fail our recovery attempt silently.
        int64_t endpos = ftell(f->file);
        if (endpos > (int64_t)f->first_particle_pos && (uint64_t)endpos != f->first_particle_pos) {
          f->nparticles = ( endpos - f->first_particle_pos ) / f->particle_size;
          if (caller_is_mcpl_repair) {
            *repair_status = 2;//file broken and should be able to repair
          } else {
            printf("MCPL WARNING: Input file appears to not have been closed properly. Recovered %" PRIu64 " particles.\n",
                   f->nparticles);
          }
        }
      }
      fseek( f->file, f->first_particle_pos, SEEK_SET );//if this fseek failed, it might just be that we are at EOF with no particles.
    }
  }

  out.internal = f;
  return out;
}

mcpl_file_t mcpl_open_file(const char * filename)
{
  int repair_status = 0;
  return mcpl_actual_open_file(filename,&repair_status);
}

void mcpl_repair(const char * filename)
{
  int repair_status = 1;
  mcpl_file_t f = mcpl_actual_open_file(filename,&repair_status);
  uint64_t nparticles = mcpl_hdr_nparticles(f);
  mcpl_close_file(f);
  if (repair_status==0) {
    mcpl_error("Asked to repair file which does not appear to be broken.");
  } else if (repair_status==1) {
    mcpl_error("Input file is indeed broken, but must be gunzipped before it can be repaired.");
  }
  //Ok, we should repair the file by updating nparticles in the header:
  FILE * fh = fopen(filename,"rb+");
  if (!fh)
    mcpl_error("Unable to open file in update mode!");
  mcpl_update_nparticles(fh, nparticles);
  fclose(fh);
  //Verify that we fixed it:
  repair_status = 1;
  f = mcpl_actual_open_file(filename,&repair_status);
  uint64_t nparticles2 = mcpl_hdr_nparticles(f);
  mcpl_close_file(f);
  if (repair_status==0&&nparticles==nparticles2) {
    printf("MCPL: Succesfully repaired file with %" PRIu64 " particles.\n",nparticles);
  } else {
    mcpl_error("Something went wrong while attempting to repair file.");
  }
}

void mcpl_close_file(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;

  free(f->hdr_srcprogname);
  uint32_t i;
  for (i = 0; i < f->ncomments; ++i)
    free(f->comments[i]);
  free(f->comments);
  for (i = 0; i < f->nblobs; ++i)
    free(f->blobkeys[i]);
  for (i = 0; i < f->nblobs; ++i)
    free(f->blobs[i]);
  free(f->blobkeys);
  free(f->blobs);
  free(f->bloblengths);
  free(f->particle);
#ifdef MCPL_HASZLIB
  if (f->filegz)
    gzclose(f->filegz);
#endif
  if (f->file)
    fclose(f->file);
  free(f);
}


unsigned mcpl_hdr_version(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->format_version;
}

uint64_t mcpl_hdr_nparticles(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->nparticles;
}

unsigned mcpl_hdr_ncomments(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->ncomments;
}

const char * mcpl_hdr_comment(mcpl_file_t ff, unsigned i)
{
  MCPLIMP_FILEDECODE;
  if (i>=f->ncomments)
    mcpl_error("Invalid comment requested (index out of bounds)");
  return f->comments[i];
}

int mcpl_hdr_nblobs(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->nblobs;
}

const char** mcpl_hdr_blobkeys(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return (const char**)f->blobkeys;
}

int mcpl_hdr_blob(mcpl_file_t ff, const char* key,
                  uint32_t* ldata, const char ** data)
{
  MCPLIMP_FILEDECODE;
  uint32_t i;
  for (i = 0; i < f->nblobs; ++i) {
    if (strcmp(f->blobkeys[i],key)==0) {
      *data = f->blobs[i];
      *ldata = f->bloblengths[i];
      return 1;
    }
  }
  *data = 0;
  *ldata = 0;
  return 0;
}

const char* mcpl_hdr_srcname(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->hdr_srcprogname;
}

int mcpl_hdr_has_userflags(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->opt_userflags;
}

int mcpl_hdr_has_polarisation(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->opt_polarisation;
}

int mcpl_hdr_has_doubleprec(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return !f->opt_singleprec;
}

const mcpl_particle_t* mcpl_read(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  f->current_particle_idx += 1;
  if ( f->current_particle_idx > f->nparticles ) {
    f->current_particle_idx = f->nparticles;//overflow guard
    return 0;
  }

  //read particle data:
  size_t nb;
  unsigned lbuf = f->particle_size;
  char * pbuf = &(f->particle_buffer[0]);
#ifdef MCPL_HASZLIB
    if (f->filegz)
      nb = gzread(f->filegz, pbuf, lbuf);
    else
#endif
      nb = fread(pbuf, 1, lbuf, f->file);
  if (nb!=lbuf)
    mcpl_error("Errors encountered while attempting to read particle data.");

  //Transfer to particle struct:
  unsigned ibuf = 0;
  mcpl_particle_t * p = f->particle;
  double pack_ekindir[3];
  p->weight = f->opt_universalweight;
  int i;
  if (f->opt_singleprec) {
    if (f->opt_polarisation) {
      for (i=0;i<3;++i) {
        p->polarisation[i] = *(float*)&pbuf[ibuf];
        ibuf += sizeof(float);
      }
    } else {
      for (i=0;i<3;++i)
        p->polarisation[i] = 0.0;
    }
    for (i=0;i<3;++i) {
      p->position[i] = *(float*)&pbuf[ibuf];
      ibuf += sizeof(float);
    }
    for (i=0;i<3;++i) {
      pack_ekindir[i] = *(float*)&pbuf[ibuf];
      ibuf += sizeof(float);
    }
    p->time = *(float*)&pbuf[ibuf];
    ibuf += sizeof(float);
    if (!p->weight) {
      p->weight = *(float*)&pbuf[ibuf];
      ibuf += sizeof(float);
    }
  } else {
    if (f->opt_polarisation) {
      for (i=0;i<3;++i) {
        p->polarisation[i] = *(double*)&pbuf[ibuf];
        ibuf += sizeof(double);
      }
    } else {
      for (i=0;i<3;++i)
        p->polarisation[i] = 0.0;
    }
    for (i=0;i<3;++i) {
      p->position[i] = *(double*)&pbuf[ibuf];
      ibuf += sizeof(double);
    }
    for (i=0;i<3;++i) {
      pack_ekindir[i] = *(double*)&pbuf[ibuf];
      ibuf += sizeof(double);
    }
    p->time = *(double*)&pbuf[ibuf];
    ibuf += sizeof(double);
    if (!p->weight) {
      p->weight = *(double*)&pbuf[ibuf];
      ibuf += sizeof(double);
    }
  }

  if (f->opt_universalpdgcode) {
    p->pdgcode = f->opt_universalpdgcode;
  } else {
    p->pdgcode = *(int32_t*)&pbuf[ibuf];
    ibuf += sizeof(int32_t);
  }
  if (f->opt_userflags) {
    p->userflags = *(uint32_t*)&pbuf[ibuf];
    ibuf += sizeof(uint32_t);
  } else {
    f->opt_userflags = 0;
  }
  assert(ibuf==lbuf);

  //Unpack direction and ekin:

  if (f->format_version>=3) {
    p->ekin = fabs(pack_ekindir[2]);
    pack_ekindir[2] = copysign(1.0,pack_ekindir[2]);
    mcpl_unitvect_unpack_adaptproj(pack_ekindir,p->direction);
  } else {
    assert(f->format_version==2);
    mcpl_unitvect_unpack_oct(pack_ekindir,p->direction);
    p->ekin = pack_ekindir[2];
    if (signbit(pack_ekindir[2])) {
      p->ekin = -p->ekin;
      p->direction[2] = 0.0;
    }
  }
  return p;
}

int mcpl_skipforward(mcpl_file_t ff,uint64_t n)
{
  MCPLIMP_FILEDECODE;
  //increment, but guard against overflows:
  if ( n >= f->nparticles || f->current_particle_idx >= f->nparticles )
    f->current_particle_idx = f->nparticles;
  else
    f->current_particle_idx += n;
  if ( f->current_particle_idx > f->nparticles )
    f->current_particle_idx = f->nparticles;

  int notEOF = f->current_particle_idx<f->nparticles;
  if (n==0)
    return notEOF;
  if (notEOF) {
    int error;
#ifdef MCPL_HASZLIB
    if (f->filegz) {
      int64_t targetpos = f->current_particle_idx*f->particle_size+f->first_particle_pos;
      error = gzseek( f->filegz, targetpos, SEEK_SET )!=targetpos;
    } else
#endif
      error = fseek( f->file, f->particle_size * n, SEEK_CUR )!=0;
    if (error)
      mcpl_error("Errors encountered while skipping in particle list");
  }
  return notEOF;
}

int mcpl_rewind(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  int already_there = (f->current_particle_idx==0);
  f->current_particle_idx = 0;
  int notEOF = f->current_particle_idx<f->nparticles;
  if (notEOF&&!already_there) {
    int error;
#ifdef MCPL_HASZLIB
    if (f->filegz) {
      error = gzseek( f->filegz, f->first_particle_pos, SEEK_SET )!=(int64_t)f->first_particle_pos;
    } else
#endif
      error = fseek( f->file, f->first_particle_pos, SEEK_SET )!=0;
    if (error)
      mcpl_error("Errors encountered while rewinding particle list");
  }
  return notEOF;
}

int mcpl_seek(mcpl_file_t ff,uint64_t ipos)
{
  MCPLIMP_FILEDECODE;
  int already_there = (f->current_particle_idx==ipos);
  f->current_particle_idx = (ipos<f->nparticles?ipos:f->nparticles);
  int notEOF = f->current_particle_idx<f->nparticles;
  if (notEOF&&!already_there) {
    int error;
#ifdef MCPL_HASZLIB
    if (f->filegz) {
      int64_t targetpos = f->current_particle_idx*f->particle_size+f->first_particle_pos;
      error = gzseek( f->filegz, targetpos, SEEK_SET )!=targetpos;
    } else
#endif
      error = fseek( f->file, f->first_particle_pos + f->particle_size * ipos, SEEK_SET )!=0;
    if (error)
      mcpl_error("Errors encountered while seeking in particle list");
  }
  return notEOF;
}

uint64_t mcpl_currentposition(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->current_particle_idx;
}

const char * mcpl_basename(const char * filename)
{
  //portable "basename" which doesn't modify it's argument:
  const char * bn = strrchr(filename, '/');
  return bn ? bn + 1 : filename;
}

int mcpl_hdr_particle_size(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->particle_size;
}

uint64_t mcpl_hdr_header_size(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->first_particle_pos;
}

int mcpl_hdr_universal_pdgcode(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->opt_universalpdgcode;
}

int mcpl_hdr_universel_pdgcode(mcpl_file_t ff)
{
  printf("MCPL WARNING: Usage of function mcpl_hdr_universel_pdgcode is obsolete as it has"
         " been renamed to mcpl_hdr_universal_pdgcode. Please update your code.\n");
  return mcpl_hdr_universal_pdgcode(ff);
}

double mcpl_hdr_universal_weight(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->opt_universalweight;
}

int mcpl_hdr_little_endian(mcpl_file_t ff)
{
  MCPLIMP_FILEDECODE;
  return f->is_little_endian;
}

void mcpl_transfer_last_read_particle(mcpl_file_t source, mcpl_outfile_t target)
{
  //TODO: We keep this as an internal function for now, but it would be great to
  //have it publically available. But first, we should extend it a bit to better
  //work when source and target have somewhat different settings. When
  //signatures are different, we should not error but instead revert to slower code
  //which would only error if the transfer would throw away information
  //(e.g. polarisation or pdgcode not possible to set in output, but ok to not
  //enable opt_userflags or double prec).

  mcpl_outfileinternal_t * ft = (mcpl_outfileinternal_t *)target.internal; assert(ft);
  mcpl_fileinternal_t * fs = (mcpl_fileinternal_t *)source.internal; assert(fs);

  if (ft->opt_signature!=fs->opt_signature) {
    mcpl_error("mcpl_transfer_last_read_particle used on files with incompatible options.");
  }

  if (fs->format_version==2) {
    //source file is in old format with different unit vector packing. Thus, we
    //can not avoid a repacking, but this is unavoidable when we want to keep
    //older files as fully functioning as possible:
    mcpl_add_particle(target,fs->particle);
    return;
  }

  if (ft->header_notwritten)
    mcpl_write_header(target);

  assert(fs->particle_size==ft->particle_size);
  ft->nparticles += 1;

  size_t nb;
  nb = fwrite(fs->particle_buffer, 1, fs->particle_size, ft->file);
  if (nb!=fs->particle_size)
    mcpl_error("Errors encountered while attempting to write particle data.");
}

void mcpl_dump_header(mcpl_file_t f)
{
  printf("\n  Basic info\n");
  printf("    Format             : MCPL-%i\n",mcpl_hdr_version(f));
  printf("    No. of particles   : %" PRIu64 "\n",mcpl_hdr_nparticles(f));
  printf("    Header storage     : %" PRIu64 " bytes\n",mcpl_hdr_header_size(f));
  printf("    Data storage       : %" PRIu64 " bytes\n",mcpl_hdr_nparticles(f)*mcpl_hdr_particle_size(f));
  printf("\n  Custom meta data\n");
  printf("    Source             : \"%s\"\n",mcpl_hdr_srcname(f));
  unsigned nc=mcpl_hdr_ncomments(f);
  printf("    Number of comments : %i\n",nc);
  unsigned ic;
  for (ic = 0; ic < nc; ++ic)
    printf("          -> comment %i : \"%s\"\n",ic,mcpl_hdr_comment(f,ic));
  unsigned nb = mcpl_hdr_nblobs(f);
  printf("    Number of blobs    : %i\n",nb);
  const char** blobkeys = mcpl_hdr_blobkeys(f);
  uint32_t ib;
  for (ib = 0; ib < nb; ++ib) {
    const char * data;
    uint32_t ldata;
    int ok = mcpl_hdr_blob(f, blobkeys[ib], &ldata, &data);
    if (!ok)
      mcpl_error("Unexpected blob access error");
    printf("          -> %lu bytes of data with key \"%s\"\n",(unsigned long)ldata,blobkeys[ib]);
  }

  printf("\n  Particle data format\n");
  printf("    User flags         : %s\n",(mcpl_hdr_has_userflags(f)?"yes":"no"));
  printf("    Polarisation info  : %s\n",(mcpl_hdr_has_polarisation(f)?"yes":"no"));
  printf("    Fixed part. type   : ");
  int32_t updg = mcpl_hdr_universal_pdgcode(f);
  if (updg)
    printf("yes (pdgcode %li)\n",(long)updg);
  else
    printf("no\n");
  printf("    Fixed part. weight : ");
  double uw = mcpl_hdr_universal_weight(f);
  if (uw)
    printf("yes (weight %g)\n",uw);
  else
    printf("no\n");
  printf("    FP precision       : %s\n",(mcpl_hdr_has_doubleprec(f)?"double":"single"));
  printf("    Endianness         : %s\n",(mcpl_hdr_little_endian(f)?"little":"big"));
  printf("    Storage            : %i bytes/particle\n",mcpl_hdr_particle_size(f));

  printf("\n");
}

//Not in the public interface, but perhaps it should be to allow custom
//applications to apply custom filters and see the selected particles. For now,
//we simply keep the function signature stable, allowing other code to access it
//by forward declaring it themselves:
void mcpl_dump_particles(mcpl_file_t f, uint64_t nskip, uint64_t nlimit,
                         int(filter)(const mcpl_particle_t*))
{
  int has_uf = mcpl_hdr_has_userflags(f);
  int has_pol = mcpl_hdr_has_polarisation(f);
  printf("index     pdgcode   ekin[MeV]       x[cm]       y[cm]       z[cm]          ux          uy          uz    time[ms]      weight");
  if (has_pol)
    printf("       pol-x       pol-y       pol-z");
  if (has_uf)
    printf("  userflags");
  printf("\n");
  mcpl_skipforward(f,nskip);
  uint64_t count = nlimit;
  const mcpl_particle_t* p;
  while((nlimit==0||count--)&&(p=mcpl_read(f))) {
    if (filter && !filter(p) ) {
      ++count;
      continue;
    }
    uint64_t idx = mcpl_currentposition(f)-1;//-1 since mcpl_read skipped ahead
    printf("%5" PRIu64 " %11i %11.5g %11.5g %11.5g %11.5g %11.5g %11.5g %11.5g %11.5g %11.5g",
           idx,
           p->pdgcode,
           p->ekin,
           p->position[0],
           p->position[1],
           p->position[2],
           p->direction[0],
           p->direction[1],
           p->direction[2],
           p->time,
           p->weight
           );
    if (has_pol)
      printf(" %11.5g %11.5g %11.5g",p->polarisation[0],p->polarisation[1],p->polarisation[2]);
    if (has_uf)
      printf(" 0x%08x",p->userflags);
    printf("\n");
  }
}

void mcpl_dump(const char * filename, int parts, uint64_t nskip, uint64_t nlimit)
{
  if (parts<0||parts>2)
    mcpl_error("mcpl_dump got forbidden value for argument parts");
  mcpl_file_t f = mcpl_open_file(filename);
  printf("Opened MCPL file %s:\n",mcpl_basename(filename));
  if (parts==0||parts==1)
    mcpl_dump_header(f);
  if (parts==0||parts==2)
    mcpl_dump_particles(f,nskip,nlimit,0);
  mcpl_close_file(f);
}

int mcpl_actual_can_merge(mcpl_file_t ff1, mcpl_file_t ff2)
{
  mcpl_fileinternal_t * f1 = (mcpl_fileinternal_t *)ff1.internal;
  mcpl_fileinternal_t * f2 = (mcpl_fileinternal_t *)ff2.internal;
  assert(f1&&f2);
  if (f1->first_particle_pos!=f2->first_particle_pos)
    return 0;//different header

  //Note, we do not check the format_version field here, since mcpl_merge_files
  //can actually work on files with different versions.

  //Very strict checking of everything except nparticles. Even order of blobs
  //and comments must be preserved (could possibly be relaxed a bit):
  if (strcmp(f1->hdr_srcprogname,f2->hdr_srcprogname)!=0) return 0;
  if (f1->opt_userflags!=f2->opt_userflags) return 0;
  if (f1->opt_polarisation!=f2->opt_polarisation) return 0;
  if (f1->opt_singleprec!=f2->opt_singleprec) return 0;
  if (f1->opt_universalpdgcode!=f2->opt_universalpdgcode) return 0;
  if (f1->opt_universalweight!=f2->opt_universalweight) return 0;
  if (f1->is_little_endian!=f2->is_little_endian) return 0;
  if (f1->particle_size!=f2->particle_size) return 0;
  if (f1->ncomments!=f2->ncomments) return 0;
  if (f1->nblobs!=f2->nblobs) return 0;
  uint32_t i;
  for (i = 0; i<f1->ncomments; ++i) {
    if (strcmp(f1->comments[i],f2->comments[i])!=0) return 0;
  }
  for (i = 0; i<f1->nblobs; ++i) {
    if (f1->bloblengths[i]!=f2->bloblengths[i]) return 0;
    if (strcmp(f1->blobkeys[i],f2->blobkeys[i])!=0) return 0;
    if (memcmp(f1->blobs[i],f2->blobs[i],f1->bloblengths[i])!=0) return 0;
  }
  return 1;
}


int mcpl_can_merge(const char * file1, const char* file2)
{
  mcpl_file_t f1 = mcpl_open_file(file1);
  mcpl_file_t f2 = mcpl_open_file(file2);
  int can_merge = mcpl_actual_can_merge(f1,f2);
  mcpl_close_file(f1);
  mcpl_close_file(f2);
  return can_merge;
}

#ifdef MCPL_THIS_IS_UNIX
#  include <sys/stat.h>
#endif

int mcpl_file_certainly_exists(const char * filename)
{
#if defined MCPL_THIS_IS_UNIX || defined MCPL_THIS_IS_MS
  if( access( filename, F_OK ) != -1 )
    return 1;
  return 0;
#else
  //esoteric platform without access(..). Try opening for reads:
  FILE *fd;
  if ((fd = fopen(filename, "r"))) {
    fclose(fd);
    return 1;
  }
  //non-existing or read access not allowed:
  return 0;
#endif
}

#ifdef MCPL_THIS_IS_UNIX
#  include <sys/types.h>
#  include <sys/stat.h>
#endif

void mcpl_warn_duplicates(unsigned n, const char ** filenames)
{
  //Checks that no filenames in provided list represent the same file (the
  //detection is not 100% certain on non-POSIX platforms). If duplicates are
  //found, emit warning - it is assumed the function is called from
  //mcpl_merge_xxx on a user-provided list of files.

  //Since this is C, we resort to slow O(N^2) comparison for simplicity.

  if (n<2)
    return;

#ifdef MCPL_THIS_IS_UNIX
  //Bullet proof(ish) way, (st_ino,st_dev) uniquely identifies a file on a system.
  dev_t * id_dev = (dev_t*)calloc(n*sizeof(dev_t),1);
  ino_t * id_ino = (ino_t*)calloc(n*sizeof(ino_t),1);
  unsigned i;
  for (i = 0; i<n; ++i) {
    FILE * fd = fopen(filenames[i],"rb");
    struct stat sinfo;
    if( !fd || fstat(fileno(fd), &sinfo) < 0) {
      id_dev[i] = 0;
      id_ino[i] = 0;
    } else {
      id_dev[i] = sinfo.st_dev;
      id_ino[i] = sinfo.st_ino;
    }
    if (fd)
      fclose(fd);
    if (id_dev[i]==0&&id_ino[i]==0) {
      printf("MCPL WARNING: Problems %s file (%s).\n",
             (fd?"accessing meta data of":"opening"),filenames[i]);
      continue;
    }
    unsigned j;
    for (j = 0; j<i; ++j) {
      if (id_dev[j]==0&&id_ino[j]==0)
        continue;
      if (id_ino[i]==id_ino[j] && id_dev[i]==id_dev[j]) {
        if (strcmp(filenames[i], filenames[j]) == 0) {
          printf("MCPL WARNING: Merging file with itself (%s).\n",
                 filenames[i]);
        } else {
          printf("MCPL WARNING: Merging file with itself (%s and %s are the same file).\n",
                 filenames[j],filenames[i]);
        }
      }
    }
  }
  free(id_dev);
  free(id_ino);
#else
  //Simple check that strings are unique. Very easy to fool obviously and could
  //be improved with platform-dependent code to at least normalise paths before
  //comparison.
  unsigned i, j;
  for (i = 0; i<n; ++i) {
    for (j = i+1; j<n; ++j) {
      if (strcmp(filenames[i], filenames[j]) == 0) {
        printf("MCPL WARNING: Merging file with itself (%s).\n",
               filenames[i]);
      }
    }
  }
#endif
}


//Internal function for merges which will transfer the particle data in the
//input file into an output file handle which must already be open and ready to
//be written to, and otherwise be associated with an MCPL file with a compatible
//format. Note that the error messages assume the overall operation is a merge:
void mcpl_transfer_particle_contents(FILE * fo, mcpl_file_t ffi, uint64_t nparticles)
{
  mcpl_fileinternal_t * fi = (mcpl_fileinternal_t *)ffi.internal; assert(fi);

  if (!nparticles)
    return;//no particles to transfer

  unsigned particle_size = fi->particle_size;

  //buffer for transferring up to 1000 particles at a time:
  const unsigned npbufsize = 1000;
  char * buf = (char*)malloc(npbufsize*particle_size);
  uint64_t np_remaining = nparticles;

  while(np_remaining) {
    //NB: On linux > 2.6.33 we could use sendfile for more efficient in-kernel
    //transfer of data between two files!
    uint64_t toread = np_remaining >= npbufsize ? npbufsize : np_remaining;
    np_remaining -= toread;

    //read:
    size_t nb;
#ifdef MCPL_HASZLIB
    if (fi->filegz)
      nb = gzread(fi->filegz, buf, toread*particle_size);
    else
#endif
      nb = fread(buf,1,toread*particle_size,fi->file);
    if (nb!=toread*particle_size)
      mcpl_error("Unexpected read-error while merging");

    //write:
    nb = fwrite(buf,1,toread*particle_size,fo);
    if (nb!=toread*particle_size)
      mcpl_error("Unexpected write-error while merging");
  }

  free(buf);
}


mcpl_outfile_t mcpl_merge_files( const char* file_output,
                                 unsigned nfiles, const char ** files)
{
  mcpl_outfile_t out;
  out.internal = 0;

  if (!nfiles)
    mcpl_error("mcpl_merge_files must be called with at least one input file");

  //Check all files for compatibility before we start (for robustness, we check
  //again when actually merging each file).
  unsigned ifile;
  for (ifile = 1; ifile < nfiles; ++ifile) {
    if (!mcpl_can_merge(files[0],files[ifile]))
      mcpl_error("Attempting to merge incompatible files.");
  }

  //Warn user if they are merging a file with itself:
  mcpl_warn_duplicates(nfiles,files);

  //Create new file:

  if (mcpl_file_certainly_exists(file_output))
    mcpl_error("requested output file of mcpl_merge_files already exists");

  out = mcpl_create_outfile(file_output);
  mcpl_outfileinternal_t * out_internal = (mcpl_outfileinternal_t *)out.internal;

  mcpl_file_t f1;
  f1.internal = 0;

  int warned_oldversion = 0;

  for (ifile = 0; ifile < nfiles; ++ifile) {
    mcpl_file_t fi = mcpl_open_file(files[ifile]);
    if (ifile==0) {
      //Add metadata from the first file:
      mcpl_transfer_metadata(fi, out);
      if (out_internal->header_notwritten)
        mcpl_write_header(out);
      f1 = fi;
    } else {
      //Check file is still compatible with first file
      if (!mcpl_actual_can_merge(f1,fi))
        mcpl_error("Aborting merge of suddenly incompatible files.");
    }

    //Transfer particle contents:
    if (mcpl_hdr_version(fi)==MCPL_FORMATVERSION) {
      //Can transfer raw bytes:
      uint64_t npi = mcpl_hdr_nparticles(fi);
      mcpl_transfer_particle_contents(out_internal->file, fi, npi);
      out_internal->nparticles += npi;
    } else {
      //Merging from older version. Transfer via public interface to re-encode
      //particle data for latest format:
      if (!warned_oldversion) {
        warned_oldversion = 1;
        printf("MCPL WARNING: Merging files from older MCPL format. Output will be in latest format.\n");
      }
      const mcpl_particle_t* particle;
      while ( ( particle = mcpl_read(fi) ) )
        mcpl_add_particle(out,particle);
    }

    if (ifile!=0)
      mcpl_close_file(fi);
  }

  mcpl_close_file(f1);

  return out;
}

void mcpl_merge(const char * file1, const char* file2)
{
  printf("MCPL WARNING: Usage of function mcpl_merge is obsolete as it has"
         " been renamed to mcpl_merge_inplace. Please update your code.\n");
  mcpl_merge_inplace(file1, file2);
}

void mcpl_merge_inplace(const char * file1, const char* file2)
{
  mcpl_file_t ff1 = mcpl_open_file(file1);
  mcpl_file_t ff2 = mcpl_open_file(file2);
  int can_merge = mcpl_actual_can_merge(ff1,ff2);
  if (!can_merge) {
    mcpl_close_file(ff1);
    mcpl_close_file(ff2);
    mcpl_error("Attempting to merge incompatible files");
  }
  //Warn user if they are merging a file with itself:
  const char * filelist[2];
  filelist[0] = file1;
  filelist[1] = file2;
  mcpl_warn_duplicates(2,filelist);

  //Access internals:
  mcpl_fileinternal_t * f1 = (mcpl_fileinternal_t *)ff1.internal;
  mcpl_fileinternal_t * f2 = (mcpl_fileinternal_t *)ff2.internal;
  assert(f1&&f2);

  if (f1->format_version!=f2->format_version) {
    mcpl_close_file(ff1);
    mcpl_close_file(ff2);
    mcpl_error("Attempting to merge incompatible files (can not mix MCPL format versions when merging inplace)");
  }

  if (f1->filegz) {
    mcpl_close_file(ff1);
    mcpl_close_file(ff2);
    mcpl_error("direct modification of gzipped files is not supported.");
  }

  uint64_t np1 = f1->nparticles;
  uint64_t np2 = f2->nparticles;
  if (!np2)
    return;//nothing to take from file 2.

  unsigned particle_size = f1->particle_size;
  uint64_t first_particle_pos = f1->first_particle_pos;

  //Should be same since can_merge:
  assert(particle_size==f2->particle_size);
  assert(first_particle_pos==f2->first_particle_pos);

  //Now, close file1 and reopen a file handle in append mode:
  mcpl_close_file(ff1);
  FILE * f1a = fopen(file1,"rb+");

  //Update file positions. Note that f2->file is already at the position for the
  //first particle and that the seek operation on f1a correctly discards any
  //partial entries at the end, which could be there if the file was in need of
  //mcpl_repair:
  if (!f1a)
    mcpl_error("Unable to open file1 in update mode!");
  if (fseek( f1a, first_particle_pos + particle_size*np1, SEEK_SET ))
    mcpl_error("Unable to seek to end of file1 in update mode");

  //Transfer particle contents, setting nparticles to 0 during the operation (so
  //the file appears broken and in need of mcpl_repair in case of errors during
  //the transfer):
  mcpl_update_nparticles(f1a,0);
  mcpl_transfer_particle_contents(f1a, ff2, np2);
  mcpl_update_nparticles(f1a,np1+np2);

  //Finish up.
  mcpl_close_file(ff2);
  fclose(f1a);
}

#define MCPLIMP_TOOL_DEFAULT_NLIMIT 10
#define MCPLIMP_TOOL_DEFAULT_NSKIP 0

int mcpl_tool_usage( char** argv, const char * errmsg ) {
  if (errmsg) {
    printf("ERROR: %s\n\n",errmsg);
    printf("Run with -h or --help for usage information\n");
    return 1;
  }
  const char * progname = mcpl_basename(argv[0]);

  printf("Tool for inspecting or modifying Monte Carlo Particle List (.mcpl) files.\n");
  printf("\n");
  printf("The default behaviour is to display the contents of the FILE in human readable\n");
  printf("format (see Dump Options below for how to modify what is displayed).\n");
  printf("\n");
#ifdef MCPL_HASZLIB
  printf("This installation supports direct reading of gzipped files (.mcpl.gz).\n");
  printf("\n");
#endif
  printf("Usage:\n");
  printf("  %s [dump-options] FILE\n",progname);
  printf("  %s --merge [merge-options] FILE1 FILE2\n",progname);
  printf("  %s --extract [extract-options] FILE1 FILE2\n",progname);
  printf("  %s --repair FILE\n",progname);
  printf("  %s --version\n",progname);
  printf("  %s --help\n",progname);
  printf("\n");
  printf("Dump options:\n");
  printf("  By default include the info in the FILE header plus the first ten contained\n");
  printf("  particles. Modify with the following options:\n");
  assert(MCPLIMP_TOOL_DEFAULT_NLIMIT==10);
  printf("  -j, --justhead  : Dump just header info and no particle info.\n");
  printf("  -n, --nohead    : Dump just particle info and no header info.\n");
  printf("  -lN             : Dump up to N particles from the file (default %i). You\n",MCPLIMP_TOOL_DEFAULT_NLIMIT);
  printf("                    can specify -l0 to disable this limit.\n");
  printf("  -sN             : Skip past the first N particles in the file (default %i).\n",MCPLIMP_TOOL_DEFAULT_NSKIP);
  printf("  -bKEY           : Dump binary blob stored under KEY to standard output.\n");
  printf("\n");
  printf("Merge options:\n");
  printf("  -m, --merge FILEOUT FILE1 FILE2 ... FILEN\n");
  printf("                    Creates new FILEOUT with combined particle contents from\n");
  printf("                    specified list of N existing and compatible files.\n");
  printf("  -m, --merge --inplace FILE1 FILE2 ... FILEN\n");
  printf("                    Appends the particle contents in FILE2 ... FILEN into\n");
  printf("                    FILE1. Note that this action modifies FILE1!\n");
  printf("\n");
  printf("Extract options:\n");
  printf("  -e, --extract FILE1 FILE2\n");
  printf("                    Extracts particles from FILE1 into a new FILE2.\n");
  printf("  -lN, -sN          Select range of particles in FILE1 (as above).\n");
  printf("  -pPDGCODE         select particles of type given by PDGCODE.\n");
  printf("\n");
  printf("Other options:\n");
  printf("  -r, --repair FILE\n");
  printf("                    Attempt to repair FILE which was not properly closed, by up-\n");
  printf("                    dating the file header with the correct number of particles.\n");
  printf("  -v, --version   : Display version of MCPL installation.\n");
  printf("  -h, --help      : Display this usage information (ignores all other options).\n");

  return 0;
}

int mcpl_str2int(const char* str, size_t len, int64_t* res)
{
  //portable 64bit str2int with error checking (only INT64_MIN might not be
  //possible to specify).
  *res = 0;
  if (!len)
    len=strlen(str);
  if (!len)
    return 0;
  int sign = 1;
  if (str[0]=='-') {
    sign = -1;
    len -= 1;
    str += 1;
  }
  int64_t tmp = 0;
  size_t i;
  for (i=0; i<len; ++i) {
    if (str[i]<'0'||str[i]>'9') {
      return 0;
    }
    int64_t prev = tmp;
    tmp *= 10;
    tmp += str[i] - '0';
    if (prev>=tmp)
      return 1;//overflow (hopefully it did not trigger a signal or FPE)
  }
  *res = sign * tmp;
  return 1;
}

int mcpl_tool(int argc,char** argv) {

  int nfilenames = 0;
  char ** filenames = 0;
  const char * blobkey = 0;
  const char * pdgcode_str = 0;
  int opt_justhead = 0;
  int opt_nohead = 0;
  int64_t opt_num_limit = -1;
  int64_t opt_num_skip = -1;
  int opt_merge = 0;
  int opt_inplace = 0;
  int opt_extract = 0;
  int opt_preventcomment = 0;//undocumented unoffical flag for mcpl unit tests
  int opt_repair = 0;
  int opt_version = 0;

  int i;
  for (i = 1; i<argc; ++i) {
    char * a = argv[i];
    size_t n=strlen(a);
    if (!n)
      continue;
    if (n>=2&&a[0]=='-'&&a[1]!='-') {
      //short options:
      int64_t * consume_digit = 0;
      size_t j;
      for (j=1; j<n; ++j) {
        if (consume_digit) {
          if (a[j]<'0'||a[j]>'9')
            return mcpl_tool_usage(argv,"Bad option: expected number");
          *consume_digit *= 10;
          *consume_digit += a[j] - '0';
          continue;
        }
        if (a[j]=='b') {
          if (blobkey)
            return mcpl_tool_usage(argv,"-b specified more than once");
          if (j+1==n)
            return mcpl_tool_usage(argv,"Missing argument for -b");
          blobkey = a+j+1;
          break;
        }
        if (a[j]=='p') {
          if (pdgcode_str)
            return mcpl_tool_usage(argv,"-p specified more than once");
          if (j+1==n)
            return mcpl_tool_usage(argv,"Missing argument for -p");
          pdgcode_str = a+j+1;
          break;
        }

        switch(a[j]) {
          case 'h': return mcpl_tool_usage(argv,0);
          case 'j': opt_justhead = 1; break;
          case 'n': opt_nohead = 1; break;
          case 'm': opt_merge = 1; break;
          case 'e': opt_extract = 1; break;
          case 'r': opt_repair = 1; break;
          case 'v': opt_version = 1; break;
          case 'l': consume_digit = &opt_num_limit; break;
          case 's': consume_digit = &opt_num_skip; break;
          default:
            return mcpl_tool_usage(argv,"Unrecognised option");
        }
        if (consume_digit) {
          *consume_digit = 0;
          if (j+1==n)
            return mcpl_tool_usage(argv,"Bad option: missing number");
        }
      }
    } else if (n>=3&&a[0]=='-'&&a[1]=='-') {
      a+=2;
      //long options:
      const char * lo_help = "help";
      const char * lo_justhead = "justhead";
      const char * lo_nohead = "nohead";
      const char * lo_merge = "merge";
      const char * lo_inplace = "inplace";
      const char * lo_extract = "extract";
      const char * lo_preventcomment = "preventcomment";
      const char * lo_repair = "repair";
      const char * lo_version = "version";
      //Use strstr instead of "strcmp(a,"--help")==0" to support shortened
      //versions (works since all our long-opts start with unique char).
      if (strstr(lo_help,a)==lo_help) return mcpl_tool_usage(argv,0);
      else if (strstr(lo_justhead,a)==lo_justhead) opt_justhead = 1;
      else if (strstr(lo_nohead,a)==lo_nohead) opt_nohead = 1;
      else if (strstr(lo_merge,a)==lo_merge) opt_merge = 1;
      else if (strstr(lo_inplace,a)==lo_inplace) opt_inplace = 1;
      else if (strstr(lo_extract,a)==lo_extract) opt_extract = 1;
      else if (strstr(lo_repair,a)==lo_repair) opt_repair = 1;
      else if (strstr(lo_version,a)==lo_version) opt_version = 1;
      else if (strstr(lo_preventcomment,a)==lo_preventcomment) opt_preventcomment = 1;
      else return mcpl_tool_usage(argv,"Unrecognised option");
    } else if (n>=1&&a[0]!='-') {
      //input file
      if (!filenames) {
        //For code simplicity, we overallocate and never free:
        filenames = (char **)calloc(argc,sizeof(char*));
      }
      filenames[nfilenames] = a;
      ++nfilenames;
    } else {
      return mcpl_tool_usage(argv,"Bad arguments");
    }
  }

  if ( opt_extract==0 && pdgcode_str )
    return mcpl_tool_usage(argv,"-p can only be used with --extract.");

  if ( opt_merge==0 && opt_inplace!=0 )
    return mcpl_tool_usage(argv,"--inplace can only be used with --merge.");

  int number_dumpopts = (opt_justhead + opt_nohead + (blobkey!=0));
  if (opt_extract==0)
    number_dumpopts += (opt_num_limit!=-1) + (opt_num_skip!=-1);
  int any_dumpopts = number_dumpopts != 0;
  int any_extractopts = (opt_extract!=0||pdgcode_str!=0);
  int any_mergeopts = (opt_merge!=0);
  if (any_dumpopts+any_mergeopts+any_extractopts+opt_repair+opt_version>1)
    return mcpl_tool_usage(argv,"Conflicting options specified.");

  if (blobkey&&(number_dumpopts>1))
    return mcpl_tool_usage(argv,"Do not specify other dump options with -b.");

  if (opt_version) {
    if (nfilenames)
      return mcpl_tool_usage(argv,"Unrecognised arguments for --version.");
    printf("MCPL version " MCPL_VERSION_STR "\n");
    return 0;
  }

  if (opt_merge) {

    if (nfilenames<2)
      return mcpl_tool_usage(argv,"Too few arguments for --merge.");

    int ifirstinfile = (opt_inplace ? 0 : 1);
    for (i = ifirstinfile+1; i < nfilenames; ++i)
      if (!mcpl_can_merge(filenames[ifirstinfile],filenames[i]))
        return mcpl_tool_usage(argv,"Requested files are incompatible for merge as they have different header info.");

    if (opt_inplace) {
      for (i = ifirstinfile+1; i < nfilenames; ++i)
        mcpl_merge_inplace(filenames[ifirstinfile],filenames[i]);
    } else {
      if (mcpl_file_certainly_exists(filenames[0]))
        return mcpl_tool_usage(argv,"Requested output file already exists.");

      //Disallow .gz endings unless it is .mcpl.gz, in which case we attempt to gzip automatically.
      char * outfn = filenames[0];
      size_t lfn = strlen(outfn);
      int attempt_gzip = 0;
      if( lfn > 8 && !strcmp(outfn + (lfn - 8), ".mcpl.gz")) {
        attempt_gzip = 1;
        outfn = (char*)malloc(lfn+1);
        outfn[0] = '\0';
        strcat(outfn,filenames[0]);
        outfn[lfn-3] = '\0';
        if (mcpl_file_certainly_exists(outfn))
          return mcpl_tool_usage(argv,"Requested output file already exists (without .gz extension).");

      } else if( lfn > 3 && !strcmp(outfn + (lfn - 3), ".gz")) {
        return mcpl_tool_usage(argv,"Requested output file should not have .gz extension (unless it is .mcpl.gz).");
      }

      mcpl_outfile_t mf = mcpl_merge_files( outfn, nfilenames-1, (const char**)filenames + 1);
      if (attempt_gzip) {
        if (!mcpl_closeandgzip_outfile(mf))
          printf("MCPL WARNING: Failed to gzip output. Non-gzipped output is found in %s\n",outfn);
      } else {
        mcpl_close_outfile(mf);
      }
      if (outfn != filenames[0])
        free(outfn);
    }

    return 0;
  }

  if (opt_extract) {
    if (nfilenames>2)
      return mcpl_tool_usage(argv,"Too many arguments.");

    if (nfilenames!=2)
      return mcpl_tool_usage(argv,"Must specify both input and output files with --extract.");

    if (mcpl_file_certainly_exists(filenames[1]))
      return mcpl_tool_usage(argv,"Requested output file already exists.");

    mcpl_file_t fi = mcpl_open_file(filenames[0]);
    mcpl_outfile_t fo = mcpl_create_outfile(filenames[1]);
    mcpl_transfer_metadata(fi, fo);
    uint64_t fi_nparticles = mcpl_hdr_nparticles(fi);

    if (!opt_preventcomment) {
      char comment[1024];
      sprintf(comment, "mcpltool: extracted particles from file with %" PRIu64 " particles",fi_nparticles);
      mcpl_hdr_add_comment(fo,comment);
    }

    int32_t pdgcode_select = 0;
    if (pdgcode_str) {
      int64_t pdgcode64;
      if (!mcpl_str2int(pdgcode_str, 0, &pdgcode64) || pdgcode64<-2147483648 || pdgcode64>2147483647 || !pdgcode64)
        return mcpl_tool_usage(argv,"Must specify non-zero 32bit integer as argument to -p.");
      pdgcode_select = (int32_t)pdgcode64;
    }

    if (opt_num_skip>0)
      mcpl_seek(fi,(uint64_t)opt_num_skip);

    //uint64_t(-1) instead of UINT64_MAX to fix clang c++98 compilation
    uint64_t left = opt_num_limit>0 ? (uint64_t)opt_num_limit : (uint64_t)-1;
    uint64_t added = 0;
    const mcpl_particle_t* particle;
    while ( left-- && ( particle = mcpl_read(fi) ) ) {
      if (pdgcode_select && pdgcode_select!= particle->pdgcode)
        continue;
      mcpl_transfer_last_read_particle(fi, fo);//Doing mcpl_add_particle(fo,particle) is potentially (very rarely) lossy
      ++added;
    }

    char *fo_filename = (char*)malloc(strlen(mcpl_outfile_filename(fo))+4);
    fo_filename[0] = '\0';
    strcat(fo_filename,mcpl_outfile_filename(fo));
    if (mcpl_closeandgzip_outfile(fo))
      strcat(fo_filename,".gz");
    mcpl_close_file(fi);

    printf("MCPL: Succesfully extracted %" PRIu64 " / %" PRIu64 " particles from %s into %s\n",
           added,fi_nparticles,filenames[0],fo_filename);
    free(fo_filename);
    return 0;
  }

  if (nfilenames>1)
    return mcpl_tool_usage(argv,"Too many arguments.");

  if (!nfilenames)
    return mcpl_tool_usage(argv,"No input file specified");

  if (opt_repair) {
    mcpl_repair(filenames[0]);
    return 0;
  }

  //Dump mode:
  if (blobkey) {
    mcpl_file_t mcplfile = mcpl_open_file(filenames[0]);
    uint32_t ldata;
    const char * data;
    if (!mcpl_hdr_blob(mcplfile, blobkey, &ldata, &data))
      return 1;//mcpl_tool_usage(argv,"Too many arguments.");
#ifdef MCPL_THIS_IS_MS
    setmode(STDOUT_FILENO, O_BINARY);
#endif
    uint32_t nb = write(STDOUT_FILENO,data,ldata);
    if (nb!=ldata)
      mcpl_error("Problems writing to stdout");
    return 0;
  }

  if (opt_justhead&&(opt_num_limit!=-1||opt_num_skip!=-1))
    return mcpl_tool_usage(argv,"Do not specify -l or -s with --justhead");

  if (opt_num_limit<0) opt_num_limit = MCPLIMP_TOOL_DEFAULT_NLIMIT;
  if (opt_num_skip<0) opt_num_skip = MCPLIMP_TOOL_DEFAULT_NSKIP;

  if (opt_justhead&&opt_nohead)
    return mcpl_tool_usage(argv,"Do not supply both --justhead and --nohead.");

  int parts = 0;
  if (opt_nohead) parts=2;
  else if (opt_justhead) parts=1;
  mcpl_dump(filenames[0],parts,opt_num_skip,opt_num_limit);
  return 0;
}

int mcpl_gzip_file_rc(const char * filename)
{
  printf("MCPL WARNING: Usage of function mcpl_gzip_file_rc is obsolete as"
         " mcpl_gzip_file now also returns the status. Please update your code"
         " to use mcpl_gzip_file instead.\n");
  return mcpl_gzip_file(filename);
}

#if defined(MCPL_HASZLIB) && !defined(Z_SOLO) && !defined(MCPL_NO_CUSTOM_GZIP)
#  define MCPLIMP_HAS_CUSTOM_GZIP
int _mcpl_custom_gzip(const char *file, const char *mode);//return 1 if successful, 0 if not
#endif

#if defined MCPL_THIS_IS_UNIX && !defined(MCPL_NO_EXT_GZIP)
//Platform is unix-like enough that we assume gzip is installed and we can
//include posix headers.
#  include <sys/types.h>
#  include <sys/wait.h>
#  include <errno.h>

int mcpl_gzip_file(const char * filename)
{
  const char * bn = strrchr(filename, '/');
  bn = bn ? bn + 1 : filename;

  //spawn process in which to perform gzip:
  printf("MCPL: Attempting to compress file %s with gzip\n",bn);
  fflush(0);
  pid_t gzip_pid = fork();
  if (gzip_pid) {
    //main proc
    int chld_state = 0;
    pid_t ret = waitpid(gzip_pid,&chld_state,0);
    if (ret!=gzip_pid||chld_state!=0) {
#  ifdef MCPLIMP_HAS_CUSTOM_GZIP
      printf("MCPL WARNING: Problems invoking gzip - will revert to a custom zlib based compression\n");
      if (!_mcpl_custom_gzip(filename,"wb"))
        mcpl_error("Problems encountered while attempting to compress file");
      else
        printf("MCPL: Succesfully compressed file into %s.gz\n",bn);
#  else
      mcpl_error("Problems encountered while attempting to invoke gzip");
#  endif
    }
    else
      printf("MCPL: Succesfully compressed file into %s.gz\n",bn);
  } else {
    //spawned proc in which to invoke gzip
    execlp("gzip", "gzip", "-f",filename, (char*)0);
    printf("MCPL: execlp/gzip error: %s\n",strerror(errno));
    exit(1);
  }
  return 1;
}
#else
//Non unix-y platform (like windows). We could use e.g. windows-specific calls
//instead of the fork() and waitpid() used above, but gzip likely not present on
//the system anyway, so we either resort to using zlib directly to gzip, or we
//disable the feature and print a warning.
#  ifndef MCPLIMP_HAS_CUSTOM_GZIP
int mcpl_gzip_file(const char * filename)
{
  const char * bn = strrchr(filename, '/');
  bn = bn ? bn + 1 : filename;
  printf("MCPL WARNING: Requested compression of %s to %s.gz is not supported in this build.\n",bn,bn);
  return 0;
}
#  else
int mcpl_gzip_file(const char * filename)
{
  const char * bn = strrchr(filename, '/');
  bn = bn ? bn + 1 : filename;
  printf("MCPL: Attempting to compress file %s with zlib\n",bn);
  if (!_mcpl_custom_gzip(filename,"wb"))
    printf("MCPL ERROR: Problems encountered while compressing file %s.\n",bn);
  else
    printf("MCPL: Succesfully compressed file into %s.gz\n",bn);
  return 1;
}
#  endif
#endif

#ifdef MCPLIMP_HAS_CUSTOM_GZIP

int _mcpl_custom_gzip(const char *filename, const char *mode)
{
  //Open input file:
  FILE *handle_in = fopen(filename, "rb");
  if (!handle_in)
    return 0;

  //Construct output file name by appending .gz:
  char * outfn = (char*)malloc(strlen(filename) + 4);
  outfn[0] = '\0';
  strcat(outfn,filename);
  strcat(outfn,".gz");

  //Open output file:
  gzFile handle_out = gzopen(outfn, mode);

  free(outfn);

  if (!handle_out) {
    fclose(handle_in);
    return 0;
  }

  //Compress input to output:
  char buf[16384];
  size_t len;
  while (1) {
    len = (int)fread(buf, 1, sizeof(buf), handle_in);
    if (ferror(handle_in))
      return 0;
    if (!len)
      break;
    if ((size_t)gzwrite(handle_out, buf, (unsigned)len) != len)
      return 0;
  }

  //close file:
  fclose(handle_in);
  if (gzclose(handle_out) != Z_OK)
    return 0;

  //remove input file and return success:
  unlink(filename);
  return 1;
}

#endif
