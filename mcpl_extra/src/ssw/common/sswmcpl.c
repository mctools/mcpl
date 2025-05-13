
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
//  sswmcpl : Code for converting between MCPL and SSW files from MCNP(X).    //
//                                                                            //
//  Compilation of sswmcpl.c can proceed via any compliant C-compiler using   //
//  -std=c99 later.                                                           //
//                                                                            //
// Note that usage of MCNP(X)-related utilities might require additional      //
// permissions and licenses from third-parties, which is not within the       //
// scope of the MCPL project itself.                                          //
//                                                                            //
// Written 2015-2025, thomas.kittelmann@ess.eu (European Spallation Source).  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "sswmcpl.h"
#include "sswread.h"
#include "mcpl.h"

#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>
#include <assert.h>

void ssw_error(const char * msg);//fwd declare internal function from sswread.c


int ssw2mcpl(const char * sswfile, const char * mcplfile)
{
  return ssw2mcpl2(sswfile, mcplfile, 0, 0, 1, 0);
}

size_t ssw_strlen( const char * str, size_t maxsize )
{
  const char * nullchr = (const char *) memchr( str, '\0', maxsize );
  if ( !nullchr || (size_t)(nullchr-str) >= maxsize )
    ssw_error("ssw_strlen: could not calculate valid string length");
  return (size_t)(nullchr-str);
}

void ssw_strcat( char * dest, const char * src, size_t destbuflen )
{
  size_t nd = ssw_strlen( dest, destbuflen );
  size_t ns = ssw_strlen( src, destbuflen );
  size_t n = nd + ns;
  if (!ns)
    return;
  if ( n < nd || n < ns || n > destbuflen )
    ssw_error("ssw_strcat: resulting string size out of range");
  memcpy( dest + nd, src, ns+1 );
}

int ssw2mcpl2(const char * sswfile, const char * mcplfile,
              int opt_dp, int opt_surf, int opt_gzip,
              const char * inputdeckfile)
{
  ssw_file_t f = ssw_open_file(sswfile);
  mcpl_outfile_t mcplfh = mcpl_create_outfile(mcplfile);
  mcpl_hdr_set_srcname(mcplfh,ssw_mcnpflavour(f));
  const int32_t np1 = ssw_abs_np1( f );

  size_t lstrbuf = 1024;
  lstrbuf += strlen(ssw_srcname(f));
  lstrbuf += strlen(ssw_srcversion(f));
  lstrbuf += strlen(ssw_title(f));
  if (lstrbuf<4096) {
    char * buf = (char*)malloc(lstrbuf);
    if (!buf)
      ssw_error("memory allocation failure");
    buf[0] = '\0';
    ssw_strcat(buf,"SSW file from ",lstrbuf);
    ssw_strcat(buf,ssw_mcnpflavour(f),lstrbuf);
    ssw_strcat(buf," converted with ssw2mcpl",lstrbuf);
    mcpl_hdr_add_comment(mcplfh,buf);

    buf[0] = '\0';
    ssw_strcat(buf,"SSW metadata: [kods='",lstrbuf);
    ssw_strcat(buf,ssw_srcname(f),lstrbuf);
    ssw_strcat(buf,"', vers='",lstrbuf);
    ssw_strcat(buf,ssw_srcversion(f),lstrbuf);
    ssw_strcat(buf,"', title='",lstrbuf);
    ssw_strcat(buf,ssw_title(f),lstrbuf);
    ssw_strcat(buf,"']",lstrbuf);
    mcpl_hdr_add_comment(mcplfh,buf);
    free(buf);
  } else {
    mcpl_hdr_add_comment(mcplfh,"SSW metadata: <too long so not stored>");
  }
  if (opt_surf) {
    mcpl_hdr_add_comment(mcplfh,"The userflags in this file are the surface IDs found in the SSW file");
    mcpl_enable_userflags(mcplfh);
  }
  if (opt_dp) {
    mcpl_enable_doubleprec(mcplfh);
  }

  mcpl_hdr_add_stat_sum(mcplfh,"ssw_np1",-1.0);

  if (inputdeckfile) {
    char* cfgfile_buf;
    uint64_t cfgfile_lbuf;
    mcpl_read_file_to_buffer( inputdeckfile,
                              104857600,//100mb is beyond enough and within than
                                        //32bit integer reach.
                              1,//must be text
                              &cfgfile_lbuf,
                              &cfgfile_buf );
    /* if (!sswmcpl_file2buf(inputdeckfile, &cfgfile_buf, &cfgfile_lbuf, 104857600, 1)) */
    /*   return 0; */
    if (!strstr((const char*)cfgfile_buf, ssw_title(f))) {
      printf("Error: specified configuration file %s does not contain title"
             " found in ssw file: \"%s\".\n",inputdeckfile,ssw_title(f));
      return 0;
    }
    mcpl_hdr_add_data(mcplfh, "mcnp_input_deck",
                      (uint32_t)cfgfile_lbuf,
                      cfgfile_buf);
    free(cfgfile_buf);
  }

  mcpl_particle_t mcpl_particle;
  memset(&mcpl_particle,0,sizeof(mcpl_particle));

  while ( 1 ) {
    const ssw_particle_t * p = ssw_load_particle(f);
    if (!p)
      break;
    mcpl_particle.pdgcode = p->pdgcode;
    if (!mcpl_particle.pdgcode) {
      printf("Warning: ignored particle with no PDG code set (raw ssw type was %li).\n",p->rawtype);
      continue;
    }

    mcpl_particle.position[0] = p->x;//already in cm
    mcpl_particle.position[1] = p->y;//already in cm
    mcpl_particle.position[2] = p->z;//already in cm
    mcpl_particle.direction[0] = p->dirx;
    mcpl_particle.direction[1] = p->diry;
    mcpl_particle.direction[2] = p->dirz;
    mcpl_particle.time = p->time * 1.0e-5;//"shakes" to milliseconds
    mcpl_particle.weight = p->weight;
    mcpl_particle.ekin = p->ekin;//already in MeV
    mcpl_particle.userflags = p->isurf;

    mcpl_add_particle(mcplfh,&mcpl_particle);

  }

  const char * tmp = mcpl_outfile_filename(mcplfh);
  size_t laf = strlen(tmp);
  char * actual_filename = malloc(laf+1);
  if (!actual_filename)
    ssw_error("memory allocation failure");
  actual_filename[0]='\0';
  ssw_strcat(actual_filename,tmp,laf+1);

  if ( np1 > 0 )
    mcpl_hdr_add_stat_sum(mcplfh,"ssw_np1",(double)np1);

  int did_gzip = 0;
  if (opt_gzip)
    did_gzip = mcpl_closeandgzip_outfile(mcplfh);
  else
    mcpl_close_outfile(mcplfh);
  ssw_close_file(f);

  printf("Created %s%s\n",actual_filename,(did_gzip?".gz":""));
  free(actual_filename);
  return 1;
}

void ssw2mcpl_parse_args(int argc,char **argv, const char** infile,
                         const char **outfile, const char **cfgfile,
                         int* double_prec, int* surface_info, int* do_gzip) {
  *cfgfile = 0;
  *infile = 0;
  *outfile = 0;
  *surface_info = 0;
  *double_prec = 0;
  *do_gzip = 1;
  int i;
  for (i=1; i < argc; ++i) {
    if (argv[i][0]=='\0')
      continue;
    if (strcmp(argv[i],"-h")==0||strcmp(argv[i],"--help")==0) {
      char * progname = mcpl_usage_progname(argv[0]);
      printf("Usage:\n\n");
      printf("  %s [options] input.ssw [output.mcpl]\n\n",progname);
      printf("Converts the Monte Carlo particles in the input.ssw file (MCNP Surface\n"
             "Source Write format) to MCPL format and stores in the designated output\n"
             "file (defaults to \"output.mcpl\").\n"
             "\n"
             "Options:\n"
             "\n"
             "  -h, --help   : Show this usage information.\n"
             "  -d, --double : Enable double-precision storage of floating point values.\n"
             "  -s, --surf   : Store SSW surface IDs in the MCPL userflags.\n"
             "  -n, --nogzip : Do not attempt to gzip output file.\n"
             "  -c FILE      : Embed entire configuration FILE (the input deck)\n"
             "                 used to produce input.ssw in the MCPL header.\n"
             );
      free(progname);
      exit(0);
    }
    if (strcmp(argv[i],"-c")==0) {
      if (i+1==argc||argv[i+1][0]=='-') {
        printf("Error: Missing argument for -c\n");
        exit(1);
      }
      ++i;
      if (*cfgfile) {
        printf("Error: -c specified more than once\n");
        exit(1);
      }
      *cfgfile = argv[i];
      continue;
    }

    if (strcmp(argv[i],"-d")==0||strcmp(argv[i],"--double")==0) {
      *double_prec = 1;
      continue;
    }
    if (strcmp(argv[i],"-s")==0||strcmp(argv[i],"--surf")==0) {
      *surface_info = 1;
      continue;
    }
    if (strcmp(argv[i],"-n")==0||strcmp(argv[i],"--nogzip")==0) {
      *do_gzip = 0;
      continue;
    }
    if (argv[i][0]=='-') {
      printf("Error: Unknown argument: %s\n",argv[i]);
      exit(1);
    }
    if (!*infile) {
      *infile = argv[i];
      continue;
    }
    if (!*outfile) {
      *outfile = argv[i];
      continue;
    }
    printf("Error: Too many arguments! (run with -h or --help for usage instructions)\n");
    exit(1);
  }
  if (!*infile) {
    printf("Error: Too few arguments! (run with -h or --help for usage instructions)\n");
    exit(1);
  }
  if (!*outfile)
    *outfile = "output.mcpl";
  if (strcmp(*infile,*outfile)==0) {
    //basic test, easy to cheat:
    printf("Error: input and output files are identical.\n");
    exit(1);
  }
}

int ssw2mcpl_app(int argc,char** argv)
{
  const char * infile;
  const char * outfile;
  const char * cfgfile;
  int double_prec, surface_info, do_gzip;
  ssw2mcpl_parse_args(argc,argv,&infile,&outfile,&cfgfile,&double_prec,&surface_info,&do_gzip);
  int ok = ssw2mcpl2(infile, outfile,double_prec, surface_info, do_gzip,cfgfile);
  return ok ? 0 : 1;
}

void ssw_update_nparticles( mcpl_generic_wfilehandle_t* fh,
                            int64_t np1pos, int32_t np1,
                            int64_t nrsspos, int32_t nrss)
{
  //Seek and update np1 and nrss fields at correct location in header:
  uint64_t savedpos = fh->current_pos;
  mcpl_generic_fwseek( fh, np1pos );
  mcpl_generic_fwrite( fh, (char*)&np1, sizeof(np1) );
  mcpl_generic_fwseek( fh, nrsspos );
  mcpl_generic_fwrite( fh, (char*)&nrss, sizeof(nrss) );
  mcpl_generic_fwseek( fh, savedpos );
}

void ssw_writerecord( mcpl_generic_wfilehandle_t* fh,
                      int reclen, size_t lbuf, char* buf )
{
  if (reclen==4) {
    if ( lbuf > UINT32_MAX )
      ssw_error("output record size too large for 32bit records");
    uint32_t rl = (uint32_t)lbuf;
    mcpl_generic_fwrite( fh, (char*)&rl, sizeof(rl) );
    mcpl_generic_fwrite( fh, buf, lbuf );
    mcpl_generic_fwrite( fh, (char*)&rl, sizeof(rl) );
  } else {
    assert(reclen==8);
    uint64_t rl = lbuf;
    mcpl_generic_fwrite( fh, (char*)&rl, sizeof(rl) );
    mcpl_generic_fwrite( fh, buf, lbuf );
    mcpl_generic_fwrite( fh, (char*)&rl, sizeof(rl) );
  }
}

int mcpl2ssw(const char * inmcplfile, const char * outsswfile, const char * refsswfile,
             long surface_id, long nparticles_limit)
{

  mcpl_file_t fmcpl = mcpl_open_file(inmcplfile);

  printf( "Opened MCPL file produced with \"%s\" (contains %llu particles)\n",
          mcpl_hdr_srcname(fmcpl),
          (unsigned long long)mcpl_hdr_nparticles(fmcpl) );

  if (surface_id==0 && !mcpl_hdr_has_userflags(fmcpl))
    ssw_error("MCPL file contains no userflags so parameter specifying "
              "resulting SSW surface ID of particles is mandatory (use -s<ID>).");

  printf("Opening reference SSW file:\n");
  ssw_file_t fsswref = ssw_open_file(refsswfile);

  //Open reference file and figure out variables like header length, position of
  //"nparticles"-like variables, fortran record length and mcnp version.
  int ssw_reclen;
  int ssw_ssblen;
  int64_t ssw_hdrlen;
  int64_t ssw_np1pos;
  int64_t ssw_nrsspos;
  ssw_layout(fsswref, &ssw_reclen, &ssw_ssblen, &ssw_hdrlen, &ssw_np1pos, &ssw_nrsspos);
  assert(ssw_np1pos<ssw_hdrlen);
  assert(ssw_nrsspos<ssw_hdrlen);

#define SSW_MCNP6 1
#define SSW_MCNPX 2
#define SSW_MCNP5 3
  int ssw_mcnp_type = 0;
  if (ssw_is_mcnp6(fsswref)) {
    ssw_mcnp_type = SSW_MCNP6;
  } else if (ssw_is_mcnpx(fsswref)) {
    ssw_mcnp_type = SSW_MCNPX;
  } else if (ssw_is_mcnp5(fsswref)) {
    ssw_mcnp_type = SSW_MCNP5;
  }
  assert(ssw_mcnp_type>0);
  char ref_mcnpflavour_str[64];
  ref_mcnpflavour_str[0] = '\0';
  ssw_strcat( ref_mcnpflavour_str,
              ssw_mcnpflavour(fsswref),
              sizeof(ref_mcnpflavour_str) );
  ssw_close_file(fsswref);

  //Grab the header:
  char * hdrbuf;
  {
    uint64_t actual_size;
    mcpl_read_file_to_buffer( refsswfile,
                              (uint64_t)ssw_hdrlen,
                              0,//not text
                              &actual_size,
                              &hdrbuf );
    if ( !hdrbuf || actual_size != (uint64_t)ssw_hdrlen )
      ssw_error("Problems extracting header from reference file");
  }

  int32_t orig_np1 = * ((int32_t*)(&hdrbuf[ssw_np1pos]));

  //Clear |np1| and nrss in header to to indicate incomplete info (we will
  //update just before closing the file):
  *((int32_t*)(&hdrbuf[ssw_np1pos])) = 0;
  *((int32_t*)(&hdrbuf[ssw_nrsspos])) = 0;

  printf("Creating (or overwriting) output SSW file.\n");

  //Open new ssw file:
  mcpl_generic_wfilehandle_t fout = mcpl_generic_wfopen( outsswfile );
  if (!fout.internal)
    ssw_error("Problems opening new SSW file");

  //Write header:
  mcpl_generic_fwrite( &fout, hdrbuf, ssw_hdrlen);
  free(hdrbuf);
  hdrbuf = NULL;

  double ssb[11];

  if ( ssw_ssblen != 10 && ssw_ssblen != 11)
    ssw_error("Unexpected length of ssb record in reference SSW file");
  if ( (ssw_mcnp_type == SSW_MCNP6) && ssw_ssblen != 11 )
    ssw_error("Unexpected length of ssb record in reference SSW file (expected 11 for MCNP6 files)");

  //ssb[0] should be history number (starting from 1), but in our case we always
  //put nhistories=nparticles, so it is simply incrementing by 1 for each particle.
  ssb[0] = 0.0;


  assert(surface_id>=0&&surface_id<1000000);


  long used = 0;
  long long skipped_nosswtype = 0;

  printf("Initiating particle conversion loop.\n");

  while ( 1 ) {
    const mcpl_particle_t* mcpl_p = mcpl_read(fmcpl);
    if (!mcpl_p)
      break;
    ++ssb[0];
    ssb[2] = mcpl_p->weight;
    ssb[3] = mcpl_p->ekin;//already in MeV
    ssb[4] = mcpl_p->time * 1.0e5;//milliseconds to "shakes"
    ssb[5] = mcpl_p->position[0];//already in cm
    ssb[6] = mcpl_p->position[1];//already in cm
    ssb[7] = mcpl_p->position[2];//already in cm
    ssb[8] = mcpl_p->direction[0];
    ssb[9] = mcpl_p->direction[1];

    int32_t isurf = surface_id;
    if (!isurf)
      isurf = (int32_t)mcpl_p->userflags;

    if (isurf<=0||isurf>1000000) {
      if (isurf==0&&surface_id==0)
        ssw_error("Could not determine surface ID: no global surface id specified and particle had no (or empty) userflags");
      else
        ssw_error("Surface id must be in range 1..999999");
    }

    int64_t rawtype;
    if (ssw_mcnp_type == SSW_MCNP6) {
      rawtype = conv_mcnp6_pdg2ssw(mcpl_p->pdgcode);
    } else if (ssw_mcnp_type == SSW_MCNPX) {
      rawtype = conv_mcnpx_pdg2ssw(mcpl_p->pdgcode);
    } else {
      assert(ssw_mcnp_type == SSW_MCNP5);
      rawtype = (mcpl_p->pdgcode==2112?1:(mcpl_p->pdgcode==22?2:0));
    }

    if (!rawtype) {
      ++skipped_nosswtype;
      if (skipped_nosswtype<=100) {
        printf("WARNING: Found PDG code (%li) in the MCPL file which can not be converted to an %s particle type\n",
               (long)mcpl_p->pdgcode,ref_mcnpflavour_str);
        if (skipped_nosswtype==100)
          printf("WARNING: Suppressing future warnings regarding non-convertible PDG codes.\n");
      }
      continue;
    }

    if ( !(rawtype>0 ) )
      ssw_error("Logic error in PDG code conversions.");
    assert(rawtype>0);

    if (ssw_mcnp_type == SSW_MCNP6) {
      assert(ssw_ssblen==11);
      ssb[10] = isurf;//Should we set the sign of ssb[10] to mean something (we take abs(ssb[10]) in sswread.c)?
      ssb[1] = (double)(((int64_t)rawtype)*4);//Shift 2 bits (thus we only create files with those two bits zero!)
    } else if (ssw_mcnp_type == SSW_MCNPX) {
      ssb[1] = (double)(isurf + 1000000*((int64_t)rawtype));
      if (ssw_ssblen==11)
        ssb[10] = 1.0;//Cosine of angle at surface? Can't calculate it, so we simply set
                      //it to 1 (seems to be not used anyway?)
    } else {
      assert(ssw_mcnp_type == SSW_MCNP5);
      //NOTE: We had for MCPL <=1.6.x: ssb[1] = (isurf + 1000000*rawtype)*8; But
      //now we try instead:
      ssb[1] = (double)((isurf + 100000000*((int64_t)rawtype))*8);
      if (ssw_ssblen==11)
        ssb[10] = 1.0;//Cosine of angle at surface? Can't calculate it, so we simply set
                      //it to 1 (seems to be not used anyway?)
    }

    //Sign of ssb[1] is used to store the sign of dirz:
    assert(ssb[1] >= 1.0);
    if (mcpl_p->direction[2]<0.0)
      ssb[1] = - ssb[1];

    ssw_writerecord(&fout,ssw_reclen,sizeof(double)*ssw_ssblen,(char*)&ssb[0]);
    if (++used==nparticles_limit) {
      long long remaining = mcpl_hdr_nparticles(fmcpl) - skipped_nosswtype - used;
      if (remaining)
        printf("Output limit of %li particles reached. Ignoring remaining %lli particles in the MCPL file.\n",
               nparticles_limit,remaining);
      break;
    }
  }

  printf("Ending particle conversion loop.\n");

  if (skipped_nosswtype) {
    printf("WARNING: Ignored %lli particles in the input MCPL file since their PDG codes"
           " could not be converted to MCNP types.\n",(long long)skipped_nosswtype);
  }

  int32_t new_nrss = used;
  int32_t new_np1 = new_nrss;

  if (new_np1==0) {
    //SSW files must at least have 1 history (but can have 0 particles)
    printf("WARNING: Input MCPL file has 0 useful particles but we are setting number"
           " of histories in new SSW file to 1 to avoid creating an invalid file.\n");
    new_np1 = 1;
  }
  if (orig_np1<0)
    new_np1 = - new_np1;

  ssw_update_nparticles(&fout,ssw_np1pos,new_np1,ssw_nrsspos,new_nrss);

  mcpl_close_file(fmcpl);
  mcpl_generic_fwclose(&fout);

  printf("Created %s with %lli particles (nrss) and %lli histories (np1).\n",outsswfile,(long long)new_nrss,(long long)labs(new_np1));
  return 1;


}


int mcpl2ssw_app_usage( const char** argv, const char * errmsg ) {
  if (errmsg) {
    printf("ERROR: %s\n\n",errmsg);
    printf("Run with -h or --help for usage information\n");
    return 1;
  }
  char * progname = mcpl_usage_progname(argv[0]);
  printf("Usage:\n\n");
  printf("  %s [options] <input.mcpl> <reference.ssw> [output.ssw]\n\n",progname);
  printf("Converts the Monte Carlo particles in the input MCPL file to SSW format\n"
         "(MCNP Surface Source Write) and stores the result in the designated output\n"
         "file (defaults to \"output.ssw\").\n"
         "\n"
         "In order to do so and get the details of the SSW format correct, the user\n"
         "must also provide a reference SSW file from the same approximate setup\n"
         "(MCNP version, input deck...) where the new SSW file is to be used. The\n"
         "reference SSW file can of course be very small, as only the file header is\n"
         "important (the new file essentially gets a copy of the header found in the\n"
         "reference file, except for certain fields related to number of particles\n"
         "whose values are changed).\n"
         "\n"
         "Finally, one must pay attention to the Surface ID assigned to the\n"
         "particles in the resulting SSW file: Either the user specifies a global\n"
         "one with -s<ID>, or it is assumed that the MCPL userflags field in the\n"
         "input file is actually intended to become the Surface ID. Note that not\n"
         "all MCPL files have userflag fields and that valid Surface IDs are\n"
         "integers in the range 1-999999.\n"
         "\n"
         "Options:\n"
         "\n"
         "  -h, --help   : Show this usage information.\n"
         "  -s<ID>       : All particles in the SSW file will get this surface ID.\n"
         "  -l<LIMIT>    : Limit the number of particles transferred to the SSW file\n"
         "                 (defaults to 2147483647, the maximal SSW capacity).\n"
         );
  free(progname);
  return 0;
}

int mcpl2ssw_parse_args(int argc,const char **argv, const char** inmcplfile,
                        const char **refsswfile, const char **outsswfile,
                        long* nparticles_limit, long* surface_id) {
  //returns: 0 all ok, 1: error, -1: all ok but do nothing (-h/--help mode)
  *inmcplfile = 0;
  *refsswfile = 0;
  *outsswfile = 0;
  *nparticles_limit = INT32_MAX;
  *surface_id = 0;

  int64_t opt_num_limit = -1;
  int64_t opt_num_isurf = -1;
  int i;
  for (i = 1; i<argc; ++i) {
    const char * a = argv[i];
    size_t n = strlen(a);
    if (!n)
      continue;
    if (n>=2&&a[0]=='-'&&a[1]!='-') {
      //short options:
      int64_t * consume_digit = 0;
      size_t j;
      for (j=1; j<n; ++j) {
        if (consume_digit) {
          if (a[j]<'0'||a[j]>'9')
            return mcpl2ssw_app_usage(argv,"Bad option: expected number");
          *consume_digit *= 10;
          *consume_digit += a[j] - '0';
          continue;
        }
        switch(a[j]) {
        case 'h': mcpl2ssw_app_usage(argv,0); return -1;
        case 'l': consume_digit = &opt_num_limit; break;
        case 's': consume_digit = &opt_num_isurf; break;
        default:
          return mcpl2ssw_app_usage(argv,"Unrecognised option");
        }
        if (consume_digit) {
          *consume_digit = 0;
          if (j+1==n)
            return mcpl2ssw_app_usage(argv,"Bad option: missing number");
        }
      }

    } else if (n==6 && strcmp(a,"--help")==0) {
      mcpl2ssw_app_usage(argv,0);
      return -1;
    } else if (n>=1&&a[0]!='-') {
      if (*outsswfile)
        return mcpl2ssw_app_usage(argv,"Too many arguments.");
      if (*refsswfile) *outsswfile = a;
      else if (*inmcplfile) *refsswfile = a;
      else *inmcplfile = a;
    } else {
      return mcpl2ssw_app_usage(argv,"Bad arguments");
    }
  }

  if (!*inmcplfile)
    return mcpl2ssw_app_usage(argv,"Missing argument : input MCPL file");
  if (!*refsswfile)
    return mcpl2ssw_app_usage(argv,"Missing argument : Reference SSW file");
  if (!*outsswfile)
    *outsswfile = "output.ssw";

  if (opt_num_limit<=0)
    opt_num_limit = INT32_MAX;
  if (opt_num_limit>INT32_MAX)
    return mcpl2ssw_app_usage(argv,"Parameter out of range : SSW files can only hold up to 2147483647 particles.");
  *nparticles_limit = (long)opt_num_limit;

  if (opt_num_isurf==0||opt_num_isurf>999999)
    return mcpl2ssw_app_usage(argv,"Parameter out of range : Surface ID must be in range [1,999999].");
  if (opt_num_isurf<0)
    opt_num_isurf = 0;

  *surface_id = (long)opt_num_isurf;

  return 0;
}

int mcpl2ssw_app( int argc, char** argv ) {

  const char * inmcplfile;
  const char * refsswfile;
  const char * outsswfile;
  long nparticles_limit;
  long surface_id;

  int parse = mcpl2ssw_parse_args( argc, (const char**)argv,
                                   &inmcplfile, &refsswfile, &outsswfile,
                                   &nparticles_limit, &surface_id );

  if (parse==-1)// --help
    return 0;

  if (parse)// parse error
    return parse;

  if (mcpl2ssw(inmcplfile, outsswfile, refsswfile,surface_id, nparticles_limit))
    return 0;

  return 1;

}
