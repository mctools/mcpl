---
title: Using MCPL from the command line
weight: 20
---

- two magic lines for toc
{:toc}

The MCPL distribution includes a handy command-line tool, `mcpltool`, which can
be used to either inspect MCPL files, or to carry out a
limited number of operations on them.

This page includes a few examples of how `mcpltool` can be used, but users are referred to
{% include linkpaper.html subsection=2.3 %} for more information.

At the bottom of the page is also included a quick and dirty recipe for how the `mcpltool` command can be obtained without first downloading and installing the MCPL distribution (note that users of McStas, McXtrace and the ESS dgcode framework already have access to the command).

## Examples

A few examples of how to use the `mcpltool` are provided here. Note that a small sample MCPL file is included with the MCPL distribution at [examples/example.mcpl]({{"/raw/master/examples/example.mcpl" | prepend: site.github.repository_url }}), in case new users would like something to try the `mcpltool` on.

### Inspect file contents

Simply invoking `mcpltool` on a file with no additional arguments, results in a summary of the header information being printed, in addition to the particle state information of the first ten particles in the file:

```shell
$ mcpltool example.mcpl
```
```
Opened MCPL file example.mcpl:

  Basic info
    Format             : MCPL-3
    No. of particles   : 1006
    Header storage     : 140 bytes
    Data storage       : 36216 bytes

  Custom meta data
    Source             : "G4MCPLWriter [G4MCPLWriter]"
    Number of comments : 1
          -> comment 0 : "Transmission spectrum from 10GeV proton beam on 20cm lead"
    Number of blobs    : 0

  Particle data format
    User flags         : no
    Polarisation info  : no
    Fixed part. type   : no
    Fixed part. weight : no
    FP precision       : single
    Endianness         : little
    Storage            : 36 bytes/particle

index     pdgcode   ekin[MeV]       x[cm]       y[cm]       z[cm]          ux          uy          uz    time[ms]      weight
    0          22      1.2635     -3.5852    -0.81223          20    -0.41453   -0.022799     0.90975  7.3389e-07           1
    1          22      2.6273     0.85935      10.196          20   0.0031473     0.75937     0.65065  8.6567e-07           1
    2         211      1050.4      2.9741    -0.32269          20     0.24133   0.0099724     0.97039  7.1473e-07           1
    3        2112     0.26395     -2.7828      -4.709          20     -0.7575    0.041025     0.65154  2.7656e-05           1
    4        2112     0.34922     0.42959     -11.636          20     0.22266    -0.82642     0.51716  1.9382e-05           1
    5        2112      1.4445      3.8808      14.263          20   -0.036128     0.47899     0.87708  1.9604e-05           1
    6        2112     0.21436     -20.706    0.071227          20    -0.42916     0.43638     0.79082  1.1434e-05           1
    7        2112     0.27496     -6.9939      7.9537          20    -0.47614     0.36919     0.79812  6.8358e-05           1
    8        2112     0.41955     -3.0206     0.11889          20    -0.62614    0.040539     0.77866  2.7557e-05           1
    9        2112     0.64336     -11.788      12.976          20    -0.77018    -0.35919     0.52707  6.1839e-05           1
```

The `-l` (limit) and `-s` (skip) flags can be used to change which particles are printed (use `-l0` to print _all_ particles), and `-j` can be used to suppress the header information.

### Extract some particles from a file

Using the `--extract` flag, it is possible to extract a subset of particles from a file, into a new file. Using the `-p` flag, one can select according to [particle type](http://pdg.lbl.gov/2014/reviews/rpp2014-rev-monte-carlo-numbering.pdf) (2112=neutron, 22=gamma, etc.).

```shell
mcpltool --extract -p2112 example.mcpl justneutrons.mcpl
```
```
MCPL: Attempting to compress file justneutrons.mcpl with gzip
MCPL: Succesfully compressed file into justneutrons.mcpl.gz
MCPL: Succesfully extracted 726 / 1006 particles from examples/example.mcpl into justneutrons.mcpl.gz
```

Note that the output file is currently always compressed into .mcpl.gz when possible (this behaviour might change in the future).

You can also use the `-l` and `-s` flags to extract particles according to their position in the file, which might for instance be useful to extract a specific interesting particle from a huge file. Here we extract 1 particle starting from position 123:

```shell
mcpltool --extract -l1 -s123  examples/example.mcpl justneutrons.mcpl
```
```
MCPL: Attempting to compress file justneutrons.mcpl with gzip
MCPL: Succesfully compressed file into justneutrons.mcpl.gz
MCPL: Succesfully extracted 1 / 1006 particles from examples/example.mcpl into justneutrons.mcpl.gz
```

### Merging compatible files

Using the `--merge` flag, it is possible to merge contents from a list of compatible files into a single new one. Here four existing files are merged, creating newfile.mcpl as a result:

```shell
mcpltool --merge newfile.mcpl file1.mcpl file2.mcpl file3.mcpl file4.mcpl
```

Note that files are currently compatible if and only if they have similar settings and meta-data.

### Get full usage instructions

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
  mcpltool --extract [extract-options] FILE1 FILE2
  mcpltool --repair FILE
  mcpltool --version
  mcpltool --help

Dump options:
  By default include the info in the FILE header plus the first ten contained
  particles. Modify with the following options:
  -j, --justhead  : Dump just header info and no particle info.
  -n, --nohead    : Dump just particle info and no header info.
  -lN             : Dump up to N particles from the file (default 10). You
                    can specify -l0 to disable this limit.
  -sN             : Skip past the first N particles in the file (default 0).
  -bKEY           : Dump binary blob stored under KEY to standard output.

Merge options:
  -m, --merge FILEOUT FILE1 FILE2 ... FILEN
                    Creates new FILEOUT with combined particle contents from
                    specified list of N existing and compatible files.
  -m, --merge --inplace FILE1 FILE2 ... FILEN
                    Appends the particle contents in FILE2 ... FILEN into
                    FILE1. Note that this action modifies FILE1!

Extract options:
  -e, --extract FILE1 FILE2
                    Extracts particles from FILE1 into a new FILE2.
  -lN, -sN          Select range of particles in FILE1 (as above).
  -pPDGCODE         select particles of type given by PDGCODE.

Other options:
  -r, --repair FILE
                    Attempt to repair FILE which was not properly closed, by up-
                    dating the file header with the correct number of particles.
  -v, --version   : Display version of MCPL installation.
  -h, --help      : Display this usage information (ignores all other options).
```

## Quick and dirty way to get the mcpltool

Rather than downloading and building the full MCPL distribution, it is possible to get hold
of the `mcpltool` command simply by downloading and saving the
single-file ("fat") version of the code found at this link: {% include linkfile.html file="src_fat/mcpltool_app_fat.c" download=true %}.

Next, compile it with the command (exchange "gcc" with the name of your compiler - e.g.
"clang" on OS X):

```shell
gcc -std=c99 -lm mcpltool_app_fat.c -o mcpltool
```

And you are ready to run! For instance you can inspect an MCPL file with:

```shell
./mcpltool  <my-mcpl-file>
```

Or get full usage instructions with:

```shell
./mcpltool --help
```
