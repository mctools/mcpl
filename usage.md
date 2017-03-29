---
title: Using MCPL
underconstruction: true
weight: 30
---

Using MCPL typically implies using pre-existing [plugins or converters](LOCAL:hooks) to either create or read a list of particles from MCPL files via a given simulation tool, such as [Geant4](LOCAL:hooks_geant4), [McStas](LOCAL:hooks_mcstas), [McXtrace](LOCAL:hooks_mcxtrace) or [MCNP](LOCAL:hooks_mcnp). Additionally, most users will find it beneficial to use the generic [mcpltool](LOCAL:usage_cmdline) command from the command line, in order to inspect or perform operations on files, and some users with advanced use-cases might [write C or C++ code](LOCAL:usage_c) in order to manipulate MCPL files (for instance, to create new plugins or converters for their tools).

Many more details can be found in {% include linkpaper.html section=2 %}.
