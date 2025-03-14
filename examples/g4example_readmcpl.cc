
////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  This file is part of MCPL (see https://mctools.github.io/mcpl/)           //
//                                                                            //
//  Copyright 2015-2025 MCPL developers.                                      //
//                                                                            //
//  Licensed under the Apache License, Version 2.0 (the "License");           //
//  you may not use this file except in compliance with the License.          //
//  You may obtain a copy of the License at                                   //
//                                                                            //
//      http://www.apache.org/licenses/LICENSE-2.0                            //
//                                                                            //
//  Unless required by applicable law or agreed to in writing, software       //
//  distributed under the License is distributed on an "AS IS" BASIS,         //
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  //
//  See the License for the specific language governing permissions and       //
//  limitations under the License.                                            //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

// Simple example which uses the G4MCPLGenerator to shoot particles from an MCPL
// file into a large empty box, and enabling verbose tracking output to get
// resulting particles printed.

//fixme: move this file elsewhere?

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
