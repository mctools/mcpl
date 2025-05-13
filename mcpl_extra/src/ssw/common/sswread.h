
/******************************************************************************/
/*                                                                            */
/*  This file is part of MCPL (see https://mctools.github.io/mcpl/)           */
/*                                                                            */
/*  Copyright 2015-2025 MCPL developers.                                      */
/*                                                                            */
/*  Licensed under the Apache License, Version 2.0 (the "License");           */
/*  you may not use this file except in compliance with the License.          */
/*  You may obtain a copy of the License at                                   */
/*                                                                            */
/*      http://www.apache.org/licenses/LICENSE-2.0                            */
/*                                                                            */
/*  Unless required by applicable law or agreed to in writing, software       */
/*  distributed under the License is distributed on an "AS IS" BASIS,         */
/*  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  */
/*  See the License for the specific language governing permissions and       */
/*  limitations under the License.                                            */
/*                                                                            */
/******************************************************************************/

#ifndef sswread_h
#define sswread_h

////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Code for reading SSW files from MCNP(X). Not all versions of the format    //
// has been tested, but it is the hope that this will at the very least       //
// provide reliable functionality for extracting the particle information     //
// within.                                                                    //
//                                                                            //
// The code was written with help from E. Klinkby DTU NuTech and under        //
// inspiration from equivalent programs written in Fortran (E. Klinkby DTU    //
// NuTech with help from H. Breitkreutz) and in python (PyNE & mc-tools by    //
// K. Batkov ESS).                                                            //
//                                                                            //
// Refer to the top of sswread.c for details regarding how to build.          //
//                                                                            //
// Note that usage of MCNP(X)-related utilities might require additional      //
// permissions and licenses from third-parties, which is not within the       //
// scope of the MCPL project itself.                                          //
//                                                                            //
// Written 2015-2025, thomas.kittelmann@ess.eu (European Spallation Source).  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

  typedef struct {
    void * internal;
  } ssw_file_t;

  typedef struct {
    double x;//cm
    double y;//cm
    double z;//cm
    double dirx;
    double diry;
    double dirz;
    double weight;
    double ekin;//MeV
    double time;//"shakes" (1e-8seconds)
    long rawtype;//raw particle type encoding (mcnpx and mcnp6 employs different schemes)
    long pdgcode;//rawtype converted to PDG codes.
    long isurf;
  } ssw_particle_t;

  //Open file (can read gzipped ssw .gz files directly if zlib usage is enabled):
  ssw_file_t ssw_open_file(const char * filename);

  //Query header info:
  unsigned long ssw_nparticles(ssw_file_t);
  const char* ssw_srcname(ssw_file_t);//Usually "mcnp" or "mcnpx"
  const char* ssw_srcversion(ssw_file_t);
  const char* ssw_title(ssw_file_t);//Problem title from input deck
  int32_t ssw_abs_np1(ssw_file_t);//absolute value of np1 field in file.
  int ssw_is_mcnp6(ssw_file_t);
  int ssw_is_mcnp5(ssw_file_t);
  int ssw_is_mcnpx(ssw_file_t);
  const char * ssw_mcnpflavour(ssw_file_t);//string like "MCNPX" or "MCNP6"

  //load next particle (null indicates eof):
  const ssw_particle_t * ssw_load_particle(ssw_file_t);

  //close file and release resources:
  void ssw_close_file(ssw_file_t);

  //Advanced info about file layout:
  void ssw_layout(ssw_file_t, int* reclen, int* ssblen, int64_t* hdrlen,
                  int64_t* np1pos, int64_t* nrsspos);

  ////////////////////////////////////////////////////////////////////////////
  //                                                                        //
  // Utility functions for converting between particle codes used in SSW    //
  // files from MCNPX or MCNP6 and the codes from the Particle Data Group:  //
  //                                                                        //
  // http://pdg.lbl.gov/2014/reviews/rpp2014-rev-monte-carlo-numbering.pdf  //
  //                                                                        //
  // Note that all the functions here return 0 when the code could not be   //
  // converted. This might not be an error as such, but could indicate an   //
  // exotic particle which has no code assigned in the target MCNP scheme.  //
  //                                                                        //
  // MCNP5 does not have it's own function as it only supports neutrons     //
  // (1<->2112) and gammas (2<->22).                                        //
  //                                                                        //
  ////////////////////////////////////////////////////////////////////////////

  int32_t conv_mcnpx_ssw2pdg(int32_t);
  int32_t conv_mcnp6_ssw2pdg(int32_t);

  int32_t conv_mcnpx_pdg2ssw(int32_t);
  int32_t conv_mcnp6_pdg2ssw(int32_t);

#ifdef __cplusplus
}
#endif

#endif
