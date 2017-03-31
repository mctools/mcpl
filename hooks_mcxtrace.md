---
title: MCPL hooks in McXtrace
underconstruction: true
weight: 30
---

- two magic lines for toc
{:toc}

MCPL input or output from [McXtrace](http://mcxtrace.org) is handled via two
components, MCPL_input and MCPL_output, which users can activate by adding
entries at relevant points in their instrument files. Please refer to {% include linkpaper.html
subsection=3.3 %} for a more detailed discussion of these.

Users of McXtrace do not need to download MCPL themselves, as it is included
inside McXtrace already starting from version 1.4 (expected to be released spring 2017). In addition to the
MCPL_input and MCPL_output components, this also gives McXtrace users
access to the [mcpltool](LOCAL:usage_cmdline) command.

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
mxdoc MCPL_input
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
mxdoc MCPL_output
```

## Notes for users running in special environments

As from release 1.4 of McXtrace, linking to the MCPL-library distributed with
McXtrace is **automatic when using the GUI or the utility scripts like
mxrun**. If neither is available, such as may be the case in an HPC-environment,
library and include paths must be added to the build step. An example of this
could be (assuming McXtrace is installed in /usr/share/mcxtrace/1.4):

```shell
mcxtrace -t MyInstrument.instr 
cc -o MyInstrument.out MyInstrument.c \
   -I/usr/share/mcxtrace/1.4/libs/mcpl -L/usr/share/mcxtrace/1.4/libs/mcpl \
   -lmcpl -lm -O2
```
