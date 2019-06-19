
/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
//  sswread : Code for reading SSW files from MCNP(X)                              //
//                                                                                 //
//                                                                                 //
//  Compilation of sswread.c can proceed via any compliant C-compiler using        //
//  -std=c99 or later, and the resulting code must always be linked with libm      //
//  (using -lm). Furthermore, the following preprocessor flags can be used         //
//  when compiling sswread.c to fine tune the build process and the                //
//  capabilities of the resulting binary.                                          //
//                                                                                 //
//  SSWREAD_HASZLIB : Define if compiling and linking with zlib, to allow direct   //
//                    reading of gzipped SSW files.                                //
//  SSWREAD_ZLIB_INCPATH : Specify alternative value if the zlib header is not to  //
//                         be included as "zlib.h".                                //
//  SSWREAD_HDR_INCPATH : Specify alternative value if the sswread header itself   //
//                        is not to be included as "sswread.h".                    //
//                                                                                 //
// This file can be freely used as per the terms in the LICENSE file.              //
//                                                                                 //
// However, note that usage of MCNP(X)-related utilities might require additional  //
// permissions and licenses from third-parties, which is not within the scope of   //
// the MCPL project itself.                                                        //
//                                                                                 //
// Written 2015-2017, thomas.kittelmann@esss.se (European Spallation Source).      //
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


//Should be large enough to hold first record in all supported files:
#define SSWREAD_STDBUFSIZE 1024

#define SSW_MCNP_NOTFOUND 0
#define SSW_MCNP6 1
#define SSW_MCNPX 2
#define SSW_MCNP5 3

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
  char aids[129];  // Creation-Run Problem-Title-Card
  int32_t np1;
  int32_t nrss;
  int32_t njsw;
  int32_t nrcd;
  int32_t niss;
  int32_t pos;
  int mcnp_type;
#ifdef SSWREAD_HASZLIB
  gzFile filegz;
#else
  void * filegz;
#endif
  FILE * file;
  ssw_particle_t part;
  unsigned lbuf;
  unsigned lbufmax;
  char * buf;
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

  if (f->lbuf > f->lbufmax) {
    //Very large record, must grow buffer:
    free(f->buf);
    f->lbufmax = f->lbuf;
    f->buf = malloc(f->lbufmax);
  }

  if ( f->lbuf <= SSWREAD_STDBUFSIZE
       && f->lbufmax > SSWREAD_STDBUFSIZE ) {
    //Make sure we don't hold on to very large buffers once they are no longer
    //needed:
    free(f->buf);
    f->lbufmax = SSWREAD_STDBUFSIZE;
    f->buf = malloc(f->lbufmax);
  }

  if (!f->buf) {
    //Could be corrupted data resulting in unusually large lbuf:
    printf("SSW Error: unable to allocate requested buffer (corrupted input?).\n");
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
  free(f->buf);
  free(f);
  ff.internal = 0;
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
    free(f->buf);
    free(f);
  }
  ssw_error(msg);
  ssw_file_t out;
  out.internal = 0;
  return out;
}

//NB: Do not change function signature without updating code in sswmcpl.c as well!
void ssw_internal_grabhdr( const char * filename, int is_gzip, int64_t hdrlen,
                           unsigned char * hdrbuf )
{
  //To be used by mcpl2ssw, but we don't want to complicate the build process
  //for users further by also requiring sswmcpl.c to deal with zlib
  //directly. Thus, we provide a hidden function here which mcpl2ssw can use by
  //forward declaring it.
  if (is_gzip) {
#ifdef SSWREAD_HASZLIB
    gzFile filegz = gzopen(filename,"rb");
    if (!filegz)
      ssw_error("Unable to open file!");
    int64_t pos = 0;
    int64_t toread = hdrlen;
    while(toread) {
      int chunk = (hdrlen>16384?16384:(int)hdrlen);
      int nb = gzread(filegz, hdrbuf+pos, chunk);
      if (!nb)
        printf("SSW Error: read failure\n");
      assert(toread >= nb);
      toread -= nb;
      pos += nb;
    }
    gzclose(filegz);
#else
    ssw_error("This installation was not built with zlib support and can not read compressed (.gz) files directly.");
#endif
  } else {
    FILE * fh = fopen(filename,"rb");
    if (!fh)
      ssw_error("Unable to open file!\n");
    int64_t pos = 0;
    int64_t toread = hdrlen;
    while(toread) {
      int chunk = (hdrlen>16384?16384:(int)hdrlen);
      int nb = fread(hdrbuf+pos,1,chunk,fh);
      if (!nb)
        printf("SSW Error: read failure\n");
      assert(toread >= nb);
      toread -= nb;
      pos += nb;
    }
    fclose(fh);
  }
}

ssw_file_t ssw_open_and_procrec0( const char * filename )
{
  ssw_fileinternal_t * f = (ssw_fileinternal_t*)calloc(sizeof(ssw_fileinternal_t),1);
  assert(f);

  ssw_file_t out;
  out.internal = f;

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
    ssw_error("This installation was not built with zlib support and can not read compressed (.gz) files directly.");
#endif
  } else {
    f->file = fopen(filename,"rb");
    if (!f->file)
      ssw_error("Unable to open file!");
  }

  //Prepare buffer. SSWREAD_STDBUFSIZE bytes should always be enough for the
  //first record (guaranteed by the checks below), but it might later grow on
  //demand inside ssw_loadrecord if needed.

  f->lbufmax = SSWREAD_STDBUFSIZE;
  char * buf = malloc(f->lbufmax);
  f->buf = buf;

  //Fortran data is usually written in "records" with an initial and final 32bit
  //or 64bit integer specifying the record byte-length. The tested file-types
  //begin in one of the following ways:
  //
  // 1) 4B[163|167] + KODS : MCNPX2.7.0 with 32bit reclen
  // 2) 8B[163|167] + KODS : MCNPX2.7.0 with 64bit reclen
  // 3) 16B +4B[143 or 191] + KODS : MCNP6 with 32bit reclen
  // 4) 24B +8B[143 or 191] + KODS : MCNP6 with 64bit reclen
  // 5) 4B[143]+KODS : MCNP5 with 32bit reclen.
  // 6) 8B[143]+KODS : MCNP5 with 64bit reclen.
  //
  //Where KODS is 8 bytes representing the "code name" as a string. For pure
  //MCNPX/MCNP6 this string contains "mcnpx" and "mcnp" respectively, but we
  //should allow for custom in-house versions with modified contents of KODS. We
  //do, however, require that the first character or KODS is an ASCII character
  //in the range 32-126 (i.e. non-extended ascii without control or null chars).
  //
  //Note that for option 3) and 4), the second record can have a length of
  //either 143 (MCNP 6.0) or 191 (MCNP 6.2), since the "aids" field increased in
  //size from 80 to 128 chars.
  //
  //Note that for option 3) and 4), the 16B / 24B are a fortran record with 8
  //bytes of data - usually (always?) the string "SF_00001".

  //Thus, we probe the first 36 bytes and search the patterns above:

  ssw_readbytes(f,buf,36);
  uint32_t first32 = *((uint32_t*)buf);
  uint32_t first64 = *((uint64_t*)buf);

  f->reclen = 0;
  f->mcnp_type = SSW_MCNP_NOTFOUND;
  uint64_t lenrec0 = 99999;
  unsigned rec0begin = 0;

  //First look for MCNP6:
  unsigned mcnp6_lenaids = 80;
  if ( first32==8 && *((uint32_t*)(buf+12))==8 && (*((uint32_t*)(buf+16))==143||*((uint32_t*)(buf+16))==191) && buf[20]>=32 && buf[20]<127) {
    //Looks like 3), an mcnp6 file with 32bit fortran records.
    f->mcnp_type = SSW_MCNP6;
    f->reclen = 4;
    lenrec0 = *((uint32_t*)(buf+16));
    rec0begin = 20;
    if (*((uint32_t*)(buf+16))==191)
      mcnp6_lenaids = 128;
  } else if ( first32==8 && *((uint64_t*)(buf+16))==8 && (*((uint64_t*)(buf+24))==143||*((uint64_t*)(buf+24))==191) && buf[32]>=32 && buf[32]<127) {
    //Looks like 4), an mcnp6 file with 64bit fortran records.
    f->mcnp_type = SSW_MCNP6;
    f->reclen = 8;
    lenrec0 = *((uint64_t*)(buf+24));
    rec0begin = 32;
    if (*((uint64_t*)(buf+24))==191)
      mcnp6_lenaids = 128;
  }

  //Next, look for MCNPX:
  if ( f->mcnp_type == SSW_MCNP_NOTFOUND ) {
    if ( (first32==163||first32==167) && ( buf[4]>=32 && buf[4]<127 ) ) {
      //Looks like 1), an mcnpx file with 32bit fortran records.
      f->mcnp_type = SSW_MCNPX;
      f->reclen = 4;
      lenrec0 = first32;
      rec0begin = 4;
    } else if ( (first64==163||first64==167) && ( buf[8]>=32 && buf[8]<127 ) ) {
      //Looks like 2), an mcnpx file with 64bit fortran records.
      f->mcnp_type = SSW_MCNPX;
      f->reclen = 8;
      lenrec0 = first64;
      rec0begin = 8;
    }
  }

  //Finally, look for MCNP5:
  if ( f->mcnp_type == SSW_MCNP_NOTFOUND ) {
    if ( first32==143 && ( buf[4]>=32 && buf[4]<127 ) ) {
      //Looks like 5), an mcnp5 file with 32bit fortran records.
      f->mcnp_type = SSW_MCNP5;
      f->reclen = 4;
      lenrec0 = first32;
      rec0begin = 4;
    } else if ( first64==143 && ( buf[8]>=32 && buf[8]<127 ) ) {
      //Looks like 6), an mcnp5 file with 64bit fortran records.
      f->mcnp_type = SSW_MCNP5;
      f->reclen = 8;
      lenrec0 = first64;
      rec0begin = 8;
    }
  }

  if ( f->mcnp_type == SSW_MCNP_NOTFOUND )
    return ssw_openerror(f,"ssw_open_file error: File does not look like a supported MCNP SSW file");

  assert(f->reclen && rec0begin && lenrec0 && lenrec0<99999 );

  if (f->reclen==8) {
    printf("ssw_open_file WARNING: 64bit Fortran records detected which is untested (feedback"
           " appreciated at https://mctools.github.io/mcpl/contact/).\n");
  }

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
  if (f->mcnp_type == SSW_MCNP6) {
    char * r = buf + rec0begin;
    unsigned n;
    memcpy(f->kods,r, n=8); r += n;
    memcpy(f->vers,r, n=5); r += n;
    memcpy(f->lods,r, n=28); r += n;
    memcpy(f->idtms,r, n=18); r += n;
    memcpy(f->aids,r, n=mcnp6_lenaids);
    f->probs[0]='\0';
  } else if (f->mcnp_type == SSW_MCNPX) {
    assert(lenrec0==163||lenrec0==167);
    char * r = buf + f->reclen;
    unsigned n;
    memcpy(f->kods,r, n=8); r += n;
    memcpy(f->vers,r, n=5); r += n;
    memcpy(f->lods,r, n=28); r += n;
    memcpy(f->idtms,r, n=19); r += n;
    memcpy(f->probs,r, n=19); r += n;
    memcpy(f->aids,r, n=80);
  } else {
    assert(f->mcnp_type == SSW_MCNP5);
    assert(lenrec0==143);
    char * r = buf + f->reclen;
    unsigned n;
    memcpy(f->kods,r, n=8); r += n;
    memcpy(f->vers,r, n=5); r += n;
    memcpy(f->lods,r, n=8); r += n;
    memcpy(f->idtms,r, n=19); r += n;
    memcpy(f->probs,r, n=19); r += n;
    memcpy(f->aids,r, n=80);
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

  printf("ssw_open_file: Opened file \"%s\":\n",bn);

  const char * expected_kods = (f->mcnp_type == SSW_MCNPX?"mcnpx":"mcnp");
  if (strcmp(f->kods,expected_kods)!=0) {
    printf("ssw_open_file WARNING: Unusual MCNP flavour detected (\"%s\").\n",f->kods);
  }

  if (f->mcnp_type==SSW_MCNP6) {
    if ( strcmp(f->vers,"6")!=0 && strcmp(f->vers,"6.mpi")!=0 ) {
      printf("ssw_open_file WARNING: Untested MCNP6 source version : \"%s\". (feedback"
             " appreciated at https://mctools.github.io/mcpl/contact/)\n",f->vers);
    }
  } else if (f->mcnp_type==SSW_MCNPX) {
    if ( strcmp(f->vers,"2.5.0")!=0 && strcmp(f->vers,"2.6.0")!=0
         && strcmp(f->vers,"2.7.0")!=0 && strcmp(f->vers,"26b")!=0 )
      printf("ssw_open_file WARNING: Untested MCNPX source version : \"%s\". (feedback"
             " appreciated at https://mctools.github.io/mcpl/contact/)\n",f->vers);
  } else if (f->mcnp_type==SSW_MCNP5) {
    if ( strcmp(f->vers,"5")!=0 )
      printf("ssw_open_file WARNING: Untested MCNP5 source version : \"%s\". (feedback"
             " appreciated at https://mctools.github.io/mcpl/contact/)\n",f->vers);
  }

  return out;
}
ssw_file_t ssw_open_file( const char * filename )
{
  if (!filename)
    ssw_error("ssw_open_file called with null string for filename");

  //Open, classify and process first record with mcnp type and version info:

  ssw_file_t out = ssw_open_and_procrec0( filename );
  ssw_fileinternal_t * f = (ssw_fileinternal_t *)out.internal; assert(f);

  //Skip a record:
  if (!ssw_loadrecord(f))
    return ssw_openerror(f,"ssw_open_file error: problems loading record");

  //Position of current record payload in file:
  long int current_recpos;
#ifdef SSWREAD_HASZLIB
  if (f->filegz)
    current_recpos = gztell(f->filegz);
  else
#endif
    current_recpos = ftell(f->file);
  current_recpos -= f->reclen;
  current_recpos -= f->lbuf;

  //Read size data and mark position of nrss & np1 variables.
  int32_t * bi = (int32_t*)f->buf;
  if ( (f->mcnp_type == SSW_MCNP6) && f->lbuf>=32 ) {
    f->np1 = bi[0];
    f->np1pos = current_recpos + 0 * sizeof(int32_t);
    f->nrss = bi[2];
    f->nrsspos = current_recpos + 2 * sizeof(int32_t);
    f->nrcd = abs(bi[4]);
    f->njsw = bi[5];
    f->niss = bi[6];
  } else if ( (f->mcnp_type == SSW_MCNPX) && f->lbuf==20 ) {
    f->np1 = bi[0];
    f->np1pos = current_recpos + 0 * sizeof(int32_t);
    f->nrss = bi[1];
    f->nrsspos = current_recpos + 1 * sizeof(int32_t);
    f->nrcd = bi[2];
    f->njsw = bi[3];
    f->niss = bi[4];
  } else if ( (f->mcnp_type == SSW_MCNP5) && f->lbuf==32 ) {
    int64_t np1_64 = ((int64_t*)f->buf)[0];
    if (np1_64 > 2147483647 || np1_64 < -2147483647)
      return ssw_openerror(f,"ssw_open_file error: MCNP5 files with more than 2147483647"
                           " histories are not supported");
    f->np1 = (int32_t)np1_64;
    f->np1pos = current_recpos + 0 * sizeof(int64_t);
    uint64_t nrss_64 = ((uint64_t*)f->buf)[1];
    if (nrss_64 > 2147483647 )
      return ssw_openerror(f,"ssw_open_file error: MCNP5 files with more than 2147483647"
                           " particles are not supported");
    f->nrss = (int32_t)nrss_64;
    f->nrsspos = current_recpos + 1 * sizeof(int64_t);
    f->nrcd = bi[4];
    f->njsw = bi[5];
    f->niss = bi[6];
  } else if (f->lbuf==40) {
    printf("ssw_open_file WARNING: File format has header format for which decoding was never tested (feedback"
           " appreciated at https://mctools.github.io/mcpl/contact/).\n");
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

  printf("ssw_open_file:    File layout detected : %s\n",ssw_mcnpflavour(out));
  printf("ssw_open_file:    Code ID fields : \"%s\" / \"%s\"\n",f->kods,f->vers);
  printf("ssw_open_file:    Title field : \"%s\"\n",f->aids);
  /* printf("ssw_open_file: Found kods  = '%s'\n",f->kods); */
  /* printf("ssw_open_file: Found vers  = '%s'\n",f->vers); */
  /* printf("ssw_open_file: Found lods  = '%s'\n",f->lods); */
  /* printf("ssw_open_file: Found idtms = '%s'\n",f->idtms); */
  /* printf("ssw_open_file: Found probs = '%s'\n",f->probs); */
  /* printf("ssw_open_file: Found aids  = '%s'\n",f->aids); */
  printf("ssw_open_file:    Source statistics (histories): %11i\n" , abs(f->np1));
  printf("ssw_open_file:    Particles in file            : %11i\n" , f->nrss);
  printf("ssw_open_file:    Number of surfaces           : %11i\n" , f->njsw);
  printf("ssw_open_file:    Histories at surfaces        : %11i\n" , f->niss);
  //  printf("ssw_open_file: File length of SSB array          : %11i\n" , f->nrcd);

  if(f->nrcd==6)
    return ssw_openerror(f,"ssw_open_file error: SSW files with spherical sources are not currently supported.");
  if(f->nrcd<10)
    return ssw_openerror(f,"ssw_open_file error: Too short SSB arrays in file");
  if(f->nrcd>11)
    return ssw_openerror(f,"ssw_open_file error: Unexpected length of SSB arrays in file");

  if ( (f->mcnp_type == SSW_MCNP6) && f->nrcd==10 )
    return ssw_openerror(f,"ssw_open_file error: Unexpected length of SSB arrays in MCNP6 file");

  int32_t niwr = 0;
  if (f->np1==0)
    return ssw_openerror(f,"ssw_open_file error: File has 0 particle histories which should not be possible");

  if (f->np1<0) {//Sign is well-defined since f->np1!=0
    f->np1 = - f->np1;
    if (!ssw_loadrecord(f))
      return ssw_openerror(f,"ssw_open_file error: problems loading record");
    niwr = bi[0];
    //mipts = bi[1];//source particle type
    //kjaq  = bi[2];//macrobody facet flag
  }

  //skip over njsw + niwr + 1 records which we are not interested in:
  int i;
  for (i = 0; i < f->njsw+niwr+1; ++i) {
    if (!ssw_loadrecord(f))
      return ssw_openerror(f,"ssw_open_file error: problems loading record");
  }

  //End of header? Mark the position:
  f->pos = 0;
#ifdef SSWREAD_HASZLIB
  if (f->filegz)
    f->headlen = gztell(f->filegz);
  else
#endif
    f->headlen = ftell(f->file);

  //Check that it was really the end of the header by preloading the next
  //record(s) and checking if the length corresponds to that of particle data
  //(NB: ssw_load_particle knows that the particle at position 0 will have
  //already been loaded by these checks). See also
  //https://github.com/mctools/mcpl/issues/45:
  unsigned nmaxunexpected = 3;
  while ( nmaxunexpected-- > 0 ) {
    if (!ssw_loadrecord(f)) {
      //For files with 0 particles, we assume (this is not guaranteed of
      //course!) that the failure is due to EOF:
      if (f->nrss==0)
        break;
      //But this is certainly an error for files with >0 particles:
      return ssw_openerror(f,"ssw_open_file error: problems loading record");
    }
    if ( f->nrss > 0 && f->lbuf == (unsigned)8*f->nrcd ) {
      //Looks like we preloaded the first particle of the file!
      break;
    } else {
      //Looks like this could not be a particle, so we interpret this as if the
      //header was actually one record longer than previously thought:
      f->headlen += f->reclen * 2 + f->lbuf;
      printf("ssw_open_file WARNING: Unexpected %i byte record encountered at end of header. Continuing under the assumption it contains valid configuration data.\n",f->lbuf);

    }
  }

  //Return handle:
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
  return f->mcnp_type == SSW_MCNP6;
}

int ssw_is_mcnpx(ssw_file_t ff) {
  SSW_FILEDECODE;
  return f->mcnp_type == SSW_MCNPX;
}

int ssw_is_mcnp5(ssw_file_t ff) {
  SSW_FILEDECODE;
  return f->mcnp_type == SSW_MCNP5;
}

const char * ssw_mcnpflavour(ssw_file_t ff) {
  SSW_FILEDECODE;
  switch(f->mcnp_type) {
  case SSW_MCNP5: return "MCNP5";
  case SSW_MCNP6: return "MCNP6";
  case SSW_MCNPX: return "MCNPX";
  default:
    ssw_error("ssw_mcnpflavour: logic error.\n");
  }
  return "MCNP_logic_error";
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

  //The record of the first particle in the file is always pre-loaded during
  //initialisation, for the others we must consume another record:
  if ( f->pos > 1 && !ssw_loadrecord(f) ) {
    ssw_error("ssw_load error: problems loading particle record\n");
    return 0;
  }

  if (f->lbuf != (unsigned)8*f->nrcd) {
    ssw_error("ssw_load error: unexpected particle data length");
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

  if ( f->mcnp_type == SSW_MCNP6 ) {
    assert(f->nrcd==11);
    p->isurf = labs((int32_t)ssb[10]);
    nx /= 4;//ignore two lowest bits, maybe used to indicate cell-source-particle and energy-group mode (??)
    p->rawtype = nx;
    p->pdgcode = conv_mcnp6_ssw2pdg(nx);
    if (!p->pdgcode)
      printf("ssw_load_particle WARNING: Could not convert raw MCNP6 SSW type (%li) to pdg code\n",(long)(p->rawtype));
  } else if ( f->mcnp_type == SSW_MCNPX ) {
    p->isurf = nx % 1000000;
    p->rawtype = nx / 1000000;
    p->pdgcode = conv_mcnpx_ssw2pdg(p->rawtype);
    if (!p->pdgcode)
      printf("ssw_load_particle WARNING: Could not convert raw MCNPX SSW type (%li) to pdg code\n",(long)(p->rawtype));
  } else {
    assert( f->mcnp_type == SSW_MCNP5 );
    nx /= 8;//Guess: Get rid of some bits that might be used for something else
    p->isurf = nx % 1000000;
    p->rawtype = nx / 1000000;
    p->rawtype /= 100;//Guess: Get rid of some "bits" that might be used for something else
    p->pdgcode = (p->rawtype==1?2112:(p->rawtype==2?22:0));//only neutrons and gammas in MCNP5
    if (!p->pdgcode)
      printf("ssw_load_particle WARNING: Could not convert raw MCNP5 SSW type (%li) to pdg code\n",(long)(p->rawtype));
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

int32_t conv_mcnpx_ssw2pdg( int32_t c )
{
  if (c<0)
    return 0;
  if (c<=34)
    return conv_mcnpx_to_pdg_0to34[c];
  if (c>=401&&c<=434)
    return c==402 ? 22 : - conv_mcnpx_to_pdg_0to34[c%100];
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
  //Retry without non-type related parts:
  int j = (c%1000)/100;
  if (j==2||j==6)
    return conv_mcnpx_ssw2pdg(c-200);
  return 0;
}

int32_t conv_mcnp6_ssw2pdg( int32_t c )
{
  if (c<0)
    return 0;
  int antibit = c%2;  c /=  2;
  int ptype = c%64;  c /=  64;

  if (ptype<=36) {
    //Note that A (see below) has been observed in SSW files to have non-zero
    //values for ptype<37 as well, so don't require A, Z or S to be 0 here.
    int32_t p = conv_mcnp6_to_pdg_0to36[ptype];
    return (antibit&&p!=22) ? -p : p;
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

int32_t conv_mcnpx_pdg2ssw( int32_t c )
{
  int32_t absc = c < 0 ? -c : c;
  if (absc <= 1000020040) {
    int i;
    for (i = 0; i<35; ++i) {
      if (conv_mcnpx_to_pdg_0to34[i]==c)
        return i;
    }
    for (i = 0; i<35; ++i) {
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

int32_t conv_mcnp6_pdg2ssw( int32_t c )
{
  int32_t absc = c < 0 ? -c : c;
  if (absc <= 1000020040) {
    if (c==-11)
      return 7;//e+ is special case, pick 7 (anti e-) rather than 16 (straight e+)
    int i;
    for (i = 0; i<37; ++i) {
      if (conv_mcnp6_to_pdg_0to36[i]==c)
        return 2*i;
    }
    for (i = 0; i<37; ++i) {
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
