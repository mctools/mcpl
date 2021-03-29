#ifndef stockread_h
#define stockread_h

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// Code for reading ptrac files from TRIPOLI-4 (STORAGE).                          //
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
  } stock_file_t;

  typedef struct {
    double ekin;//MeV
    double x;//cm
    double y;//cm
    double z;//cm
    double dirx;
    double diry;
    double dirz;
    double weight;
    int rawtype;//raw particle type encoding (tripoli 'ipt': 1=n, 2=p, 3=e-, 4=e+)
    long pdgcode;//rawtype converted to PDG codes.
  } stock_particle_t;

  //Open file:
  stock_file_t stock_open_file(const char * filename);

  //Query header info:

  //load next particle (null indicates eof):
  const stock_particle_t * stock_load_particle(stock_file_t);

  //close file and release resources:
  void stock_close_file(stock_file_t);

  //Advanced info about file layout:

  ////////////////////////////////////////////////////////////////////////////
  //                                                                        //
  // Utility functions for converting between particle codes used in stock  //
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
  // electrons (3<->11) and positrons (4<->-11).                            //
  //                                                                        //
  ////////////////////////////////////////////////////////////////////////////

  int32_t conv_tripoli2pdg(int32_t);
  int32_t conv_pdg2tripoli(int32_t);

#ifdef __cplusplus
}
#endif

#endif
