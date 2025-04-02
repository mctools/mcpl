
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

#ifndef phitsread_h
#define phitsread_h

////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Code for reading binary PHITS dump files. This has been tested with PHITS  //
// version 3.1 so far.                                                        //
//                                                                            //
// The code was written with help from Douglas Di Julio (European Spallation  //
// Source), and the PHITS dump file format was mostly inferred by looking in  //
// the PHITS manual (it is in any case extremely simple).                     //
//                                                                            //
// Refer to the top of phitsread.c for details regarding how to build.        //
//                                                                            //
// Note that usage of PHITS-related utilities might require additional        //
// permissions and licenses from third-parties, which is not within the       //
// scope of the MCPL project itself.                                          //
//                                                                            //
// Written 2019-2025, thomas.kittelmann@ess.eu (European Spallation Source).  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

  typedef struct {
    void * internal;
  } phits_file_t;

  typedef struct {
    double x;//cm
    double y;//cm
    double z;//cm
    double dirx;
    double diry;
    double dirz;
    double polx;
    double poly;
    double polz;
    double weight;
    double ekin;//MeV
    double time;//nanoseconds
    long rawtype;//raw particle type encoding (PHITS "kt")
    long pdgcode;//rawtype converted to PDG codes.
  } phits_particle_t;

  //Open file (can read gzipped phits .gz files directly if zlib usage is enabled):
  phits_file_t phits_open_file(const char * filename);

  //Whether input file was gzipped:
  int phits_is_gzipped(phits_file_t);

  //Whether input file contains polarisation fields (note that the special case
  //of a file with 0 particles will always register as not having polarisation
  //fields):
  int phits_has_polarisation(phits_file_t);

  //load next particle (null indicates EOF):
  const phits_particle_t * phits_load_particle(phits_file_t);

  //close file and release resources:
  void phits_close_file(phits_file_t);

  ////////////////////////////////////////////////////////////////////////////
  //                                                                        //
  // Utility functions for converting between particle codes used in PHITS  //
  // (cf user manual for PHITS 3.1, page 29), and the codes from the        //
  // Particle Data Group (which actually overlaps for the non-ions          //
  // supported in PHITS):                                                   //
  //                                                                        //
  // http://pdg.lbl.gov/2014/reviews/rpp2014-rev-monte-carlo-numbering.pdf  //
  //                                                                        //
  // Note that all the functions here return 0 when the code could not be   //
  // converted. This might not be an error as such, but could indicate an   //
  // exotic particle which has no code assigned in PHITS.                   //
  //                                                                        //
  ////////////////////////////////////////////////////////////////////////////

  int32_t conv_code_phits2pdg(int32_t);
  int32_t conv_code_pdg2phits(int32_t);

#ifdef __cplusplus
}
#endif

#endif
