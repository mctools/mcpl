
/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
//  ptracmcpl : Code for converting between MCPL and PTRAC files from MCNP(X).     //
//                                                                                 //
//                                                                                 //
//  Compilation of ptracmcpl.c can proceed via any compliant C-compiler using      //
//  -std=c99 later. Furthermore, the following preprocessor flag can be used       //
//  when compiling ptracmcpl.c to fine tune the build process.                     //
//                                                                                 //
//  SSWMCPL_HDR_INCPATH  : Specify alternative value if the ptracmcpl header       //
//                         itself is not to be included as "ptracmcpl.h".          //
//  SSWREAD_HDR_INCPATH  : Specify alternative value if the ptracread header       //
//                         is not to be included as "ptracread.h".                 //
//  MCPL_HEADER_INCPATH  : Specify alternative value if the MCPL header is         //
//                         not to be included as "mcpl.h".                         //
//                                                                                 //
// Written 2021, osiris.abbate@ib.edu.ar (Instituto Balseiro).                     //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

#ifdef SSWMCPL_HDR_INCPATH
#  include SSWMCPL_HDR_INCPATH
#else
#  include "ptracmcpl.h"
#endif

#ifdef SSWREAD_HDR_INCPATH
#  include SSWREAD_HDR_INCPATH
#else
#  include "ptracread.h"
#endif

#ifdef MCPL_HEADER_INCPATH
#  include MCPL_HEADER_INCPATH
#else
#  include "mcpl.h"
#endif

#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>
#include <assert.h>

//fwd declare internal functions from ptracread.c
void ptrac_error(const char * msg);
long ptrac_get_pdgcode(ptrac_file_t * f);

int ptrac2mcpl(const char * ptracfile, const char * mcplfile)
{
  return ptrac2mcpl2(ptracfile, mcplfile, 0, 1);
}

int ptrac2mcpl2(const char * ptracfile, const char * mcplfile,
              int opt_dp, int opt_gzip)
{
  ptrac_file_t f = ptrac_open_file(ptracfile);
  mcpl_outfile_t mcplfh = mcpl_create_outfile(mcplfile);

  mcpl_hdr_set_srcname(mcplfh,"MCNP (PTRAC)");

  // Copiar info de header de ptrac a archivo mcpl
  mcpl_enable_universal_pdgcode(mcplfh, ptrac_get_pdgcode(&f));

  if (opt_dp) {
    mcpl_enable_doubleprec(mcplfh);
  }

  mcpl_particle_t mcpl_particle;
  memset(&mcpl_particle,0,sizeof(mcpl_particle));

  const ptrac_particle_t * p;
  while ((p=ptrac_load_particle(f))) {

    mcpl_particle.position[0] = p->x;//already in cm
    mcpl_particle.position[1] = p->y;//already in cm
    mcpl_particle.position[2] = p->z;//already in cm
    mcpl_particle.direction[0] = p->dirx;
    mcpl_particle.direction[1] = p->diry;
    mcpl_particle.direction[2] = p->dirz;
    mcpl_particle.time = p->time * 1.0e-5;//"shakes" to milliseconds
    mcpl_particle.weight = p->weight;
    mcpl_particle.ekin = p->ekin;//already in MeV

    mcpl_add_particle(mcplfh,&mcpl_particle);

  }

  const char * tmp = mcpl_outfile_filename(mcplfh);
  size_t laf = strlen(tmp);
  char * actual_filename = malloc(laf+1);
  actual_filename[0]='\0';
  strcat(actual_filename,tmp);

  int did_gzip = 0;
  if (opt_gzip)
    did_gzip = mcpl_closeandgzip_outfile(mcplfh);
  else
    mcpl_close_outfile(mcplfh);
  ptrac_close_file(f);

  printf("Created %s%s\n",actual_filename,(did_gzip?".gz":""));
  free(actual_filename);
  return 1;
}

void ptrac2mcpl_parse_args(int argc,char **argv, const char** infile,
                         const char **outfile, const char **cfgfile,
                         int* double_prec, int* do_gzip) {
  *cfgfile = 0;
  *infile = 0;
  *outfile = 0;
  *double_prec = 0;
  *do_gzip = 1;
  int i;
  for (i=1; i < argc; ++i) {
    if (argv[i][0]=='\0')
      continue;
    if (strcmp(argv[i],"-h")==0||strcmp(argv[i],"--help")==0) {
      const char * progname = strrchr(argv[0], '/');
      progname = progname ? progname + 1 : argv[0];
      printf("Usage:\n\n");
      printf("  %s [options] input.ptrac [output.mcpl]\n\n",progname);
      printf("Converts the Monte Carlo particles in the input.ptrac file (MCNP Particle\n"
             "Track format) to MCPL format and stores in the designated output file\n"
             "(defaults to \"output.mcpl\").\n"
             "\n"
             "Options:\n"
             "\n"
             "  -h, --help   : Show this usage information.\n"
             "  -d, --double : Enable double-precision storage of floating point values.\n"
             "  -n, --nogzip : Do not attempt to gzip output file.\n"
             );
      exit(0);
    }

    if (strcmp(argv[i],"-d")==0||strcmp(argv[i],"--double")==0) {
      *double_prec = 1;
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

int ptrac2mcpl_app(int argc,char** argv)
{
  const char * infile;
  const char * outfile;
  const char * cfgfile;
  int double_prec, do_gzip;
  ptrac2mcpl_parse_args(argc,argv,&infile,&outfile,&cfgfile,&double_prec,&do_gzip);
  int ok = ptrac2mcpl2(infile, outfile, double_prec, do_gzip);
  return ok ? 0 : 1;
}
