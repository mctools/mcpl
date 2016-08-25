---
title: Using MCPL from the command line
underconstruction: true
---

This page has yet to be completed. For now refer to the almost complete
information in: {% include linkpaper.html subsection=2.3 %}.

{% if false %}

```shell
$ mcpltool myoutput.mcpl.gz
```
```
Opened MCPL file myoutput.mcpl.gz:

  Basic info
    Format             : MCPL-2
    No. of particles   : 1106933
    Header storage     : 140 bytes
    Data storage       : 39849588 bytes

  Custom meta data
    Source             : "G4MCPLWriter [G4MCPLWriter]"
    Number of comments : 1
          -> comment 0 : "Transmission spectrum from 10GeV proton beam on 20cm lead"
    Number of blobs    : 0

  Particle data format
    User flags         : no
    Polarisation info  : no
    Fixed part. type   : no
    FP precision       : single
    Endianness         : little
    Storage            : 36 bytes/particle

index     pdgcode   ekin[MeV]       x[cm]       y[cm]       z[cm]          ux          uy          uz    time[ms]      weight
    0         211      487.02     -0.5898       1.835          20   -0.092407     0.20491     0.97441  7.3346e-07           1
    1          22      1.5326      1.0635      11.351          20    0.080441     0.66026     0.74672  1.0882e-06           1
    2          22      3.9526    -0.43907      8.6473          20    -0.56616     0.50558     0.65104  1.0286e-06           1
    3          22     0.82591      1.7444      9.7622          20    0.092099     0.79597     0.59829  1.0378e-06           1
    4          22      1.1958      2.1806      8.6416          20     0.21997     0.66435     0.71432  1.0124e-06           1
    5          22      1.2525      3.0949      7.7366          20     0.48903     0.30789     0.81612   1.013e-06           1
    6          22      2.6247       3.948       5.681          20     0.62503     0.64221     0.44374  9.1152e-07           1
    7        2212      824.28     -1.8797     -2.5124          20     -0.3077    -0.40496       0.861  7.6539e-07           1
    8        -211      3459.8    -0.79521     0.91481          20    -0.13441     0.14438     0.98035  7.0618e-07           1
    9        2112     0.30553      54.471      33.386          20      0.4862    0.011958     0.87377  0.00016442           1
```

bla

```shell
$ mcpltool --help
```
```
Tool for inspecting or modifying Monte Carlo Particle List (.mcpl) files.

The default behaviour is to display the contents of the FILE in human readable
format (see Dump Options below for how to modify what is displayed).

This installation supports direct reading of gzipped files (.mcpl.gz).

Usage:
  mcpltool [dump-options] FILE
  mcpltool --merge [merge-options] FILE1 FILE2
  mcpltool --repair FILE
  mcpltool --version
  mcpltool --help

Dump Options:
  By default include the info in the FILE header plus the first ten contained
  particles. Modify with the following options:
  -j, --justhead  : Dump just header info and no particle info.
  -n, --nohead    : Dump just particle info and no header info.
  -lN             : Dump up to N particles from the file (default 10). You
                    can specify -l0 to disable this limit.
  -sN             : Skip past the first N particles in the file (default 0).
  -bKEY           : Dump binary blob stored under KEY to standard output.

Merge Options:
  -m, --merge FILE1 FILE2
                    Appends the particle contents in FILE2 to the end of FILE1.
                    Note that this will fail unless FILE1 and FILE2 have iden-
                    tical headers (but see option --ignore below).
  -i, --ignore      Ignore comments and binary blobs in FILE2. This allows some
                    otherwise forbidden merges, but some info might get lost.

Other options:
  -r, --repair FILE
                    Attempt to repair FILE which was not properly closed, by up-
                    dating the file header with the correct number of particles.
  -v, --version   : Display version of MCPL installation.
  -h, --help      : Display this usage information (ignores all other options).

```
{% endif %}
