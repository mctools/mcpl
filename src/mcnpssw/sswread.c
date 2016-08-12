
/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
//  sswread : Code for reading SSW files from MCNP(X)                              //
//                                                                                 //
//                                                                                 //
//  Compilation of sswread.c can proceed via any compliant C-compiler using        //
//  -std=c99 later, and the resulting code must always be linked with libm         //
//  (using -lm). Furthermore, the following preprocessor flags can be used         //
//  when compiling sswread.c to fine tune the build process and the                //
//  capabilities of the resulting binary.                                          //
//                                                                                 //
//  SSWREAD_HASZLIB : Define if compiling and linking with zlib, to allow direct   //
//                      reading of gzipped SSW files.                              //
//  SSWREAD_ZLIB_INCPATH : Specify alternative value if the zlib header is         //
//                           not to be included as "zlib.h".                       //
//  SSWREAD_HDR_INCPATH : Specify alternative value if the sswread header          //
//                          itself is not to be included as "sswread.h".           //
//                                                                                 //
// This file can be freely used as per the terms in the LICENSE file.              //
//                                                                                 //
// However, note that usage of MCNP(X)-related utilities might require additional  //
// permissions and licenses from third-parties, which is not within the scope of   //
// the MCPL project itself.                                                        //
//                                                                                 //
//  Written 2015-2016, thomas.kittelmann@esss.se (European Spallation Source).     //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

#ifdef SSWREAD_HDR_INCPATH
#  include SSWREAD_HDR_INCPATH
#else
#  include "sswread.h"
#endif

#ifdef SSWREAD_HASZLIB
#  ifdef SSWREAD_ZLIB_INCPATH
#    include SSWREAD_ZLIB_INCPATH
#  else
#    include "zlib.h"
#  endif
#endif

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdint.h>

void ssw_error(const char * msg) {
  printf("ERROR: %s\n",msg);
  exit(1);
}

typedef struct {
  //Fortran width of record length field (4 or 8)
  int reclen;

  //Header data:
  char kods[9];   // Code
  char vers[6];   // Version
  char lods[29];  // Date
  char idtms[20]; // Machine-Designator
  char probs[20]; // Problem-ID
  char aids[81];  // Creation-Run Problem-Title-Card
  int32_t np1;
  int32_t nrss;
  int32_t njsw;
  int32_t nrcd;
  int32_t niss;
  int32_t pos;
  int is_mcnp6;
#ifdef SSWREAD_HASZLIB
  gzFile filegz;
#else
  void * filegz;
#endif
  FILE * file;
  ssw_particle_t part;
  unsigned lbuf;
  char buf[1024];
  size_t np1pos;
  size_t nrsspos;
  size_t headlen;
} ssw_fileinternal_t;

#define SSW_FILEDECODE ssw_fileinternal_t * f = (ssw_fileinternal_t *)ff.internal; assert(f)

int ssw_readbytes(ssw_fileinternal_t* f, char * dest, int nbytes)
{
  int nb;
#ifdef SSWREAD_HASZLIB
  if (f->filegz)
    nb = gzread(f->filegz, dest, nbytes);
  else
#endif
    nb = fread(dest, 1, nbytes, f->file);
  if (nb!=nbytes) {
    printf("SSW Error: read failure\n");
    return 0;
  }
  return 1;
}

int ssw_loadrecord(ssw_fileinternal_t* f)
{
  if (f->reclen==4) {
    uint32_t rl;
    if (!ssw_readbytes(f, (char*)&rl, 4))
      return 0;
    f->lbuf = rl;
  } else {
    uint64_t rl;
    if (!ssw_readbytes(f, (char*)&rl, 8))
      return 0;
    f->lbuf = rl;
  }

  if (f->lbuf>sizeof(f->buf)) {
    printf("SSW Error: internal buffer too short\n");
    return 0;
  }
  char * buf = (char*)f->buf;
  if (!ssw_readbytes(f, buf, f->lbuf))
    return 0;
  if (f->reclen==4) {
    uint32_t rl;
    return ssw_readbytes(f, (char*)&rl, 4) && f->lbuf == rl;
  } else {
    uint64_t rl;
    return ssw_readbytes(f, (char*)&rl, 8) && f->lbuf == rl;
  }
}

void ssw_close_file(ssw_file_t ff) {
  SSW_FILEDECODE;
  if (!f)
    return;
  if (f->file) {
    fclose(f->file);
    f->file = 0;
  }
#ifdef SSWREAD_HASZLIB
  if (f->filegz) {
    gzclose(f->filegz);
    f->file = 0;
  }
#endif
  free(f);
}

void ssw_strip(char **str) {
  size_t l = strlen(*str);
  int i = 0;
  while ((*str)[i]==' ')
    ++i;
  if (i)
    memmove(*str,*str+i,l+1-i);
  i = l-i-1;
  while (i>=0&&(*str)[i]==' ') {
    (*str)[i]='\0';
    --i;
  }
}

ssw_file_t ssw_openerror(ssw_fileinternal_t * f, const char* msg) {
  if (f) {
    if (f->file)
      fclose(f->file);
#ifdef SSWREAD_HASZLIB
    if (f->filegz)
      gzclose(f->filegz);
#endif
    free(f);
  }
  ssw_error(msg);
  ssw_file_t out;
  out.internal = 0;
  return out;
}

ssw_file_t ssw_open_file(const char * filename)
{
  if (!filename)
    ssw_error("ssw_open_file called with null string");

  ssw_file_t out;
  out.internal = 0;

  ssw_fileinternal_t * f = (ssw_fileinternal_t*)calloc(sizeof(ssw_fileinternal_t),1);
  assert(f);

  //open file (with gzopen if filename ends with .gz):
  f->file = 0;
  f->filegz = 0;
  char * lastdot = strrchr(filename, '.');
  if (lastdot && strcmp(lastdot, ".gz") == 0) {
#ifdef SSWREAD_HASZLIB
    f->filegz = gzopen(filename,"rb");
    if (!f->filegz)
      ssw_error("Unable to open file!");
#else
    ssw_error("This installation of sswread was not built with zlib support and can not read compressed (.gz) files directly.");
#endif
  } else {
    f->file = fopen(filename,"rb");
    if (!f->file)
      ssw_error("Unable to open file!");
  }

  //Fortran data is usually written in "records" with an initial and final 32bit
  //or 64bit integer specifying the record byte-length. The known file-types
  //begin in one of the following ways:
  //
  // 1) 4B[163|167] + "mcnp" : MCNPX2.7.0 with 32bit reclen
  // 2) 8B[163|167] + "mcnp" : MCNPX2.7.0 with 64bit reclen
  // 3) 16B +4B[143] + "mcnp" : MCNP6 with 32bit reclen
  // 4) 24B +8B[143] + "mcnp" : MCNP6 with 64bit reclen
  //
  //Thus, we probe the first 36 bytes and see if we can find 4 chars spelling
  //out "mcnp" at the indicated positions, preceeded by an integer with the
  //correct value (143, 163 or 167 as indicated).

  char * buf = (char*)f->buf;
  ssw_readbytes(f,buf,36);

  f->reclen = 0;
  uint64_t lenrec0 = 99999;
  unsigned rec0begin = 0;
  f->is_mcnp6 = 0;
  if ( strncmp(buf+4,"mcnp",4) == 0 && (lenrec0=*((uint32_t*)buf)) >= 163 && lenrec0 <=167 ) {
    //case 1:
    f->reclen = 4;
    rec0begin = 4;
  } else if ( strncmp(buf+8,"mcnp",4) == 0 && (lenrec0=*((uint64_t*)buf)) >= 163 && lenrec0 <=167 ) {
    //case 2:
    f->reclen = 8;
    rec0begin = 8;
  } else if ( strncmp(buf+4+16,"mcnp",4) == 0 && (lenrec0=*((uint32_t*)(buf+16))) == 143 ) {
    //case 3:
    f->reclen = 4;
    rec0begin = 20;
    f->is_mcnp6 = 1;
  } else if ( strncmp(buf+8+24,"mcnp",4) == 0 && (lenrec0=*((uint64_t*)(buf+24))) == 143 ) {
    //case 4:
    f->reclen = 8;
    rec0begin = 32;
    f->is_mcnp6 = 1;
  }
  if (f->reclen==0||rec0begin==0||(lenrec0!=143&&lenrec0!=163&&lenrec0!=167)) {
    return ssw_openerror(f,"ssw_open_file error: File does not look like a supported mcnp .ssw file");
  }
  if (f->reclen==8)
    printf("ssw_open_file WARNING: 64bit Fortran records detected. This is untested.\n");

  //Finish reading the first record:
  int missingrec0 = (int)(lenrec0 + rec0begin) - (int)36 + f->reclen;
  assert(missingrec0>0);
  ssw_readbytes(f,buf+36,missingrec0);

  //Check final marker:
  uint64_t lenrec0_b;
  if (f->reclen==4)
    lenrec0_b = *((uint32_t*)(buf+(rec0begin+lenrec0)));
  else
    lenrec0_b = *((uint64_t*)(buf+(rec0begin+lenrec0)));
  if (lenrec0!=lenrec0_b)
    return ssw_openerror(f,"ssw_open_file error: Unexpected header contents\n");

  //decode first record, inspired by ssw.py:
  if (f->is_mcnp6) {
    char * r = buf + rec0begin;
    unsigned n;
    memcpy(f->kods,r, n=8); r += n;
    memcpy(f->vers,r, n=5); r += n;
    memcpy(f->lods,r, n=28); r += n;
    memcpy(f->idtms,r, n=18); r += n;
    memcpy(f->aids,r, n=80); r += n;
    f->probs[0]='\0';
  } else {
    assert(lenrec0==163||lenrec0==167);
    char * r = buf + f->reclen;
    unsigned n;
    memcpy(f->kods,r, n=8); r += n;
    memcpy(f->vers,r, n=5); r += n;
    memcpy(f->lods,r, n=28); r += n;
    memcpy(f->idtms,r, n=19); r += n;
    memcpy(f->probs,r, n=19); r += n;
    memcpy(f->aids,r, n=80); r += n;
  }
  char * tmp;
  tmp = f->kods; ssw_strip(&tmp);
  tmp = f->vers; ssw_strip(&tmp);
  tmp = f->lods; ssw_strip(&tmp);
  tmp = f->idtms; ssw_strip(&tmp);
  tmp = f->probs; ssw_strip(&tmp);
  tmp = f->aids; ssw_strip(&tmp);
  const char * bn = strrchr(filename, '/');
  bn = bn ? bn + 1 : filename;
  printf("ssw_open_file: Opened file    : %s\n",bn);

  if (strcmp(f->kods,"mcnp")!=0&&strcmp(f->kods,"mcnpx")!=0) {
    printf("ssw_open_file error: Unsupported source code name :\"%s\" (must be \"mcnp\" or \"mcnpx\")\n",f->kods);
    return ssw_openerror(f,"ssw_load error: Unsupported source code name");
  }

  printf("ssw_open_file: Detected code  : %s (v%s)\n",(f->is_mcnp6?"MCNP6":"MCNPX"),f->vers);
  printf("ssw_open_file: Detected title : \"%s\"\n",f->aids);
  /* printf("ssw_open_file: Found kods  = '%s'\n",f->kods); */
  /* printf("ssw_open_file: Found vers  = '%s'\n",f->vers); */
  /* printf("ssw_open_file: Found lods  = '%s'\n",f->lods); */
  /* printf("ssw_open_file: Found idtms = '%s'\n",f->idtms); */
  /* printf("ssw_open_file: Found probs = '%s'\n",f->probs); */
  /* printf("ssw_open_file: Found aids  = '%s'\n",f->aids); */

  if ( f->is_mcnp6 ) {
    if ( strcmp(f->vers,"6")!=0 ) {
      printf("ssw_open_file error: Unsupported MCNP6 source version :\"%s\" (must be \"6\")\n",f->vers);
      return ssw_openerror(f,"ssw_open_file error: Unsupported MCNP6 source version");
    }
  } else {
    if ( strcmp(f->vers,"2.6.0")!=0 && strcmp(f->vers,"2.7.0")!=0 && strcmp(f->vers,"26b")!=0 ) {
      printf("ssw_open_file error: Unsupported MCNPX source version :\"%s\" (must be \"2.7.0\", \"2.6.0\" or \"26b\")\n",f->vers);
      return ssw_openerror(f,"ssw_open_file error: Unsupported MCNPX source version");
    }
    if (strcmp(f->vers,"2.6.0")==0||strcmp(f->vers,"26b")==0)
      printf("ssw_open_file warning: Attempting to open MCNPX file with version %s. This is untested.\n",f->vers);
  }

  if (!ssw_loadrecord(f))
    return ssw_openerror(f,"ssw_open_file error: problems loading record");

  //Position of &buf[0] in file:
  long int current_recpos;
#ifdef SSWREAD_HASZLIB
  if (f->filegz)
    current_recpos = gztell(f->filegz);
  else
#endif
    current_recpos = ftell(f->file);

  current_recpos -= f->reclen;
  current_recpos -= f->lbuf;

  int32_t * bi = (int32_t*)f->buf;
  if ( f->is_mcnp6 && f->lbuf>=32 ) {
    f->np1 = bi[0];
    f->np1pos = current_recpos + 0 * sizeof(int32_t);
    f->nrss = bi[2];
    f->nrsspos = current_recpos + 2 * sizeof(int32_t);
    f->nrcd = abs(bi[4]);//not sure what negative bi[4] indicates?
    f->njsw = bi[5];//or... abs(bi[1])??
    f->niss = bi[6];//konstantin had bi[7] here...
  } else if (f->lbuf==20) {
    f->np1 = bi[0];
    f->np1pos = current_recpos + 0 * sizeof(int32_t);
    f->nrss = bi[1];
    f->nrsspos = current_recpos + 1 * sizeof(int32_t);
    f->nrcd = bi[2];
    f->njsw = bi[3];
    f->niss = bi[4];
  } else if (f->lbuf==40) {
    printf("ssw_open_file warning: Using untested code path..\n");
    f->np1 = bi[0];
    f->np1pos = current_recpos + 0 * sizeof(int32_t);
    f->nrss = bi[2];
    f->nrsspos = current_recpos + 2 * sizeof(int32_t);
    f->nrcd = bi[4];
    f->njsw = bi[6];
    f->niss = bi[8];
  } else {
    return ssw_openerror(f,"ssw_open_file error: Unexpected record length");
  }

  printf("ssw_open_file: Detected source statistics (histories): %11i\n" , abs(f->np1));
  printf("ssw_open_file: Detected particles in file            : %11i\n" , f->nrss);
  printf("ssw_open_file: Detected number of surfaces           : %11i\n" , f->njsw);
  printf("ssw_open_file: Detected histories at surfaces        : %11i\n" , f->niss);
  printf("ssw_open_file: Detected length of SSB array          : %11i\n" , f->nrcd);

  if(f->nrcd<10)
    return ssw_openerror(f,"ssw_open_file error: Too short SSB arrays in file.");//might be a configuration issue?
  if(f->nrcd>11)
    return ssw_openerror(f,"ssw_open_file error: Unexpected length of SSB arrays in file");

  if (f->is_mcnp6&&f->nrcd==10)
    return ssw_openerror(f,"ssw_open_file error: Unexpected length of SSB arrays in MCNP6 file");

  int32_t niwr = 0;
  if (f->np1==0)
    return ssw_openerror(f,"ssw_open_file error: File has 0 particle histories which should not be possible");

  if (f->np1<0) {//Sign is well-defined since f->np1!=0
    f->np1 = - f->np1;
    if (!ssw_loadrecord(f))
      return ssw_openerror(f,"ssw_open_file error: problems loading record");
    niwr = bi[0];
  }

  //skip over njsw + niwr + 1(mipts) records which we are not interested in:
  for (int i = 0; i < f->njsw+niwr+1; ++i) {
    if (!ssw_loadrecord(f))
      return ssw_openerror(f,"ssw_open_file error: problems loading record");
  }

#ifdef SSWREAD_HASZLIB
  if (f->filegz)
    f->headlen = gztell(f->filegz);
  else
#endif
    f->headlen = ftell(f->file);
  f->pos = 0;
  out.internal = f;
  return out;
}

//Query header info:
unsigned long ssw_nparticles(ssw_file_t ff) {
  SSW_FILEDECODE;
  return f->nrss;
}

const char* ssw_srcname(ssw_file_t ff) {
  SSW_FILEDECODE;
  return f->kods;
}

const char* ssw_srcversion(ssw_file_t ff) {
  SSW_FILEDECODE;
  return f->vers;
}

const char* ssw_title(ssw_file_t ff) {
  SSW_FILEDECODE;
  return f->aids;
}


int ssw_is_mcnp6(ssw_file_t ff) {
  SSW_FILEDECODE;
  return f->is_mcnp6;
}

int ssw_is_gzipped(ssw_file_t ff) {
  SSW_FILEDECODE;
#ifdef SSWREAD_HASZLIB
  if (f->filegz)
    return 1;
#endif
  return 0;
}

void ssw_layout(ssw_file_t ff, int* reclen, int* ssblen, int64_t* hdrlen, int64_t* np1pos, int64_t* nrsspos)
{
  SSW_FILEDECODE;
  *reclen = f->reclen;
  *ssblen = f->nrcd;
  *np1pos = f->np1pos;
  *nrsspos = f->nrsspos;
  *hdrlen = f->headlen;
}


//load next particle (null indicates eof):
const ssw_particle_t * ssw_load_particle(ssw_file_t ff)
{
  SSW_FILEDECODE;
  if (f->pos >= f->nrss)
    return 0;
  ++f->pos;

  if (!ssw_loadrecord(f)) {
    ssw_error("ssw_load error: problems loading record\n");
    return 0;
  }

  if (f->lbuf != (unsigned)8*f->nrcd) {
    ssw_error("ssw_load error: unexpected ssb data length");
    return 0;
  }

  double * ssb = (double*)f->buf;

  ssw_particle_t* p = &(f->part);

  p->weight = ssb[2];
  p->ekin = ssb[3];//MeV
  p->time = ssb[4];
  p->x = ssb[5];
  p->y = ssb[6];
  p->z = ssb[7];
  p->dirx = ssb[8];
  p->diry = ssb[9];
  int64_t nx = ssb[1];
  if (nx<0) nx = - nx;//sign is used for sign of dirz (see below)

  if (f->is_mcnp6) {
    assert(f->nrcd==11);
    p->isurf = labs((int32_t)ssb[10]);
    nx /= 4;//ignore two lowest bits, maybe used to indicate cell-source-particle and energy-group mode (??)
    p->rawtype = nx;
    p->pdgcode = conv_mcnp6_ssw2pdg(nx);
    if (!p->pdgcode)
      printf("ssw_load_particle WARNING: Could not convert raw MCNP6 SSW type (%li) to pdg code\n",(long)(p->rawtype));
  } else {
    p->isurf = nx % 1000000;
    p->rawtype = nx / 1000000;
    p->pdgcode = conv_mcnpx_ssw2pdg(p->rawtype);
    if (!p->pdgcode)
      printf("ssw_load_particle WARNING: Could not convert raw MCNPX SSW type (%li) to pdg code\n",(long)(p->rawtype));
  }

  p->dirz = sqrt(fmax(0.0, 1. - p->dirx*p->dirx-p->diry*p->diry));
  if (ssb[1]<0.0)
    p->dirz = - p->dirz;

  return p;

}

static int32_t conv_mcnpx_to_pdg_0to34[] = { 0, 2112, 22, 11, 13, 15, 12, 14, 16, 2212, 3122, 3222,
                                             3112, 3322, 3312, 3334, 4122, 4232, 4132, 5122, 211,
                                             111, 321, 310, 130, 411, 421, 431, 521, 511, 531,
                                             1000010020, 1000010030, 1000020030, 1000020040 };

static int32_t conv_mcnp6_to_pdg_0to36[] = { 0, 2112, 22, 11, 13, -2112, 12, 14, -11, 2212, 3122,
                                             3222, 3112, 3322, 3312, 3334, -13, -12, -14, -2212, 211,
                                             111, 321, 310, 130, -3122, -3222, -3112, -3322, -3312, -3334,
                                             1000010020, 1000010030, 1000020030, 1000020040, -211, -321 };

int32_t conv_mcnpx_ssw2pdg(int32_t c)
{
  if (c<0)
    return 0;
  if (c<=34)
    return conv_mcnpx_to_pdg_0to34[c];
  if (c>=401&&c<=434)
    return - conv_mcnpx_to_pdg_0to34[c%100];
  int32_t sign = 1;
  if (c%1000==435) {
    sign = -1;
    c -= 400;
  }
  if (c%1000==35) {
    //ion from MMMAAA035 where MMM = Z-1 to 100ZZZAAA0
    c /= 1000;
    long A = c%1000;
    if (!A)
      return 0;
    c /= 1000;
    if (c/1000)
      return 0;
    long ZM1 = c%1000;
    return sign * (1000000000 + (ZM1+1)*10000 + A*10);
  }
  return 0;
}

int32_t conv_mcnp6_ssw2pdg(int32_t c)
{
  if (c<0)
    return 0;
  int antibit = c%2;  c /=  2;
  int ptype = c%64;  c /=  64;

  if (ptype<=36) {
    //Note that A (see below) has been observed in SSW files to have non-zero
    //values for ptype<37 as well, so don't require A, Z or S to be 0 here.
    int32_t p = conv_mcnp6_to_pdg_0to36[ptype];
    return antibit ? -p : p;
  }
  if (ptype==37) {
    int A = c%512;  c /=  512;
    int Z = c%128;  c /=  128;
    int S = c;
    if (A<1||Z<1||A<Z||S>9)
      return 0;
    int32_t p = 1000000000 + 10000*Z + 10*A + S;
    return antibit ? -p : p;
  }
  return 0;
}

int32_t conv_mcnpx_pdg2ssw(int32_t c)
{
  int32_t absc = c < 0 ? -c : c;
  if (absc <= 1000020040) {
    for (int i = 0; i<35; ++i) {
      if (conv_mcnpx_to_pdg_0to34[i]==c)
        return i;
    }
    for (int i = 0; i<35; ++i) {
      if (conv_mcnpx_to_pdg_0to34[i] == -c)
        return 400+i;
    }
  }
  if (absc>1000000000&&absc<=1009999990) {
    //Ions. PDG format for ions is 10LZZZAAAI, where L!=0 indicates strangeness
    //and I!=0 indicates exited nuclei. We only allow L=I=0 ions here.
    int32_t I = absc % 10;//isomer level
    absc/=10;
    int32_t A = absc%1000;
    absc/=1000;
    int32_t Z = absc % 1000;
    assert(absc/1000==100);//L=0 guaranteed by enclosing condition.
    if ( I || !A || !Z || Z>A )
      return 0;
    return (Z-1)*1000000 + A*1000 + ( c<0 ? 435 : 35 );
  }
  return 0;
}

int32_t conv_mcnp6_pdg2ssw(int32_t c)
{
  int32_t absc = c < 0 ? -c : c;
  if (absc <= 1000020040) {
    if (c==-11)
      return 7;//e+ is special case, pick 7 (anti e-) rather than 16 (straight e+)
    for (int i = 0; i<37; ++i) {
      if (conv_mcnp6_to_pdg_0to36[i]==c)
        return 2*i;
    }
    for (int i = 0; i<37; ++i) {
      if (conv_mcnp6_to_pdg_0to36[i] == -c)
        return 1 + 2*i;
    }
  }

  if (absc>1000000000&&absc<=1009999990) {
    //Ions. PDG format for ions is 10LZZZAAAI, where L!=0 indicates strangeness
    //and I!=0 indicates exited nuclei. We only allow L=0 ions here.
    int32_t I = absc % 10;//isomer level
    absc/=10;
    int32_t A = absc%1000;
    absc/=1000;
    int32_t Z = absc % 1000;
    assert(absc/1000==100);//L=0 guaranteed by enclosing condition.
    if ( !A || !Z || Z>A )
      return 0;
    int32_t res = (c<0?1:0);
    res += 2*37;
    res += 128*A;
    res += 128*512*Z;
    res += 128*512*128*I;
    return res;
  }
  return 0;
}
