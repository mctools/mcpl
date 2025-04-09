---
title: Get MCPL
weight: 9999
---
If using conda, you can simply install MCPL from the [conda-forge](https://conda-forge.org/)
channel.  Thus, `conda install -c conda-forge mcpl` gives access to all the various
[command-line tools](LOCAL:usage_cmdline), and API's for [C/C++](LOCAL:usage_c),
[Python](LOCAL:usage_python), and CMake.

Alternatively you can also install MCPL via, `pip install mcpl`, which gives
access to only the
[pymcpltool](LOCAL:usage_cmdline#extract-statistics-from-a-file) and the [mcpl
Python module](LOCAL:usage_python). If possible, the installation via conda is
recommended.

NOTICE: In the near future (spring 2025), MCPL 2.0.0 will be released, which
will include both Windows support and fully functional PyPI releases. After that
point, `pip install mcpl` should give you a fully-fledged MCPL installation on
all platforms.

Finally, you can of course also use the [tar.gz]({{site.github.tar_url|replace: "/gh-pages","/master"}}),
 [zip]({{site.github.zip_url|replace: "/gh-pages","/master"}})
 or [github]({{site.github.repository_url}}) links
to download source files for the latest MCPL distribution. But take note that if you are a user
of [McStas](LOCAL:hooks_mcstas/), [McXtrace](LOCAL:hooks_mcxtrace/) or the
[simplebuild-dgcode framework](https://mctools.github.io/simplebuild-dgcode/), you likely
already have MCPL available through the framework you are using.

After downloading the MCPL
[tar-ball]({{site.github.tar_url|replace: "/gh-pages","/master"}})
or [zip-file]({{site.github.zip_url|replace: "/gh-pages","/master"}}),
unpack it somewhere and follow the instructions in the
[INSTALL]({{"/raw/master/INSTALL" | prepend: site.github.repository_url }})
file for how to proceed to build and install using either CMake (to build
everything including examples) or a simple Makefile or compilation command (to
build just "fat" versions of [mcpltool](LOCAL:usage_cmdline/), ssw2mcpl,
mcpl2ssw, phits2mcpl, or mcpl2phits executables). Additional information can also be found in {% include linkpaper.html subsection=2.5 %}.

To start playing around with the [mcpltool](LOCAL:usage_cmdline/), we also provide a small sample MCPL file with the distribution: [example.mcpl]({{"/raw/master/examples/example.mcpl" | prepend: site.github.repository_url }}).
