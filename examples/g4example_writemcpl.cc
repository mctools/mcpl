///////////////////////////////////////////////////////////////////////////////////
//                                                                               //
// Simple example of simulating a 10 GeV proton impinging on a box of lead and   //
// using a detector volume on the backside to capture all particles reaching it  //
// and store them in an MCPL file.                                               //
//                                                                               //
// This file can be freely used as per the terms in the LICENSE file.            //
//                                                                               //
// Written by Thomas Kittelmann, 2016.                                           //
//                                                                               //
///////////////////////////////////////////////////////////////////////////////////

#include "G4MCPLWriter.hh"
#include "G4RunManager.hh"
#include "G4VUserDetectorConstruction.hh"
#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4PhysListFactory.hh"
#include "G4NistManager.hh"
#include "G4ParticleGun.hh"
#include "G4SystemOfUnits.hh"
#include "G4Box.hh"
#include "G4PVPlacement.hh"
#include "G4SDManager.hh"

class MyGeo : public G4VUserDetectorConstruction {
public:
  MyGeo(){}
  virtual ~MyGeo(){}
  virtual G4VPhysicalVolume* Construct()
  {
    G4Material * mat_vacuum = G4NistManager::Instance()->FindOrBuildMaterial("G4_Galactic",true);
    G4Material * mat_lead = G4NistManager::Instance()->FindOrBuildMaterial("G4_Pb",true);
    G4LogicalVolume * world_log = new G4LogicalVolume(new G4Box("World",1*CLHEP::m,1*CLHEP::m,0.4*CLHEP::m),
                                                      mat_vacuum,"World",0,0,0);
    G4PVPlacement * world_phys = new G4PVPlacement(0,G4ThreeVector(),world_log,"World",0,false,0);

    G4LogicalVolume * target_log = new G4LogicalVolume(new G4Box("Target",1*CLHEP::m, 1*CLHEP::m, 0.1*CLHEP::m),
                                                       mat_lead,"Target",0,0,0);
    new G4PVPlacement(0,G4ThreeVector(0.0,0.0,0.1*CLHEP::m),target_log,"Target",world_log,false,0);
    G4LogicalVolume * detector_log = new G4LogicalVolume(new G4Box("Detector",1*CLHEP::m, 1*CLHEP::m, 0.1*CLHEP::m),
                                                         mat_lead,"Detector",0,0,0);
    new G4PVPlacement(0,G4ThreeVector(0.0,0.0,0.3*CLHEP::m),detector_log,"Detector",world_log,false,0);

    //Setup our mcpl writer and register it as a sensitive detector on the desired volume(s):

    G4MCPLWriter * mcplwriter = new G4MCPLWriter("myoutput.mcpl");

    mcplwriter->AddComment( "Transmission spectrum from 10GeV proton beam on 20cm lead" );
    // mcplwriter->AddComment( ... );          //optionally add comment to header
    // mcplwriter->AddData( ... );             //optionally add binary data blob(s) to header
    // mcplwriter->EnableDoublePrecision();    //optionally enable double precision storage
    // mcplwriter->EnablePolarisation();       //optionally enable storage of polarisation vectors
    // mcplwriter->EnableUniversalWeight(1.0); //optionally enable universal weight

    G4SDManager::GetSDMpointer()->AddNewDetector( mcplwriter );
    detector_log->SetSensitiveDetector(mcplwriter);

    return world_phys;
  }
};

class MyGun : public G4VUserPrimaryGeneratorAction {
public:

  MyGun() : m_gun(new G4ParticleGun(1)) {
    m_gun->SetParticleDefinition(G4ParticleTable::GetParticleTable()->FindParticle("proton"));
    m_gun->SetParticleEnergy(10*CLHEP::GeV);
    m_gun->SetParticlePosition(G4ThreeVector(0.0, 0.0, -1.0*CLHEP::cm));
    m_gun->SetParticleMomentumDirection(G4ThreeVector(0.0, 0.0, 1.0));
  }

  virtual ~MyGun() {
    delete m_gun;
  }

  void GeneratePrimaries(G4Event* evt) {
    m_gun->GeneratePrimaryVertex(evt);
  }

private:
  G4ParticleGun* m_gun;
};

int main( int, char** ) {

  CLHEP::HepRandom::setTheSeed(123456);
  G4RunManager* rm = new G4RunManager;
  rm->SetUserInitialization(new MyGeo);
  rm->SetUserInitialization(G4PhysListFactory().GetReferencePhysList("QGSP_BERT"));
  rm->SetUserAction(new MyGun);
  rm->Initialize();
  rm->BeamOn(10);
  delete rm;
  return 0;
}
