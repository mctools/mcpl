
///////////////////////////////////////////////////////////////////////////////////
//                                                                               //
// Simple example which uses the G4MCPLGenerator to shoot particles from an MCPL //
// file into a large empty box, and enabling verbose tracking output to get      //
// resulting particles printed.                                                  //
//                                                                               //
// This file can be freely used as per the terms in the LICENSE file.            //
//                                                                               //
// Written by Thomas Kittelmann, 2016.                                           //
//                                                                               //
///////////////////////////////////////////////////////////////////////////////////


#include "G4MCPLGenerator.hh"

#include "G4RunManager.hh"
#include "G4VUserDetectorConstruction.hh"
#include "G4PhysListFactory.hh"
#include "G4NistManager.hh"
#include "G4Box.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4UImanager.hh"
#include <limits>

class MyGeo : public G4VUserDetectorConstruction {
public:
  MyGeo(){}
  virtual ~MyGeo(){}
  virtual G4VPhysicalVolume* Construct()
  {
    G4Material * mat_vacuum = G4NistManager::Instance()->FindOrBuildMaterial("G4_Galactic",true);
    G4VSolid * world_shape = new G4Box("World",1*CLHEP::km,1*CLHEP::km,1*CLHEP::km);
    G4LogicalVolume * world_log = new G4LogicalVolume(world_shape,mat_vacuum,"World");
    G4PVPlacement * world_phys = new G4PVPlacement(0,G4ThreeVector(),world_log,"World",0,false,0);
    return world_phys;
  }
};

int main( int argc, char** argv ) {

  if (argc!=2) {
    G4cout << "Please specify exactly one MCPL file to use for event generation." << G4endl;
    return 1;
  }

  CLHEP::HepRandom::setTheSeed(123456);//set seed for better reproducibility (in
                                       //case of unstable particles in the
                                       //input).
  G4RunManager runManager;
  runManager.SetUserInitialization(new MyGeo);
  runManager.SetUserInitialization(G4PhysListFactory().GetReferencePhysList("QGSP_BERT"));
  runManager.SetUserAction(new G4MCPLGenerator(argv[1]));
  runManager.Initialize();

  if ( G4UImanager::GetUIpointer()->ApplyCommand("/tracking/verbose 1") != fCommandSucceeded ) {
    G4cout << "Problems executing \"/tracking/verbose 1\". Aborting."<<G4endl;
    return 1;
  }

  runManager.BeamOn(std::numeric_limits<G4int>::max());

  return 0;
}
