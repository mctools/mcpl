---
title: MCPL hooks in McStas
underconstruction: false
weight: 40
---

- two magic lines for toc
{:toc}

MCPL input or output from [McStas](http://mcstas.org) is handled via two
components,
[MCPL_input](http://mcstas.org/download/components/misc/MCPL_input.html) and
[MCPL_output](http://mcstas.org/download/components/misc/MCPL_output.html),
which users can activate by adding entries at relevant points in their
instrument files. Please refer to {% include linkpaper.html subsection=3.3
%} for a more detailed discussion of these.

Users of McStas do not need to download MCPL themselves, as it is included
inside McStas already since version 2.3 (_but note that McStas 2.3 users need to
update their components [as explained
here](#notes-for-users-of-mcstas-version-23)_). In addition to the
[MCPL_input](http://mcstas.org/download/components/misc/MCPL_input.html) and
[MCPL_output](http://mcstas.org/download/components/misc/MCPL_output.html)
components, this also gives McStas users access to the
[mcpltool](LOCAL:usage_cmdline/) command.

## How to use the components

### MCPL_input

In its most simple form, users can add the following lines to their instrument
files in order to inject particles from an MCPL file into their instrument
simulations:

```c
COMPONENT vin = MCPL_input( filename="myfile.mcpl" )
AT(0,0,0) RELATIVE Origin
```

The initial position of the particles will be given by the coordinates found in
the MCPL file, relative to the position of the MCPL_input component in the
instrument. In the example above, the particle coordinates will thus be
interpreted as being relative to the Origin component.

For further details, refer to {% include linkpaper.html subsection=3.3
%} and/or bring up documentation specific to the actual version of MCPL_input
being used by typing:

```shell
mcdoc MCPL_input
```

### MCPL_output

In its most simple form, users can add the following lines to their instrument
files at a given point in order to capture a snapshot of particles at that point
in their instrument simulations and store them in an MCPL file:


```c
COMPONENT mcplout = MCPL_output( filename="myoutput.mcpl" )
AT(0,0,0) RELATIVE PREVIOUS
```

The coordinates of the stored particle will be relative to the MCPL_output
component itself. Thus, the above lines captures particles relative to the
previous component. This could for instance make sense if the previous component
was the sample component, and you need the coordinates to be written to be
relative to the sample position. If instead you need the coordinates to be
absolute, you could either specify `ABSOLUTE` or the `Origin` component:

```c
COMPONENT mcplout = MCPL_output( filename="myoutput.mcpl" )
AT(0,0,0) RELATIVE ABSOLUTE
```

For further details, refer to {% include linkpaper.html subsection=3.3
%} and/or bring up documentation specific to the actual version of MCPL_output
being used by typing:

```shell
mcdoc MCPL_output
```

## Notes for users of McStas version 2.3

If you are an user of McStas version 2.3, you should download an updated version
of the component you will be using and place it in your run directory:

* [MCPL_input.comp](https://raw.githubusercontent.com/McStasMcXtrace/McCode/18b94253d61fa91e5f4f7859f59ed7636a343ff7/mcstas-comps/misc/MCPL_input.comp)
* [MCPL_output.comp](https://raw.githubusercontent.com/McStasMcXtrace/McCode/409a9f6a333f22c30074f0f015e19b16bb9f513f/mcstas-comps/misc/MCPL_output.comp)

This is because several important issues were identified and fixed in the
component codes after the release (in particular a nasty memory leak in
MCPL_output).

## Notes for users running in special environments

As from release 2.3 of McStas, linking to the MCPL-library distributed with
McStas is **automatic when using the GUI or the utility scripts like mcrun**. If
neither is available, such as may be the case in an HPC-environment, library and
include paths must be added to the build step. An example of this could be
(assuming McStas is installed in /usr/share/mcstas/2.3):

```shell
mcstas -t MyInstrument.instr 
cc -o MyInstrument.out MyInstrument.c \
   -I/usr/share/mcstas/2.3/libs/mcpl -L/usr/share/mcstas/2.3/libs/mcpl \
   -lmcpl -lm -O2
```
