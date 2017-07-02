#ifndef MCPL_G4MCPLGenerator_hh
#define MCPL_G4MCPLGenerator_hh

///////////////////////////////////////////////////////////////////////////////////
//                                                                               //
// This class opens the input_file in MCPL format provided in the constructor    //
// and use one of the particles found inside each time GeneratePrimaries(..) is  //
// called to generate a primary particle in the G4Event.                         //
//                                                                               //
// If it runs out of particles in the input file it will call abortRun on the    //
// run manager (normally a soft-abort). Thus, simply calling beamOn with a very  //
// high number of particles will ensure that all particles in the input_file     //
// will be used.                                                                 //
//                                                                               //
// If desired, reimplement and override the UseParticle function to ignore       //
// certain particles in the input file, or override the ModifyParticle method to //
// for instance translate or rotate input coordinates or perform time shifts or  //
// reweighing.                                                                   //
//                                                                               //
// This file can be freely used as per the terms in the LICENSE file.            //
//                                                                               //
// Written by Thomas Kittelmann, 2016-2017.                                      //
//                                                                               //
///////////////////////////////////////////////////////////////////////////////////

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ThreeVector.hh"
#include "G4String.hh"
#include "mcpl.h"
#include <map>

class G4ParticleDefinition;
class G4ParticleGun;

class G4MCPLGenerator : public G4VUserPrimaryGeneratorAction
{
  public:

    G4MCPLGenerator(const G4String& inputFile);
    virtual ~G4MCPLGenerator();
    virtual void GeneratePrimaries(G4Event*);

  protected:

    //Reimplement this to filter input particles (default implementation
    //accepts all particles):
    virtual bool UseParticle(const mcpl_particle_t*) const;

    //Reimplement this to change coordinates or weights of input particles
    //before using them (does nothing by default):
    virtual void ModifyParticle( G4ThreeVector& pos, G4ThreeVector& dir,
                                 G4ThreeVector& pol, G4double& time,
                                 G4double& weight ) const;

  private:

    G4MCPLGenerator& operator=(const G4MCPLGenerator&);
    G4MCPLGenerator(const G4MCPLGenerator&);
    void FindNext();
    G4ParticleDefinition* LookupPDG(G4int);

    mcpl_file_t m_mcplfile;
    const mcpl_particle_t * m_p;
    G4ParticleGun * m_gun;
    G4int m_currentPDG;
    G4ParticleDefinition* m_currentPartDef;
    std::map<G4int,G4ParticleDefinition*> m_pdg2pdef;
    unsigned long long m_nUnknownPDG;
    G4String m_inputFile;
};

#endif
