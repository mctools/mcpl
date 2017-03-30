---
title: MCPL converters for MCNP
underconstruction: true
weight: 20
---

The MCNP–MCPL interface currently supports MCNPX, MCNP5 and MCNP6 and exploits the existing MCNP capability to stop and subsequently restart simulations at a user-defined set of surfaces through the Surface Source
Write/Read (SSW/SSR) functionality into files. We refer to such files as "SSW files", although different names are occasionally used (e.g. "RSSA files"). The MCNP-MCPL interface is thus implemented as two standalone commandline converters: `ssw2mcpl` and `mcpl2ssw`. A detailed description of the commands, as well as references to the relevant MCNP manuals in which it is described how to enable the SSW functionality in a given MCNP _input deck_, is given in {% include linkpaper.html subsection=3.2 %} and the present page will merely provide a few typical usage examples.

At the bottom of the page is also included a quick and dirty recipe for how the `ssw2mcpl` and `mcpl2ssw` commands can be obtained without first downloading and installing the MCPL distribution. Note that users of the ESS dgcode framework already have access to the command, and it is planned to provide McStas and McXtrace users with them as well
(cf. [this issue]({{"/20"|prepend site.github.issues_url}})).

##Examples

todo

### Converting an SSW file to MCPL

todo

### Converting an MCPL file to SSW

todo

### Get full usage instructions

todo

## Quick and dirty way to get ssw2mcpl and mcpl2ssw

Rather than downloading and building the full MCPL distribution, it is possible to get hold
of the `ssw2mcpl` and `mcpl2ssw` commands simply by downloading and saving
the two single-file ("fat") versions of the code with via these links: {% include linkfile.html file="src_fat/ssw2mcpl_app_fat.c" %} and {% include linkfile.html file="src_fat/mcpl2ssw_app_fat.c"
%}.

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
