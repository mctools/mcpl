---
title: Monte Carlo Particle Lists
notitleheader: true
slug: home
weight: 999999
underconstruction: true
---


![MCPL support](/assets/mcpl_support_diagram.png){: .align-right width="50%" }

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
both quick recipes and updated information where needed. You can [install](LOCAL:get/)
and try out the MCPL code right away, or use the
menu above to navigate to more information.

* April 2025:
  The milestone release MCPL [v2.0.0](https://github.com/mctools/mcpl/releases/tag/v2.0.0) is out! Most notably this release brings support for Windows, and `pip install mcpl` now provides fully-fledged MCPL installations. The release includes many other changes to both license, packaging and how the project is developed, so be sure to consult the [release announcement](https://github.com/mctools/mcpl/releases/tag/v2.0.0) for all details.
* November 2022-June 2023:
  Several minor maintenance updates were released:
  [v1.5.1](https://github.com/mctools/mcpl/releases/tag/v1.5.1),
  [v1.6.0](https://github.com/mctools/mcpl/releases/tag/v1.6.0),
  [v1.6.1](https://github.com/mctools/mcpl/releases/tag/v1.6.1), and
  [v1.6.2](https://github.com/mctools/mcpl/releases/tag/v1.6.2).
* October 14, 2022:
  MCPL is now available on conda! Specifically in the [conda-forge](https://conda-forge.org/)
  channel.  Thus, `conda install -c conda-forge mcpl` now gives access to all the various
  [command-line tools](LOCAL:usage_cmdline), and API's for [C/C++](LOCAL:usage_c),
  [Python](LOCAL:usage_python), and CMake.
* October 5, 2022:
  [v1.5.0](https://github.com/mctools/mcpl/releases/tag/v1.5.0)
  released, introducing the `mcpl-config` command and making it easier
  for downstream CMake-based projects to locate MCPL.
* August 16, 2022:
  [v1.4.0](https://github.com/mctools/mcpl/releases/tag/v1.4.0)
  released, updating the CMake code to support integration with
  downstream CMake-based projects.
* February 9, 2020:
  [v1.3.2](https://github.com/mctools/mcpl/releases/tag/v1.3.2)
  released, fixing the time conversion in [phits2mcpl](LOCAL:hooks_phits)
  and [mcpl2phits](LOCAL:hooks_phits).
* June 29, 2019:
  [v1.3.1](https://github.com/mctools/mcpl/releases/tag/v1.3.1)
  released, with important bug-fixes for the [Python API](LOCAL:usage_python)
  and the [pymcpltool](LOCAL:usage_cmdline#extract-statistics-from-a-file).
* June 21, 2019:
  [v1.3.0](https://github.com/mctools/mcpl/releases/tag/v1.3.0)
  released. In addition to general maintenance, this release brings support for
  [PHITS](https://phits.jaea.go.jp/) and a new `mcpltool --forcemerge` option.
* September 26, 2018:
  [v1.2.3](https://github.com/mctools/mcpl/releases/tag/v1.2.3)
  released. This release brings support for MCNP 6.2.
* March 7, 2018:
  [v1.2.2](https://github.com/mctools/mcpl/releases/tag/v1.2.2)
  released. This is a pure maintenance release.
* January 26, 2018:
  MCPL is now available on the [Python Package Index](https://pypi.python.org/pypi/mcpl)!
  Thus, `pip install mcpl` now gives access to the [pymcpltool](LOCAL:usage_cmdline#extract-statistics-from-a-file)
  and the [mcpl Python module](LOCAL:usage_python).
* January 23, 2018:
  [v1.2.1](https://github.com/mctools/mcpl/releases/tag/v1.2.1)
  released. This is a pure maintenance release.
* July 4, 2017:
  [v1.2.0](https://github.com/mctools/mcpl/releases/tag/v1.2.0)
  released, bringing native [Python](LOCAL:usage_python) support and
  [pymcpltool](LOCAL:usage_cmdline#extract-statistics-from-a-file) to MCPL!
* April 20, 2017: The MCPL paper (describing MCPL v1.1.0) was accepted for publication in Computer
  Physics Communications with full Open Access:
  [doi:10.1016/j.cpc.2017.04.012](https://doi.org/10.1016/j.cpc.2017.04.012).
* March 29, 2017:
  [v1.1.0](https://github.com/mctools/mcpl/releases/tag/v1.1.0) released.
* September 7, 2016:
  [v1.0.0](https://github.com/mctools/mcpl/releases/tag/v1.0.0) released.
{:#mcplnewsbox}
