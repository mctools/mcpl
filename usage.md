---
title: Using MCPL
underconstruction: true
weight: 30
---

Using MCPL typically implies using pre-existing plugins or converters to either create or read a list of particles from MCPL files via a given simulation tool. Additionally, most users will find it beneficial to use the generic `mcpltool` command from the command line, in order to inspect or perform operations on files, and some users with advanced use-cases might write C or C++ code in order to manipulate MCPL files (for instance, to create new plugins or converters for their tools).

Many more details can be found in {% include linkpaper.html section=2 %}, or in the pages below:

* Generic access:
  * [Use mcpl.h from C or C++.](LOCAL:usage_c)
  * [Use mcpltool from the command line.](LOCAL:usage_cmdline)
* [Using plugins and converters for specific applications](LOCAL:hooks):
  * [Geant4](LOCAL:hooks_geant4)
  * [McStas](LOCAL:hooks_mcstas)
  * [McXtrace](LOCAL:hooks_mcxtrace)
  * [MCNP](LOCAL:hooks_mcnp)
