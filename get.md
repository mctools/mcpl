---
title: Get MCPL
weight: 9999
---
You can use the [tar.gz]({{site.github.tar_url|replace: "/gh-pages","/master"}}),
 [zip]({{site.github.zip_url|replace: "/gh-pages","/master"}})
 or [github]({{site.github.repository_url}}) links above
to download the latest MCPL distribution. But take note that if you are a user
of [McStas](LOCAL:hooks_mcstas), [McXtrace](LOCAL:hooks_mcxtrace) or the
[ESS-dgcode framework](https://confluence.esss.lu.se/x/lgDD), you likely
already have MCPL available through the framework you are using.

After downloading the MCPL
[tar-ball]({{site.github.tar_url|replace: "/gh-pages","/master"}})
or [zip-file]({{site.github.zip_url|replace: "/gh-pages","/master"}}),
unpack it somewhere and follow the instructions in the
[INSTALL]({{"/raw/master/INSTALL" | prepend: site.github.repository_url }})
file for how to proceed to build and install using either CMake (to build everything including examples) or a simple Makefile or compilation command (to build just "fat" versions of [mcpltool](LOCAL:usage_cmdline), ssw2mcpl and mcpl2ssw executables).

For more details, refer to the information in the
[INSTALL]({{"/raw/master/INSTALL" | prepend: site.github.repository_url }})
file of your tar-ball, and to the discussion in:
{% include linkpaper.html subsection=2.5 %}.

To start playing around with the [mcpltool](LOCAL:usage_cmdline), we also provide a small sample MCPL file with the distribution: [example.mcpl]({{"/raw/master/examples/example.mcpl" | prepend: site.github.repository_url }}).
