#ifndef MCPL_G4MCPLWriter_hh
#define MCPL_G4MCPLWriter_hh

///////////////////////////////////////////////////////////////////////////////////
//                                                                               //
// This class implements a sensitive detector which when attached to one or more //
// logical volumes in the active geometry, cause the state (at the point of      //
// entry) of any simulated particle entering those volumes to be stored in an    //
// output MPCL file, whose name must be provided in the constructor of the       //
// class. Furthermore, in the default implementation, the particles are then     //
// "killed", to avoid potential double-counting issues, as are any particle      //
// created inside the volume.                                                    //
//                                                                               //
// Thus, attaching the G4MCPLWriter to a volume, in a sense makes it act like a  //
// black hole, sucking any particle entering it into the output MCPL file,       //
// rather than letting them continue simulation.                                 //
//                                                                               //
// If desired, this exact behaviour can be modified in a derived class by        //
// overriding the ProcessHits method and using the StorePreStep(..),             //
// StorePostStep(..) and Kill(..) protected methods inside as needed. Likewise,  //
// custom 32 bit user flags can be calculated for captured particles and stored  //
// in the output file, by overriding the UserFlags and UserFlagsDescription      //
// methods.                                                                      //
//                                                                               //
// This file can be freely used as per the terms in the LICENSE file.            //
//                                                                               //
// Written by Thomas Kittelmann, 2016-2017.                                      //
//                                                                               //
///////////////////////////////////////////////////////////////////////////////////

#include "G4VSensitiveDetector.hh"
#include "G4Track.hh"
#include "mcpl.h"

class G4MCPLWriter : public G4VSensitiveDetector
{
  public:

    //The constructor needs the name of the output MCPL file, and optionally the
    //name argument to be passed to the G4VSensitiveDetector constructor:
    G4MCPLWriter( const G4String& outputFile,
                  const G4String& name = "G4MCPLWriter" );

    //Destructor closes the output file:
    virtual ~G4MCPLWriter();

    //One or more calls to the following methods can be used to add comments or
    //data into the MCPL header, or to enable double-precision or polarisation
    //info in the information of stored particles. They must be called *before*
    //the first particle is stored in the file:
    void AddComment( const G4String& );
    void AddData( const G4String& dataKey, size_t dataLength, const char* data );
    void EnableDoublePrecision();
    void EnablePolarisation();
    void EnableUniversalWeight(G4double);

    //The default ProcessHits simply "consumes" all particles entering the
    //volume, in the sense that we store their state at pre-step as a particle
    //in the MCPL file and then we "kill" it, telling Geant4 to halt further
    //simulation of the particle. If different behaviour is desired, simply
    //override ProcessHits in a derived class (consider in that case to call
    //addComments(..)  from your derived constructor, to add a comment
    //describing the new behaviour):
    virtual G4bool ProcessHits(G4Step * step,G4TouchableHistory*);

    //If desired, custom flags in the form of a 32bit integer can be stored in
    //the mcpl output along with each particle. To do so, override the next two
    //methods to calculate the custom user flags for each step plus a general
    //comment describing those flags:
    virtual G4String UserFlagsDescription() const { return ""; }
    virtual uint32_t UserFlags(const G4Step*) const { return 0; }

  protected:
    //Methods that can be used inside ProcessHits to store particles into the
    //MCPL file and/or kill the track:
    void StorePreStep(const G4Step * step) { Store(step,step->GetPreStepPoint()); }
    void StorePostStep(const G4Step * step) { Store(step,step->GetPostStepPoint()); }
    void Kill(G4Step * step) { step->GetTrack()->SetTrackStatus(fStopAndKill); }

  private:
    G4MCPLWriter& operator=(const G4MCPLWriter&);
    G4MCPLWriter(const G4MCPLWriter&);
    void Store(const G4Step *, const G4StepPoint *);
    mcpl_outfile_t m_f;
    mcpl_particle_t m_p;
    bool m_store_polarisation;
    bool m_store_userflags;
};

#endif
