#include "ptracmcpl.h"

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// ptrac2mcpl : a simple command line utility for converting PTRAC files from      //
//              MCNP(X) to MCPL.                                                   //
//                                                                                 //
// Written 2021, osiris.abbate@ib.edu.ar (Instituto Balseiro).                     //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////

int main(int argc,char** argv) {
  return ptrac2mcpl_app(argc,argv);
}
