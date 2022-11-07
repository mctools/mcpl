#ifndef ssvread_h
#define ssvread_h

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// Code for reading ASCII SSV files (space sep. values).                           //
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
  } ssv_file_t;

  typedef struct {
    long pdgcode;//rawtype converted to PDG codes.
    float ekin;//MeV
    float x;//cm
    float y;//cm
    float z;//cm
    float dirx;
    float diry;
    float dirz;
    float time;//ms
    float weight;
    float polx;
    float poly;
    float polz;
    int uf;
  } ssv_particle_t;

  //Open file:
  ssv_file_t ssv_open_file(const char * filename);

  //Query header info:

  //load next particle (null indicates eof):
  const ssv_particle_t * ssv_load_particle(ssv_file_t);

  //close file and release resources:
  void ssv_close_file(ssv_file_t);

#ifdef __cplusplus
}
#endif

#endif
