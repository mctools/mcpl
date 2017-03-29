---
title: Get MCPL
underconstruction: true
weight: 9999
---

This page has yet to be completed. For now refer to the almost complete
information in: {% include linkpaper.html subsection=2.5 %}.

You can use the [tar.gz]({{site.github.tar_url|replace: "/gh-pages","/master"}}),
 [zip]({{site.github.zip_url|replace: "/gh-pages","/master"}})
 or [github]({{site.github.repository_url}}) links above
to download the latest MCPL distribution. But take note that if you are a user
of [McStas](LOCAL:usage_mcstas), [McXtrace](LOCAL:usage_mcxtrace) or the
[ESS-dgcode framework](https://confluence.esss.lu.se/x/lgDD), you likely
already have MCPL available through the framework you are using.

After downloading the MCPL
[tar-ball]({{site.github.tar_url|replace: "/gh-pages","/master"}})
or [zip-file]({{site.github.zip_url|replace: "/gh-pages","/master"}}),
unpack it somewhere (/path/to/sourcedir), create and step into a third temporary directory
(/path/to/builddir) and configure, compile and install in a location of your
choice (/path/to/installdir) using the commands:

```shell
cmake /path/to/sourcedir -DCMAKE_INSTALL_PREFIX=/path/to/installdir
make install
```

After this is done, look in /path/to/installdir for the MCPL distribution.

{% if false %}
Should we provide a few example mcpl files for download, so people can
immediately play around?
{% endif %}
