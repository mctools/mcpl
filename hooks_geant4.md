---
title: MCPL hooks for Geant4
underconstruction: false
weight: 50
---

- two magic lines for toc
{:toc}

The interface between MCPL and [Geant4](http://geant4.cern.ch/) consists of two classes, [G4MCPLGenerator]({{"/blob/master/src/geant4/G4MCPLGenerator.hh" | prepend: site.github.repository_url }}) and [G4MCPLWriter]({{"/blob/master/src/geant4/G4MCPLWriter.hh" | prepend: site.github.repository_url }}) (currently provided as part of the [MCPL distribution](LOCAL:get) itself), which users can use to either generate primary events from the particles in an existing MCPL file (1 particle per event), or to capture the particle state of particles entering one or more specified volumes in the simulation geometry and write them to a new MCPL file. A detailed description of the classes as well as how to use them is given in {% include linkpaper.html subsection=3.1 %}, and the present page will merely provide examples for the most basic usage as well as a brief discussion of how to actually integrate the MCPL code in your Geant4 setup.

Note that users of the [ESS-dgcode framework](https://confluence.esss.lu.se/x/lgDD) have more powerful Geant4-MCPL hooks available out of the box, and they should refer to the [relevant documentation](https://confluence.esss.lu.se/x/xIDcBw) rather than the present page.

# Basic usage examples

## Using MCPL files as simulation input via G4MCPLGenerator

The `G4MCPLGenerator` class is a subclass of Geant4's `G4VUserPrimaryGeneratorAction` interface class, and can be activated in the usual manner for such classes. The name of the MCPL file to be used as input must be provided in the form of a string to the constructor of`G4MCPLGenerator`. Additionally, if the MCPL file runs out of particles (which it will eventually if Geant4 is requested to simulate more events than there are particles in the MCPL file), the `G4MCPLGenerator` will graciously request the `G4RunManager` to abort the simulation. Thus, a convenient way in which to use the entire input file for simulation is to launch the simulation with a very high number of events requested, as is shown in the following example:

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

For advanced use-cases, it is possible to fine-tune the way the particles from the input MCPL file are used. For instance, it is possible to apply a filter in order to ignore some of the particles, or to modify their properties (e.g. performing coordinate transformations, time-shifting or re-weighting). In order to do so, the user must sub-class the `G4MCPLGenerator` and overwrite one or two methods as relevant. Refer to the detailed instructions in {% include linkpaper.html subsection=3.1
%} for more information.

## Creating MCPL files from simulations via G4MCPLWriter

The `G4MCPLWriter` class is a subclass of Geant4's `G4VSensitiveDetector` interface class, and can be activated in the usual manner for such classes. In the default configuration it “consumes” all particles which, during a simulation, enter any geometrical volume(s) to which it is attached by the user and stores them into the MCPL file which was specified as an argument to its constructor. It also asks Geant4 to end further simulation of those particles (“killing” them), in order to avoid potential issues of double-counting.

It is of course also possible to add meta-data to, or otherwise modify the settings of, the newly created MCPL file. The following code sample illustrate the typical usage pattern (`alogvol` is here a logical volume in Geant4, chosen by the user according to their needs):

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

For advanced use-cases, it is possible to fine-tune the way the particles are captured and whether they are "killed" or merely recorded, and it is also possible to fill custom information into the MCPL _userflags_ in the resulting file. In order to do either, the user must sub-class the `G4MCPLGenerator` and overwrite the relevant method(s). Refer to the detailed instructions in {% include linkpaper.html subsection=3.1
%} for more information.

# Integrating MCPL in a given Geant4 setup

Note that in order to actually use the `G4MCPLGenerator` and `G4MCPLWriter` classes, the simplest approach might be to copy the [C++ files in which they reside]({{"/raw/master/src/geant4/" | prepend: site.github.repository_url }}) into your existing build system (along with [mcpl.h and mcpl.c]({{"/raw/master/src/mcpl/" | prepend: site.github.repository_url }})).

Alternatively, a perhaps more "clean" approach would be to first build and install the MCPL distribution itself via the provided CMake script after first installing Geant4 and making sure Geant4 is noticed correctly during the configuration (more [here](LOCAL:get)). This should, after the build and install is completed (with `make install`) result in an installation which includes files like the following (actual contents might depend a bit on your platform and setup, for instance the extension `.so` will usually be `.dylib` on OS X):

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

Next, make sure that the build system in which you work on your Geant4 code will include the `include/` directory above in the compiler's include path (so you can for instance do `#include "G4MCPLGenerator.hh"` in your code), and that your application is linked with the two libraries in the `lib/` directory above. It might also be a good idea to add the `bin/` directory above to your `PATH` environmental variable, so you have access to the `mcpltool` in order to easily inspect and modify MCPL files from [the command line](LOCAL:usage_cmdline).
