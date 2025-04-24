---
title: Using MCPL
weight: 30
underconstruction: true
---

Using MCPL typically implies using pre-existing [plugins or converters](LOCAL:hooks/) to either create or read a list of particles from MCPL files via a given simulation tool, such as [Geant4](LOCAL:hooks_geant4/), [McStas](LOCAL:hooks_mcstas/), [McXtrace](LOCAL:hooks_mcxtrace/), [MCNP](LOCAL:hooks_mcnp/), or [PHITS](LOCAL:hooks_phits/). Additionally, most users will find it beneficial to use the generic [mcpltool](LOCAL:usage_cmdline/) or [pymcpltool](LOCAL:usage_cmdline/) commands from the command line, in order to inspect or perform operations on files, and some users with advanced use-cases might write [C/C++ code](LOCAL:usage_c/) or [Python code](LOCAL:usage_python/) in order to inspect or manipulate MCPL files (for instance, to create new plugins or converters for their tools).

Many more details can be found in {% include linkpaper.html section=2 %} and in {% include linkpaper.html section=3 %}.
