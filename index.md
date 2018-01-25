---
title: Monte Carlo Particle Lists
notitleheader: true
slug: home
weight: 999999
---

Welcome to the home of MCPL, a binary file format for usage in physics simulations.

MCPL files contain lists of particle state information, and allows for easy
storage and interchange of particles between various Monte Carlo simulation
applications. It is implemented in portable C code and is made available to the
scientific community, along with converters and plugins for [several popular
simulation packages](LOCAL:hooks/).

MCPL is described in great detail in {% include
linkpaper.html linkname="the MCPL paper" %}, and in particular details of the file format itself can be
found in {% include linkpaper.html linkname="section 2"
section=2 %}. The present web-page serves as an online home for MCPL, providing
both quick recipes and updated information where needed. You can [download](LOCAL:get/)
and try out the MCPL distribution right away, or use the
menu above to navigate to more information.

* January 23, 2018:
  [v1.2.1](https://github.com/mctools/mcpl/releases/tag/v1.2.1)
  released. This is a pure maintenance release.
* July 4, 2017:
  [v1.2.0](https://github.com/mctools/mcpl/releases/tag/v1.2.0)
  released, bringing native [python](LOCAL:usage_python) support and
  [pymcpltool](LOCAL:usage_cmdline#extract-statistics-from-a-file) to MCPL!
* April 20, 2017: The MCPL paper (describing MCPL v1.1.0) was accepted for publication in Computer
  Physics Communications with full Open Access:
  [doi:10.1016/j.cpc.2017.04.012](https://doi.org/10.1016/j.cpc.2017.04.012).
* March 29, 2017:
  [v1.1.0](https://github.com/mctools/mcpl/releases/tag/v1.1.0) released.
{:#mcplnewsbox}