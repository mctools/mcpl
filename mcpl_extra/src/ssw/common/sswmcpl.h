
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

#ifndef sswmcpl_h
#define sswmcpl_h

////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Functions for converting SSW files from MCNP(X) to MCPL files.             //
//                                                                            //
// The code was written with help from E. Klinkby DTU NuTech.                 //
//                                                                            //
// Note that usage of MCNP(X)-related utilities might require additional      //
// permissions and licenses from third-parties, which is not within the       //
// scope of the MCPL project itself.                                          //
//                                                                            //
// Written 2015-2025 by Thomas.Kittelmann@ess.eu                              //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////


//////////////////////////////////////////////////////////////////////////////////////
// Create mcplfile based on content in sswfile. Using this function will neither
// enable double-precision or user-flags in the output file, and will always
// attempt to gzip the resulting MCPL file. Use ssw2mcpl2 instead to fine-tune
// these choices or to embed a copy of the MCNP input deck file in the MCPL
// header. Returns 1 on success, 0 on failure:
int ssw2mcpl(const char * sswfile, const char * mcplfile);

//////////////////////////////////////////////////////////////////////////////////////
// Advanced version of the above with more options:
//
//  opt_dp  : Set to 1 to enable double-precision storage of floating point
//            values. Set to 0 for single-precision.
//  opt_surf: Set to 1 to store SSW surface id information in the MCPL
//            userflags. Set to 0 to not store any userflags.
//  opt_gzip: Set to 1 to gzip the resulting mcpl file. Set to 0 to leave the
//            resulting file uncompressed.
//  inputdeckfile: Set to the filename of the MCNP input deck file, to embed a
//                 copy of it in the MCPL header. Set to 0 to not do this.
//
int ssw2mcpl2(const char * sswfile, const char * mcplfile,
              int opt_dp, int opt_surf, int opt_gzip,
              const char * inputdeckfile);

//////////////////////////////////////////////////////////////////////////////////////
// Create sswfile based on content in mcplfile. This also needs a reference
// sswfile from the same approximate setup (MCNP version, input deck...) where
// the new SSW file is to be used. If the surface_id parameter is non-zero, all
// particles in the resulting sswfile will have that surface ID, otherwise it
// will be taken from the MCPL userflags (must be in range [1,999999]). Finally,
// if the limit parameter is non-zero, it will provide an upper limit on the
// number of particles put into the resulting ssw file (up to 2147483647).
int mcpl2ssw(const char * mcplfile, const char * sswfile, const char * refsswfile,
             long surface_id, long limit);

//////////////////////////////////////////////////////////////////////////////////////
// For easily creating standard ssw2mcpl and mcpl2ssw cmdline applications:
int ssw2mcpl_app(int argc,char** argv);
int mcpl2ssw_app(int argc,char** argv);

#endif
