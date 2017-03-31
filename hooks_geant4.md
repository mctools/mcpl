---
title: MCPL hooks for Geant4
underconstruction: true
weight: 50
---

- two magic lines for toc
{:toc}

The interface between MCPL and [Geant4](http://geant4.cern.ch/) consists of two classes, [G4MCPLGenerator]({{"/blob/master/src/geant4/G4MCPLGenerator.hh" | prepend: site.github.repository_url }}) and [G4MCPLWriter]({{"/blob/master/src/geant4/G4MCPLWriter.hh" | prepend: site.github.repository_url }}) (currently provided as part of the [MCPL distribution](LOCAL:get) itself), which users can use to either generate primary events from the particles in an existing MCPL file (1 particle per event), or to capture the particle state of particles entering one or more specified volumes in the simulation geometry and write them to a new MCPL file. A detailed description of the classes as well as how to use them is given in {% include linkpaper.html subsection=3.1 %}, and the present page will merely provide examples for the most basic usage as well as a brief discussion of the to actually integrate the MCPL code in your Geant4 setup.

# Basic usage examples

In order to use the 

## Using MCPL files as simulation input via G4MCPLGenerator

(todo)

```c++
#include "G4MCPLGenerator.hh"
#include "G4RunManager.hh"
#include <limits>

//Not shown here: Code defining MyGeometry and MyPhysicsList.

int main( int argc, char** argv ) {

  G4RunManager runManager;
  runManager.SetUserInitialization(new MyGeometry);
  runManager.SetUserInitialization(new MyPhysicsList);
  runManager.SetUserAction(new G4MCPLGenerator("myfile.mcpl"));
  runManager.Initialize();
  runManager.BeamOn(std::numeric_limits<G4int>::max());

  return 0;
}
```

## Creating MCPL files from simulations via G4MCPLWriter

(todo)

```c++
//Provide output filename when creating G4MCPLWriter instance:
G4MCPLWriter * mcplwriter = new G4MCPLWriter("myoutput.mcpl");

//Optional calls which add meta-data or change flags:
mcplwriter->AddComment("Some useful description here");
mcplwriter->AddData( ... );
mcplwriter->EnableDoublePrecision();
mcplwriter->EnablePolarisation();
mcplwriter->EnableUniversalWeight(1.0);

//Register with G4SDManager and on one or more logical
//volumes to activate:
G4SDManager::GetSDMpointer()->AddNewDetector(mcplwriter);
alogvol->SetSensitiveDetector(mcplwriter);
```

# Integrating MCPL in a given Geant4 setup

Note that in order to actually use the `G4MCPLGenerator` and `G4MCPLWriter`, the [C++ files in which they reside]({{"/raw/master/src/geant4/" | prepend: site.github.repository_url }}) should either be copied into your existing build system (along with [mcpl.h and mcpl.c]({{"/raw/master/src/mcpl/" | prepend: site.github.repository_url }})), or alternatively one can simply build and install the MCPL distribution itself via the provided CMake script after first installing Geant4 (more [here](LOCAL:get)), which should result in an installation which includes files like (actual contents might depend a bit on your platform and setup, for instance the extension `.so` will likely become `.dylib` on OS X):

```
├── bin/
│   └── mcpltool
├── include/
│   ├── G4MCPLGenerator.hh
│   ├── G4MCPLWriter.hh
│   └── mcpl.h
└── lib/
    ├── libg4mcpl.so
    └── libmcpl.so
```

Next, make sure that the build system in which you work on your Geant4 code will include the `include/` directory above in the compilers include path (so you can for instance do `#include "G4MCPLGenerator.hh"` in your code), and that your application is linked with the two libraries in the `lib/` directory above.
