#ifndef stockmcpl_h
#define stockmcpl_h

//////////////////////////////////////////////////////////////////////////////////////
//                                                                                  //
// Functions for converting stock files from TRIPOLI-4 (STORAGE) to MCPL files.     //
//                                                                                  //
// Written 2021, osiris.abbate@ib.edu.ar, (Instituto Balseiro).                     //
//                                                                                  //
//////////////////////////////////////////////////////////////////////////////////////


//////////////////////////////////////////////////////////////////////////////////////
// Create mcplfile based on content in stockfile. Using this function will not
// enable double-precision or user-flags in the output file. Returns 1 on success,
// 0 on failure:
int stock2mcpl(const char * stockfile, const char * mcplfile);

//////////////////////////////////////////////////////////////////////////////////////
// Advanced version of the above with more options:
//
//  opt_dp  : Set to 1 to enable double-precision storage of floating point
//            values. Set to 0 for single-precision.
//  opt_gzip: Set to 1 to gzip the resulting mcpl file. Set to 0 to leave the
//            resulting file uncompressed.
//
int stock2mcpl2(const char * stockfile, const char * mcplfile,
              int opt_dp, int opt_gzip);

//////////////////////////////////////////////////////////////////////////////////////
// For easily creating standard stock2mcpl cmdline applications:
int stock2mcpl_app(int argc,char** argv);

#endif
