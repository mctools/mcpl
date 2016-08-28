---
title: MCPL converters for MCNP
underconstruction: true
weight: 20
---

This page has yet to be written. For now refer to the almost complete
information in: {% include linkpaper.html subsection=3.2 %}.

## Quick and dirty way to get ssw2mcpl and mcpl2ssw

Rather than downloading and building the full MCPL distribution, it is possible to get hold
of the two commands discussed in the {% include linkpaper.html subsection=3.2
linkname="paper" %}, _ssw2mcpl_ and _mcpl2ssw_, simply by downloading and saving
the two single-file ("fat") versions of the code with via these links: {% include linkfile.html file="src_fat/ssw2mcpl_app_fat.c" %} and {% include linkfile.html file="src_fat/mcpl2ssw_app_fat.c" %}.

Next, go to a terminal and compile them with two commands (exchange "gcc" with the name of your compiler - e.g.
"clang" on OSX):

```shell
gcc -std=c99 -lm ssw2mcpl_app_fat.c -o ssw2mcpl
gcc -std=c99 -lm mcpl2ssw_app_fat.c -o mcpl2ssw
```

And you are ready to run! For instance:

```shell
./ssw2mcpl <my-ssw-file> <my-mcpl-file>
```

Or get full usage instructions with:

```shell
./ssw2mcpl --help
./mcpl2ssw --help
```
