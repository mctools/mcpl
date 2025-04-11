
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

#ifndef phitsmcpl_h
#define phitsmcpl_h

#include <stdint.h>

////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Functions for converting binary PHITS dump files to and from MCPL files.   //
//                                                                            //
// The code was written with help from D. Di Julio, ESS.                      //
//                                                                            //
// Note that usage of PHITS-related utilities might require additional        //
// permissions and licenses from third-parties, which is not within the       //
// scope of the MCPL project itself.                                          //
//                                                                            //
// Written 2019-2025 by Thomas.Kittelmann@ess.eu                              //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////////////
// Create mcplfile based on content in PHITS dump file. Using this function will
// use single-precision in the output file, and will always attempt to gzip the
// resulting MCPL file. Use phits2mcpl2 instead to fine-tune these choices or to
// embed a copy of the PHITS input deck or dump summary file in the MCPL header
// for reference. Returns 1 on success, 0 on failure:
int phits2mcpl(const char * phitsfile, const char * mcplfile);

//////////////////////////////////////////////////////////////////////////////////////
// Advanced version of the above with more options:
//
//  opt_dp  : Set to 1 to enable double-precision storage of floating point
//            values. Set to 0 for single-precision.
//  opt_gzip: Set to 1 to gzip the resulting mcpl file. Set to 0 to leave the
//            resulting file uncompressed.
//  inputdeckfile: Set to the filename of the PHITS input deck file, to embed a
//                 copy of it in the MCPL header. Set to 0 to not do this.
//  dumpsummaryfile: Set to the filename of the dump summary text file (which
//                   is produced along with the binary dump file by PHITS), to
//                   embed a copy of it in the MCPL header. Set to 0 to not do
//                   this.
//
//  Note: The created mcpl file will have polarisation columns enabled if and
//  only if the input dump file has polarisation info.

int phits2mcpl2( const char * phitsdumpfile, const char * mcplfile,
                 int opt_dp, int opt_gzip,
                 const char * inputdeckfile,
                 const char * dumpsummaryfile );

//////////////////////////////////////////////////////////////////////////////////////

// Create binary PHITS dump file based on content in mcplfile. If usepol option
// is set to 1 (as opposed to 0), the resulting file will include polarisation (aka spin
// direction) information and must be read via:
//
//           dump=13
//                1 2 3 4 5 6 7 8 9 10 14 15 16
//
// Otherwise it is excluded and the reader must be configured via:
//
//           dump=10
//                1 2 3 4 5 6 7 8 9 10
//
// If the limit parameter is non-zero, it will provide an upper limit on the
// number of particles put into the resulting phits file. Finally, the reclen
// parameters control whether the hidden Fortran record markers in the produced
// file use 32bit (reclen=4) or 64bit (reclen=8) integers. The correct choice is
// almost always to use reclen=4.

int mcpl2phits( const char * mcplfile, const char * phitsdumpfile,
                int usepol, uint64_t limit, int reclen );

//////////////////////////////////////////////////////////////////////////////////////
// For easily creating standard phits2mcpl and mcpl2phits cmdline applications:
int phits2mcpl_app(int argc,char** argv);
int mcpl2phits_app(int argc,char** argv);

#endif
