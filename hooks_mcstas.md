---
title: MCPL hooks in McStas
underconstruction: true
weight: 40
---

- two magic lines for toc
{:toc}

This page has yet to be fully written. For now, in addition to the few notes
below, refer to the almost complete information in: {% include linkpaper.html
subsection=3.3 %}.

MCPL input or output from McStas is handled via two components, [MCPL_input](http://mcstas.org/download/components/misc/MCPL_input.html) and [MCPL_output](http://mcstas.org/download/components/misc/MCPL_output.html), which users can activate by adding entries at relevant points in their instrument files. Please refer to {% include linkpaper.html
subsection=3.3 %} for a more detailed discussion of these.

Users of McStas do not need to download MCPL themselves, as it is included
inside McStas already since version 2.3 (_but note that McStas 2.3 users need to update their components as explained further down, McStas 2.4 and later will hopefully be without such issues_). In addition to the
[MCPL_input](http://mcstas.org/download/components/misc/MCPL_input.html) and 
[MCPL_output](http://mcstas.org/download/components/misc/MCPL_output.html) components, this also gives access to the [mcpltool](LOCAL:usage_cmdline) command.

## How to use the components

(todo)

```c
COMPONENT vin = MCPL_input( filename="myfile.mcpl" )
AT(0,0,0) RELATIVE Origin
```

```c
COMPONENT mcplout = MCPL_output( filename="myoutput.mcpl" )
AT(0,0,0) RELATIVE PREVIOUS
```

## Notes for users of McStas version 2.3

If you are an user of McStas version 2.3, you should download an updated version of
the component you will be using and place it in your run directory:

* [MCPL_input.comp](https://raw.githubusercontent.com/McStasMcXtrace/McCode/18b94253d61fa91e5f4f7859f59ed7636a343ff7/mcstas-comps/misc/MCPL_input.comp)
* [MCPL_output.comp](https://github.com/McStasMcXtrace/McCode/blob/409a9f6a333f22c30074f0f015e19b16bb9f513f/mcstas-comps/misc/MCPL_output.comp)

This is because several important issues were identified and fixed in the
component codes after the release (in particular a nasty memory leak in MCPL_output).

## Notes for users running in special environments

As from release 2.3 of McStas, linking to the MCPL-library
distributed with McStas is **automatic when using the GUI or the utility
scripts like mcrun**. If neither is available, such as may be the case in an HPC-environment,
library and include paths must be added to the build step. An example of this
could be (assuming McStas is installed in /usr/share/mcstas/2.3):

```shell
mcstas -t MyInstrument.instr 
cc -o MyInstrument.out MyInstrument.c \
   -I/usr/share/mcstas/2.3/libs/mcpl -L/usr/share/mcstas/2.3/libs/mcpl \
   -lmcpl -lm -O2
```
