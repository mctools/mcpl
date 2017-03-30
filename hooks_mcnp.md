---
title: MCPL converters for MCNP
underconstruction: true
weight: 20
---

- two magic lines for toc
{:toc}

The MCNP–MCPL interface currently supports MCNPX, MCNP5 and MCNP6 and exploits the existing MCNP capability to stop and subsequently restart simulations at a user-defined set of surfaces through the Surface Source
Write/Read (SSW/SSR) functionality into files. We refer to such files as "SSW files", although different names are occasionally used (e.g. "RSSA files"). The MCNP-MCPL interface is thus implemented as two standalone commandline converters: `ssw2mcpl` and `mcpl2ssw`. A detailed description of the commands, as well as references to the relevant MCNP manuals in which it is described how to enable the SSW functionality in a given MCNP _input deck_, is given in {% include linkpaper.html subsection=3.2 %} and the present page will merely provide a few typical usage examples.

At the bottom of the page is also included a quick and dirty recipe for how the `ssw2mcpl` and `mcpl2ssw` commands can be obtained without first downloading and installing the MCPL distribution. Note that users of the ESS dgcode framework already have access to the commands, and it is planned to provide McStas and McXtrace users with them as well
(cf. [this issue]({{ "/20" | prepend: site.github.issues_url }})).

## Examples

todo

### Converting an SSW file to MCPL

Simply providing the `ssw2mcpl` command with the name of an existing SSW file and the desired name of the MCPL file to be created, is enough to trigger the conversion:

```shell
ssw2mcpl sswfile.w newfile.mcpl
```
```
ssw_open_file: Opened file "sswfile.w":
ssw_open_file:    File layout detected : MCNPX
ssw_open_file:    Code ID fields : "mcnpx" / "2.7.0"
ssw_open_file:    Title field : "Example to write mcpl from mcnp5,mcnp6 and mcnpx"
ssw_open_file:    Source statistics (histories):        1000
ssw_open_file:    Particles in file            :        2000
ssw_open_file:    Number of surfaces           :           2
ssw_open_file:    Histories at surfaces        :        1000
MCPL: Attempting to compress file newfile.mcpl with gzip
MCPL: Succesfully compressed file into newfile.mcpl.gz
Created newfile.mcpl.gz
```
However, it is possible to add more than the minimal amount of information into the output file. First of all, the `-d` flag can be used to enable double-precision rather than single-precision storage of floating point numbers. Next, the `-s` flag will cause the MCNP surface ID's to be embedded in the MCPL userflags fields, and finally specifying `-c <path_to_input_deck>` will cause the MCNP input deck used to generate the SSW file in question to be embedded into the MCPL header (can later be retrieved with `mcpltool -bmcnp_input_deck newfile.mcpl`). In particular, it is highly recommended to embed the input_deck with `-c` for later reference, and the `-s` might be essential if the file is intended to be converted back for usage in an MCNP with compatible surface ID's. Thus, enabling as much information as possible in the MCPL file would happen with:

```shell
ssw2mcpl -d -s -c input_deck sswfile.w newfile.mcpl
```
Inspecting the resulting newfile.mcpl with `mcpltool` might give an output like this (admittedly the SSW file was not from a very interesting simulation):

```shell
mcpltool newfile.mcpl
```
```
Opened MCPL file newfile.mcpl.gz:

  Basic info
    Format             : MCPL-3
    No. of particles   : 2000
    Header storage     : 1077 bytes
    Data storage       : 144000 bytes

  Custom meta data
    Source             : "MCNPX"
    Number of comments : 3
          -> comment 0 : "SSW file from MCNPX converted with ssw2mcpl (from MCPL release v1.1.0)"
          -> comment 1 : "SSW metadata: [kods='mcnpx', vers='2.7.0', title='Example to write mcpl from mcnp5,mcnp6 and mcnpx']"
          -> comment 2 : "The userflags in this file are the surface IDs found in the SSW file"
    Number of blobs    : 1
          -> 747 bytes of data with key "mcnp_input_deck"

  Particle data format
    User flags         : yes
    Polarisation info  : no
    Fixed part. type   : no
    Fixed part. weight : no
    FP precision       : double
    Endianness         : little
    Storage            : 72 bytes/particle

index     pdgcode   ekin[MeV]       x[cm]       y[cm]       z[cm]          ux          uy          uz    time[ms]      weight  userflags
    0        2112         250        1050           0           0           1           0           0  5.7379e-05           1 0x00000004
    1        2112         250        1500           0           0           1           0           0  8.1853e-05           1 0x00000005
    2        2112         250        1050           0           0           1           0           0  5.7379e-05           1 0x00000004
    3        2112         250        1500           0           0           1           0           0  8.1853e-05           1 0x00000005
    4        2112         250        1050           0           0           1           0           0  5.7379e-05           1 0x00000004
    5        2112         250        1500           0           0           1           0           0  8.1853e-05           1 0x00000005
    6        2112         250        1050           0           0           1           0           0  5.7379e-05           1 0x00000004
    7        2112         250        1500           0           0           1           0           0  8.1853e-05           1 0x00000005
    8        2112         250        1050           0           0           1           0           0  5.7379e-05           1 0x00000004
    9        2112         250        1500           0           0           1           0           0  8.1853e-05           1 0x00000005
```

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
