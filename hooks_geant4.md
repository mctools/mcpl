---
title: MCPL hooks for Geant4
underconstruction: true
weight: 50
---

- two magic lines for toc
{:toc}

The interface between MCPL and [Geant4](http://geant4.cern.ch/) consists of two classes, `G4MCPLGenerator` and `G4MCPLWriter` (currently provided as part of the [MCPL distribution](LOCAL:get) itself), which users can use to either generate primary events from the particles in an existing MCPL file (1 particle per event), or to capture the particle state of particles entering one or more specified volumes in the simulation geometry and write them to a new MCPL file. A detailed description of the classes as well as how to use them is given in {% include linkpaper.html subsection=3.1 %}, and the present page will merely provide examples for the most basic usage as well as a brief discussion of the to actually integrate the MCPL code in your Geant4 setup.

# Basic usage examples

In order to use the 

## Using MCPL files as simulation input via G4MCPLGenerator

(todo)

## Creating MCPL files from simulations via G4MCPLWriter

(todo)

# Integrating MCPL in a given Geant4 setup

Note that in order to actually use the `G4MCPLGenerator` and `G4MCPLWriter`, the [C++ files in which they reside]({{"/raw/master/src/geant4/" | prepend: site.github.repository_url }}) should either be copied into your existing build system (along with [mcpl.h and mcpl.c]({{"/raw/master/src/mcpl/" | prepend: site.github.repository_url }})), or alternatively one can simply build and install the MCPL distribution itself via the provided CMake script after first installing Geant4 (more [here](LOCAL:get)), which should result in an installation which includes files like (actual contents might depend a bit on your platform and setup, for instance the extension `.so` will likely become `.dylib` on OS X):

```
├── bin
│   └── mcpltool
├── include
│   ├── G4MCPLGenerator.hh
│   ├── G4MCPLWriter.hh
│   └── mcpl.h
└── lib
    ├── libg4mcpl.so
    └── libmcpl.so
```
