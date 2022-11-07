#ifndef ptracread_h
#define ptracread_h

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// Code for reading PTRAC files from MCNP(X).                                      //
//                                                                                 //
// The code was written based on other hooks included in mcpl (mcnpssw, phits),    //
// but provides a more basic interface.                                            //
//                                                                                 //
// Written 2021, osiris.abbate@ib.edu.ar, (Instituto Balseiro).                    //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

  typedef struct {
    void * internal;
  } ptrac_file_t;

  typedef struct {
    double x;//cm
    double y;//cm
    double z;//cm
    double dirx;
    double diry;
    double dirz;
    double ekin;//MeV
    double weight;
    double time;//"shakes" (1e-8seconds)
  } ptrac_particle_t;

  //Open file:
  ptrac_file_t ptrac_open_file(const char * filename);

  //Query header info:

  //load next particle (null indicates eof):
  const ptrac_particle_t * ptrac_load_particle(ptrac_file_t);

  //close file and release resources:
  void ptrac_close_file(ptrac_file_t);

  //Advanced info about file layout:

  ////////////////////////////////////////////////////////////////////////////
  //                                                                        //
  // Utility functions for converting between particle codes used in ptrac  //
  // files from TRIPOLI-4 and the codes from the Particle Data Group:       //
  //                                                                        //
  // http://pdg.lbl.gov/2014/reviews/rpp2014-rev-monte-carlo-numbering.pdf  //
  //                                                                        //
  // Note that all the functions here return 0 when the code could not be   //
  // converted. This might not be an error as such, but could indicate an   //
  // exotic particle which has no code assigned in the target TRIPOLI-4     //
  // scheme.                                                                //
  //                                                                        //
  // TRIPOLI-4 only supports neutrons (1<->2112), gammas (2<->22),          //
  // electrons (3<->?) and positrons (4<->?).                               //
  //                                                                        //
  ////////////////////////////////////////////////////////////////////////////

  int32_t conv_mcnp2pdg(int32_t);
  int32_t conv_pdg2mcnp(int32_t);

#ifdef __cplusplus
}
#endif

#endif
