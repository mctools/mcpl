
////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  This file is part of MCPL (see https://mctools.github.io/mcpl/)           //
//                                                                            //
//  Copyright 2015-2026 MCPL developers.                                      //
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

#include "mcpltestmodutils.h"
#include <stdio.h>
#include <string.h>

//Reference implementations with the C API, for comparison with files written
//by the Python MCPLOutFile class.

MCPLTEST_CTYPE_DICTIONARY
{
  return
    "void mcpltest_writefromraw( const char *, const char *, const char * );"
    "void mcpltest_repack( const char *, const char * );"
    "void mcpltest_transfer( const char *, const char *, const char * );"
    "void mcpltest_script( const char *, const char * );"
    ;
}

static void mcpltest_applyopts( mcpl_outfile_t o, const char * opts )
{
  //d=doubleprec p=polarisation u=userflags P=universal pdgcode W=universal weight
  if (strchr(opts,'d'))
    mcpl_enable_doubleprec(o);
  if (strchr(opts,'p'))
    mcpl_enable_polarisation(o);
  if (strchr(opts,'u'))
    mcpl_enable_userflags(o);
  if (strchr(opts,'P'))
    mcpl_enable_universal_pdgcode(o,2112);
  if (strchr(opts,'W'))
    mcpl_enable_universal_weight(o,2.5);
}

MCPLTEST_CTYPES void mcpltest_writefromraw( const char * rawfile,
                                            const char * outfile,
                                            const char * opts )
{
  //Raw file contains records of 12 doubles (position, direction,
  //polarisation, ekin, time, weight), an int32 (pdgcode) and an uint32
  //(userflags).
  FILE * fi = fopen( rawfile, "rb" );
  mcpl_outfile_t o = mcpl_create_outfile( outfile );
  mcpl_hdr_set_srcname(o,"writefromraw");
  mcpl_hdr_add_comment(o,"a comment");
  mcpl_hdr_add_stat_sum(o,"nsim",-1.0);
  mcpl_hdr_add_data(o,"blobkey",5,"abc\0d");
  mcpltest_applyopts(o,opts);
  mcpl_particle_t * p = mcpl_get_empty_particle(o);
  double v[12];
  int32_t pdgcode;
  uint32_t userflags;
  while ( fread(v,sizeof(v),1,fi) == 1
          && fread(&pdgcode,sizeof(pdgcode),1,fi) == 1
          && fread(&userflags,sizeof(userflags),1,fi) == 1 ) {
    for ( int i = 0; i < 3; ++i ) {
      p->position[i] = v[i];
      p->direction[i] = v[3+i];
      p->polarisation[i] = v[6+i];
    }
    p->ekin = v[9];
    p->time = v[10];
    p->weight = v[11];
    p->pdgcode = pdgcode;
    p->userflags = userflags;
    mcpl_add_particle(o,p);
  }
  mcpl_hdr_add_stat_sum(o,"nsim",12345.0);
  mcpl_close_outfile(o);
  fclose(fi);
}

MCPLTEST_CTYPES void mcpltest_repack( const char * infile, const char * outfile )
{
  mcpl_file_t f = mcpl_open_file(infile);
  mcpl_outfile_t o = mcpl_create_outfile(outfile);
  mcpl_transfer_metadata(f,o);
  const mcpl_particle_t * p;
  while ( ( p = mcpl_read(f) ) )
    mcpl_add_particle(o,p);
  mcpl_close_outfile(o);
  mcpl_close_file(f);
}

MCPLTEST_CTYPES void mcpltest_transfer( const char * infile,
                                        const char * outfile,
                                        const char * opts )
{
  mcpl_file_t f = mcpl_open_file(infile);
  mcpl_outfile_t o = mcpl_create_outfile(outfile);
  mcpltest_applyopts(o,opts);
  while ( mcpl_read(f) )
    mcpl_transfer_last_read_particle(f,o);
  mcpl_close_outfile(o);
  mcpl_close_file(f);
}

//Run a script of writer API calls, one per line (see pywriter.py for the
//Python version of this):
MCPLTEST_CTYPES void mcpltest_script( const char * outfile, const char * script )
{
  mcpl_outfile_t o = mcpl_create_outfile(outfile);
  mcpl_particle_t * p = NULL;
  char line[4096];
  const char * s = script;
  while ( *s ) {
    const char * e = strchr(s,'\n');
    size_t n = e ? (size_t)(e-s) : strlen(s);
    if ( n >= sizeof(line) )
      n = sizeof(line) - 1;
    memcpy(line,s,n);
    line[n] = '\0';
    s += n + ( e ? 1 : 0 );
    char * arg = strchr(line,' ');
    if (arg)
      *arg++ = '\0';
    else
      arg = line + strlen(line);
    if ( !strcmp(line,"srcname") ) {
      mcpl_hdr_set_srcname(o,arg);
    } else if ( !strcmp(line,"comment") ) {
      mcpl_hdr_add_comment(o,arg);
    } else if ( !strcmp(line,"blob") ) {
      char * data = strchr(arg,' ');
      if (data)
        *data++ = '\0';
      else
        data = arg + strlen(arg);
      mcpl_hdr_add_data(o,arg,(uint32_t)strlen(data),data);
    } else if ( !strcmp(line,"statsum") ) {
      char * val = strrchr(arg,' ');
      *val++ = '\0';
      mcpl_hdr_add_stat_sum(o,arg,strtod(val,NULL));
    } else if ( !strcmp(line,"scale") ) {
      mcpl_hdr_scale_stat_sums(o,strtod(arg,NULL));
    } else if ( !strcmp(line,"userflags") ) {
      mcpl_enable_userflags(o);
    } else if ( !strcmp(line,"pol") ) {
      mcpl_enable_polarisation(o);
    } else if ( !strcmp(line,"dp") ) {
      mcpl_enable_doubleprec(o);
    } else if ( !strcmp(line,"updg") ) {
      mcpl_enable_universal_pdgcode(o,(int32_t)strtol(arg,NULL,10));
    } else if ( !strcmp(line,"uw") ) {
      mcpl_enable_universal_weight(o,strtod(arg,NULL));
    } else if ( !strcmp(line,"metadata") ) {
      mcpl_file_t f = mcpl_open_file(arg);
      mcpl_transfer_metadata(f,o);
      mcpl_close_file(f);
    } else if ( !strcmp(line,"transfer") ) {
      mcpl_file_t f = mcpl_open_file(arg);
      while ( mcpl_read(f) )
        mcpl_transfer_last_read_particle(f,o);
      mcpl_close_file(f);
    } else if ( !strcmp(line,"particle") ) {
      //x y z ux uy uz polx poly polz ekin time weight pdgcode userflags
      double v[12];
      char * c = arg;
      for ( int i = 0; i < 12; ++i )
        v[i] = strtod(c,&c);
      long pdg = strtol(c,&c,10);
      unsigned long uf = strtoul(c,&c,10);
      if (!p)
        p = mcpl_get_empty_particle(o);
      for ( int i = 0; i < 3; ++i ) {
        p->position[i] = v[i];
        p->direction[i] = v[3+i];
        p->polarisation[i] = v[6+i];
      }
      p->ekin = v[9];
      p->time = v[10];
      p->weight = v[11];
      p->pdgcode = (int32_t)pdg;
      p->userflags = (uint32_t)uf;
      mcpl_add_particle(o,p);
    } else if ( !strcmp(line,"close") ) {
      mcpl_close_outfile(o);
      return;
    } else if ( !strcmp(line,"closegz") ) {
      mcpl_closeandgzip_outfile(o);
      return;
    } else {
      printf("Unknown script command: %s\n",line);
      exit(1);
    }
  }
  mcpl_close_outfile(o);
}
