
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

////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  phitsread : Code for reading binary dump files from PHITS                 //
//                                                                            //
//  Compilation of phitsread.c can proceed via any compliant C-compiler using //
//  -std=c99 or later, and the resulting code must always be linked with libm //
//  (using -lm).                                                              //
//                                                                            //
// Note that usage of PHITS-related utilities might require additional        //
// permissions and licenses from third-parties, which is not within the       //
// scope of the MCPL project itself.                                          //
//                                                                            //
// Written 2019-2025, thomas.kittelmann@ess.eu (European Spallation Source).  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "phitsread.h"
#include "mcpl.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>

FILE** phits_impl_stdout_data(void)
{
  static FILE* thefh = NULL;
  return &thefh;
}

FILE* phits_stdout(void)
{
  FILE* thefh = *phits_impl_stdout_data();
  return thefh ? thefh : stdout;
}

void phits_set_stdout( FILE* fh )
{
  fflush(stdout);
  fflush(stderr);
  FILE** fhptr = phits_impl_stdout_data();
  if (*fhptr)
    fflush(*fhptr);
  if (fh)
    fflush(fh);
  *fhptr = fh;
}


static int phits_known_nonion_codes[] = { 11, 12, 13, 14, 22, 111, 211, 221,
                                          311, 321, 331, 2112, 2212, 3112,
                                          3122, 3212, 3222, 3312, 3322, 3334 };

int phits_cmp_codes( void const *va, void const *vb )
{
  //Standard integer comparison function for bsearch
  const int * a = (const int *)va;
  const int * b = (const int *)vb;
  return  *a < *b ? -1 : ( *a > *b ? 1 : 0 );
}

int32_t conv_code_phits2pdg( int32_t c )
{
  int32_t absc = c < 0 ? -c : c;
  if (!c)
    return 0;
  if (absc<1000000) {
    //Presumably PHITS use pdg codes directly for non-nuclei/ions
    return c;
  }
  //PHITS encode nucleis as Z*1000000+A
  long A = absc % 1000000;
  long Z = absc / 1000000;
  if (!Z||Z>130||A<Z||A>500)//Just picking max Z=130, A=500 as a quick sanity check - could tighten this!
    return 0;//impossible
  //PDG format for ions is 10LZZZAAAI, where L!=0 indicates strangeness
  //and I!=0 indicates exited nuclei. We only allow L=I=0 ions here.
  long abspdgcode = 10 * (A + 1000*(Z+100000));
  return (int32_t) ( c < 0 ? -abspdgcode : abspdgcode );
}

void phits_error(const char * msg) {
  fprintf(phits_stdout(),"ERROR: %s\n",msg);
  exit(1);
}

int32_t conv_code_pdg2phits( int32_t c )
{
  int32_t absc = c < 0 ? -c : c;
  if ( absc <= 1000000000 ) {
    //Presumably PHITS use pdg codes directly for non-nuclei/ions, but only with
    //room for 6 digits. And in fact, only those in the phits_known_nonion_codes
    //are supported - and for 22, 111, 331 only if not negative (these particles
    //are their own antiparticles):
    int key = absc;
    void * res = bsearch(&key, phits_known_nonion_codes, sizeof(phits_known_nonion_codes) / sizeof(phits_known_nonion_codes[0]),
                         sizeof(phits_known_nonion_codes[0]), phits_cmp_codes);
    if ( !res || ( c < 0 && (c==-22||c==-111||c==-331) ) )
      return 0;
    return c;
  }
  if (absc<=1009999990) {
    //Ions. PDG format for ions is 10LZZZAAAI, where L!=0 indicates strangeness
    //and I!=0 indicates exited nuclei. We only allow L=I=0 ions here.
    if (c<0)
      return 0;//Negative ions seems to not actually be supported in PHITS.
    int32_t I = absc % 10;//isomer level
    absc/=10;
    int32_t A = absc%1000;
    absc/=1000;
    int32_t Z = absc % 1000;
    if ( !(absc/1000==100) ) {
      //L=0 guaranteed by enclosing condition.
      phits_error("pdgcode conversion logic error");
    }
    if ( I || !A || !Z || Z>A )
      return 0;
    //PHITS encode nucleis as Z*1000000+A:
    int32_t absphitscode = Z*1000000+A;
    return c < 0 ? -absphitscode : absphitscode;
  }
  return 0;
}

//Should be more than large enough to hold all records in all supported PHITS
//dump files, including two 64bit record markers:
#define PHITSREAD_MAXBUFSIZE (15*sizeof(double))

typedef struct {
  mcpl_generic_filehandle_t filehandle;
  phits_particle_t part;
  int reclen;//width of Fortran record length field (4 or 8)
  unsigned particlesize;//length of particle data in bytes (typically 10*8 or 13*8)
  char buf[PHITSREAD_MAXBUFSIZE];//for holding last record of raw data read (including record markers of reclen bytes)
  unsigned lbuf;//number of bytes currently read into buf
  int haspolarisation;
} phits_fileinternal_t;

int phits_ensure_load(phits_fileinternal_t* f, int nbytes)
{
  //For slowly filling up f->buf while reading first record. Returns 1 in case
  //of success.
  if ( nbytes > (int)PHITSREAD_MAXBUFSIZE )
    return 0;
  int missing = nbytes - f->lbuf;
  if ( missing<=0 )
    return 1;
  int actual = (int)mcpl_generic_fread_try( &f->filehandle,
                                            &(f->buf[f->lbuf]),
                                            (unsigned)missing );
  //int nr = phits_readbytes(f,&(f->buf[f->lbuf]),missing);
  if (actual!=missing)
    return 0;
  f->lbuf = nbytes;
  return 1;
}

int phits_tryload_reclen(phits_fileinternal_t* f, int reclen ) {
  assert(reclen==4||reclen==8);
  if ( ! phits_ensure_load( f, reclen ) )
    return 0;
  char * buf = & ( f->buf[0] );
  uint64_t l1 = ( reclen == 4 ? (uint64_t)(*((uint32_t*)buf)) : (uint64_t)(*((uint64_t*)buf)) );
  uint64_t tmp = l1 + 2*reclen;
  if ( tmp > INT_MAX )
    phits_error("Unexpectedly large record encountered");
  if ( ! phits_ensure_load( f, (int)tmp ) )
    return 0;
  buf += (reclen + l1);
  uint64_t l2 = ( reclen == 4 ? (uint64_t)(*((uint32_t*)buf)) : (uint64_t)(*((uint64_t*)buf)) );
  if (l1!=l2)
    return 0;
  //All ok!
  f->reclen = reclen;
  if ( l1 != 10*8 && l1 != 13*8 )
    phits_error("Unexpected particle size!");
  f->particlesize = (unsigned)l1;
  return 1;
}

phits_file_t phits_open_internal( const char * filename )
{
  phits_fileinternal_t * f = (phits_fileinternal_t*)calloc(1,sizeof(phits_fileinternal_t));
  if (!f)
    phits_error("memory allocation failure");

  phits_file_t out;
  out.internal = f;

  //Init:
  f->particlesize = 0;
  f->lbuf = 0;
  f->reclen = 4;
  f->haspolarisation = 0;
  memset( &( f->part ),0,sizeof(f->part) );

  //open file (supports gzipped if ends with .gz):
  f->filehandle = mcpl_generic_fopen( filename );

  //Try to read first Fortran record marker, keeping in mind that we do not
  //know if it is 32bit or 64bit, and that an empty file is to be interpreted
  //as a valid PHITS dump file with 0 particles:

  if (!phits_ensure_load(f,1)) {
    //Can't read a single byte. Assume that this indicates an empty file and
    //therefore a valid PHITS dump file with 0 particles:
    //file with 0 particles, mark as EOF:
    f->particlesize = 0;
    f->haspolarisation = 0;//Convention: We mark empty files as NOT HAVING
    //polarisation info (to avoid potentially inflating
    //mcpl files in various merge/conversion
    //scenarios).
    return out;
  }

  //Try to read first record with first 32bit then 64bit record lengths
  //(updating f->reclen and f->particlesize in case of success):
  if (!phits_tryload_reclen(f,4)) {
    if (!phits_tryload_reclen(f,8)) {
      if (f->lbuf<8)
        phits_error("Invalid PHITS dump file: too short\n");
      phits_error("Invalid PHITS dump file: Problems reading first record.\n");
    }
  }
  assert( f->reclen==4 || f->reclen==8 );

  if (f->reclen==8) {
    fprintf(phits_stdout(),"phits_open_file WARNING: 64bit Fortran records"
            " detected which is untested (feedback"
            " appreciated at https://mctools.github.io/mcpl/contact/).\n");
  }

  if (f->particlesize == 10*sizeof(double)) {
    f->haspolarisation = 0;
  } else if (f->particlesize == 13*sizeof(double)) {
    f->haspolarisation = 1;
  } else {
    phits_error("Invalid PHITS dump file: Does not contain exactly 10 or 13 fields in each"
                " particle - like due to unsupported configuration flags being used when"
                " producing the file.\n");
  }

  return out;
}

phits_file_t phits_open_file( const char * filename )
{
  if (!filename)
    phits_error("phits_open_file called with null string for filename");

  //Open, classify and process first record with mcnp type and version info:
  phits_file_t out = phits_open_internal( filename );
  phits_fileinternal_t * f = (phits_fileinternal_t *)out.internal;
  assert(f);

  out.internal = f;
  return out;
}
const phits_particle_t * phits_load_particle(phits_file_t ff)
{
  phits_fileinternal_t * f = (phits_fileinternal_t *)ff.internal;
  assert(f);

  if (!f->particlesize) {
    //EOF already
    return 0;
  }

  assert( f->particlesize == 10*sizeof(double) || f->particlesize == 13*sizeof(double) );

  if (!f->lbuf) {
    if (!phits_ensure_load(f, 1)) {
      //Can't read a single byte - assume EOF:
      f->particlesize = 0;
      return 0;
    }
    //Try to load another record
    int old_reclen = f->reclen;
    (void)old_reclen;//otherwise unused if assert inactive.
    unsigned old_particlesize = f->particlesize;
    if (!phits_tryload_reclen(f,f->reclen)) {
      phits_error("Problems loading particle data record!");
      //return 0;
    }
    assert(f->reclen==old_reclen);
    if ( f->particlesize != old_particlesize) {
      phits_error("Problems loading particle data record - particle"
                  " data length changed mid-file (perhaps it is not"
                  " actually a binary PHITS dump file after all?)!");
      //return 0;
    }
  }

  assert( f->lbuf == f->particlesize + f->reclen * 2 );
  double * pdata = (double*)(f->buf+f->reclen);
  phits_particle_t * pp =  & (f->part);
  pp->rawtype = (long)pdata[0];
  //NB: PHITS units, not MCPL units here (only difference is time unit which is ns in PHITS and ms in MCPL):
  pp->x = pdata[1];//cm
  pp->y = pdata[2];//cm
  pp->z = pdata[3];//cm
  pp->dirx = pdata[4];
  pp->diry = pdata[5];
  pp->dirz = pdata[6];
  pp->ekin = pdata[7];//MeV
  pp->weight = pdata[8];
  pp->time = pdata[9];//ns
  if (f->particlesize == 13*sizeof(double)) {
    pp->polx = pdata[10];
    pp->poly = pdata[11];
    pp->polz = pdata[12];
  } else {
    pp->polx = 0.0;
    pp->poly = 0.0;
    pp->polz = 0.0;
  }

  pp->pdgcode = conv_code_phits2pdg(pp->rawtype);

  //Mark as used:
  f->lbuf = 0;

  return pp;
}

int phits_has_polarisation(phits_file_t ff)
{
  phits_fileinternal_t * f = (phits_fileinternal_t *)ff.internal;
  if (!f)
    phits_error("Invalid file object passed to phits_has_polarisation");
  return f->haspolarisation;
}

void phits_close_file(phits_file_t ff)
{
  phits_fileinternal_t * f = (phits_fileinternal_t *)ff.internal;
  if (!f)
    phits_error("Invalid file object passed to phits_close_file");
  if ( f->filehandle.internal ) {
    mcpl_generic_fclose( &f->filehandle );
    f->filehandle.internal = NULL;
  }
  free(f);
  ff.internal = 0;
}

#ifdef MCPLPHITS_IS_TEST_LIB
//Function needed for unit tests, outfile must be ascii characters only (for
//now):
#ifdef _MSC_VER
#  pragma warning( push )
#  pragma warning( disable : 4996 )
#endif
FILE* phits_simple_fopenw( const char * fn )
{
  return fopen( fn, "w" );
}
#ifdef _MSC_VER
#  pragma warning( pop )
#endif

void phits_dump( const char * filename, const char * outfile )
{
  FILE* outfh = phits_simple_fopenw( outfile ); // Open file for writing
  phits_set_stdout(outfh);

  phits_file_t f = phits_open_file(filename);

  fprintf(phits_stdout(),"opened binary PHITS dump file with contents:\n");
  int haspol = phits_has_polarisation(f);
  fprintf(phits_stdout(),"    pdgcode   ekin[MeV]       x[cm]       y[cm]       z[cm]"
          "          ux          uy          uz%s"
          "    time[ns]      weight\n",(haspol?"        polx        poly        polz":""));
  while (1) {
    const phits_particle_t * p = phits_load_particle(f);
    if (!p)
      break;
    fprintf(phits_stdout(),"%10li %11.5g %11.5g %11.5g %11.5g"
            " %11.5g %11.5g %11.5g",
            p->pdgcode,p->ekin,p->x,p->y,p->z,
            p->dirx,p->diry,p->dirz);
    if (haspol)
      fprintf(phits_stdout()," %11.5g %11.5g %11.5g",p->polx,p->poly,p->polz);
    fprintf(phits_stdout()," %11.5g %11.5g\n",p->time,p->weight);
  }

  phits_close_file(f);
  fclose(outfh);
  phits_set_stdout(NULL);

}
#endif
