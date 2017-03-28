---
title: MCPL hooks in McXtrace
underconstruction: true
weight: 30
---

This page has yet to be fully written. For now, in addition to the few notes
below, refer to the almost complete information in: {% include linkpaper.html
subsection=3.3 %}.

Users of McXtrace do not need to download MCPL themselves, as it is included
inside McXtrace already since version 1.4. This gives access to two components,
MCPL_input and MCPL_output as described in {% include linkpaper.html
subsection=3.3 %}, as well as the mcpltool command described
[here](LOCAL:usage_cmdline).

## Notes for users running in special environments

As from release 1.4 of McXtrace, linking to the MCPL-library
distributed with McXtrace is **automatic when using the GUI or the utility
scripts like mxrun**. If neither is available, such as may be the case in an HPC-environment,
library and include paths must be added to the build step. An example of this
could be (assuming McXtrace is installed in /usr/share/mcxtrace/1.3):

```shell
mcxtrace -t MyInstrument.instr 
cc -o MyInstrument.out MyInstrument.c \
   -I/usr/share/mcxtrace/1.4/libs/mcpl -L/usr/share/mcxtrace/1.4/libs/mcpl \
   -lmcpl -lm -O2
```

