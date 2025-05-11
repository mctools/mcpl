---
title: The stat:sum convention
underconstruction: true
weight: 50
---

- two magic lines for toc
{:toc}

**WARNING: This page concerns documentation for a future release of MCPL and is still being edited**

The `stat:sum` convention for statistics in MCPL headers, allows the addition of custom statistics to the headers of MCPL files, with the values being combined through simple addition when files are merged. These values are encoded into textual comments of the form `stat:sum:<key>:<value>`, and the present page provides both a brief introduction to the subject, as well as more detailed description of the allowed syntax and guidelines for how to deal with them in various scenarios where MCPL files are filtered, merged, split, or otherwise edited.

# Introduction

In short, the `stat:sum` convention brings an often-requested feature to MCPL: Statistics in the header which are automatically combined when files are merged!

More specifically, `stat:sum` values are to be combined via simple addition when files are merged. Examples of such statistics could for instance be *"number of seed particles in simulation run"*, *"number of seconds of beam-time simulated"*, or *"number of proton collisions modelled"*.

When inspecting MCPL files, the new statistics will show up as human-readable comments where the encoded value will usually be a non-negative finite floating point number (in some cases you might also see the special value *-1* which means *Not Available*). Here is how it might look when using the `mcpltool` to inspect such a file:

```
  Custom meta data
    Source             : "my_cool_program_name"
    Number of comments : 2
          -> comment 1 : "stat:sum:my_custom_source_stat:                 1.2345e6"
          -> comment 2 : "Some other comment."
    Number of blobs    : 0
```

Note that depending on your font, you might have to scroll to the right to see the actual value, as for technical reasons values are always padded with spaces to take up exactly 24 characters. Now imagine a second (otherwise compatible) file with:

```
  Custom meta data
    Source             : "my_cool_program_name"
    Number of comments : 2
          -> comment 1 : "stat:sum:my_custom_source_stat:                    2.0e6"
          -> comment 2 : "Some other comment."
    Number of blobs    : 0
```

Before the MCPL software release version 2.1.0, the two files would not have been possible to merge with the usual tools (`mcpltool --merge` or the MCPL C API), but now they are not only mergeable, the values are properly combined via addition to produce the new post-merge value. The resulting file thus ends up with all the particles from both files and the header:

```
  Custom meta data
    Source             : "my_cool_program_name"
    Number of comments : 2
          -> comment 1 : "stat:sum:my_custom_source_stat:                 3.2345e6"
          -> comment 2 : "Some other comment."
    Number of blobs    : 0
```

If desired, users or developers interacting with MCPL files through the MCPL software can interact with these `stat:sum:<key>:<value>` entries programmatically through the C or Python APIs. For instance, they can be extracted easily into a dictionary in the Python API (here values of `-1` will be translated to `None`):

```py
>>> import mcpl
>>> f = mcpl.MCPLFile('somefile.mcpl')
>>> print( f.stat_sum )
{'my_custom_source_stat': 3.2345e6}
```

In addition to file merging, official MCPL software has been updated to deal conservately with files being *split* (as opposed to *filtered*). So for instance, selecting ranges of particles using `mcpltool --extract` with `-l` or -`s` flags will cause the value of statistics to be converted to -1 (meaning *Not Available*), since the generic MCPL code can not possibly know with certainty how to calculate the new values. On the other hand, extracting particles by type using the `-p` flag will instead cause the output to retain the original `stat:sum` value.

It is expected that most user code dealing with MCPL files will not have to be updated to deal with these new statistics entries, but anyone using custom code to deal with raw MCPL data directly should check that any code which either splits or merges data is doing the right thing. Refer to the Guidelines for custom code at the end of this page for more information. In fact, anyone intending to create or edit MCPL data with or without using the APIs in the MCPL software distributions, are highly encouraged to familiarise themselves with the full details of the convention described in this page, especially if such data might contain `stat:sum` values.

# Detailed information

The full details of the `stat:sum` convention will be described in this section.

## Motivation and background

The MCPL-2 and MCPL-3 formats allows for custom text comments in file headers. However, when merging files such comments have previously been required to be identical in the files being merged, or the merge would fail. For many (most?)  such comments, this makes perfect sense. However, for the particular use-case of wanting to record various parameters related to simulation "size", this is not ideal. Examples of simulation size could be something like "number of initial particles used for the simulation", or even scaled quantities like "number of seconds of beam-time simulated at nominal conditions". In this case, one would ideally like the quantities to be combined via simple addition when two files are merged (or somehow divided among files, if files are split or truncated).

## Example of encoding of new statistics parameters

Imagine two MCPL files, `a.mcpl` and `b.mcpl`, both produced as outcome of two separate simulation jobs, perhaps by capturing particles at a certain surface in a particular neutron scattering beam-line. The only difference between the files might be the initial random number seed, and possibly the number of initial neutrons entering the start of the instrument in the given simulation job. Imagine that the header data of the two files is identical and thus compatible for a merge operation, except for the comments which use the new syntax to encode the number of initial neutrons used in each job (the files will obviously also differ in the actual particles stored in the files). In `a.mcpl` the comment in question might read:

`"stat:sum:sim_source_count:                 1000000"`

while in `b.mcpl` the corresponding comment might be:

`"stat:sum:sim_source_count:                 2000000"`

After merging the two files into a single file, `c.mcpl`, that file will have the corresponding comment field as:

`"stat:sum:sim_source_count:                 3000000"`

We shall explain the general syntax allowed for such comments below.

## The syntax

The syntax of the comments defining a statistics with both a key and a value is: `"stat:sum:<key>:<value>"` with the following additional constraints:

* The entire string must be encoded with printable ASCII values only.

* The user definable `<key>` must be from 1 to 64 characters long, begin with an ASCII letter (a-z or A-Z), and contain only ASCII letters, numbers (0-9) or underscores (_).

* The `<value>` must always be exactly 24 characters long, and contain an ASCII representation of the value including only characters from the list `0123456789.+-eE`.  If less than 24 characters are needed for the value itself, the string can be padded with extra ASCII spaces (' ') at either end (and only at the ends).  If manually composing the strings in languages like C, C++, or Python, one can for instance encode the value using a print-format specifier like "%24.17g", which has the advantage of loss-less encoding of double-precision floating point values (assuming 64 bit IEEE-754 floating point encoding).

* The actual value represented in the `<value>` must not be negative, NaN (not-a-number) or infinity. The exception is that a value of -1 is allowed, with the special meaning of "not available". This can for instance be used to reserve space in a file with the intention of overwriting it with an actual value later. In case of an exceptional programme abort, where the file header had been written but the job ended before all particles could be written to the file, the header would in that case hold a value meaning "not available", rather than a misleading value. Any operations on statistics during file merges or splitting should yield -1 if any input value is -1 or if the result does not otherwise fit (i.e. if merges would lead to values of infinity)

* In addition to `stat:sum:...` entries, all entries starting with the string `stat:` are reserved for future usage. Thus, it is for now recommended that software dealing with MCPL files will prevent people from creating comments starting with `stat:`, except if it is a `stat:sum:<key>:value` entry compliant with the syntax defined above.

## Software support

The MCPL software release from https://github.com/mctools/mcpl supports the "stat:sum" convention starting with release 2.1.0. Earlier MCPL software releases will simply treat the special comments as any regular comments, which is likely OK as long as one is not merging or editing files, apart from imposing global filtering constraints on all particles in a file (see the section on filtering below). For consistency, it is therefore recommended that applications modify their software dependency list to require at least version 2.1.0 of the MCPL software release.

Applications or libraries interacting directly with MCPL files through their own code, rather than via the MCPL software release, are recommended to double-check the "guidelines for developers" section below to see if their software needs to be updated to support the "stat:sum" convention. In general

Users of the C or Python API of the MCPL software release do not have to fiddle with encoding or decoding `stat:sym:<key>:<value>` comments, since the APIs provide new convenience interfaces for interacting with them.

### Python API

The `MCPLFile` objects in the Python API now have `.stat_sum` properties, which are dictionaries of `(key,value)` pairs. Note that values of -1.0 in the actual `stat:sum:<key>:<value>` comments in the data are translated into `None` in the Python interface.

### C API

The C API gains three new functions:

```C
double mcpl_hdr_stat_sum( mcpl_file_t, const char * key );
void mcpl_hdr_add_stat_sum( mcpl_outfile_t,
                            const char * key, double value );
void mcpl_hdr_scale_stat_sums( mcpl_outfile_t, double scale );
```

The `mcpl_hdr_stat_sum` function is used to extract `stat:sum:` values from an existing file, by a particular key (returning -2 in case the key is not present in the file)

The `mcpl_hdr_add_stat_sum` function is used to add values into files. Of course, this could also be done with the `mcpl_hdr_add_comment` function, but this is not recommended. In particular the `mcpl_hdr_add_stat_sum` function can also be called *after* the first particle has been written to disk, as long as it was also called *before* the first particle was written, to reserve the space (for this initial reservation one can ideally use a value of -1).

If the value of the statistics is not known initially, it is possible to set value=-1 to simply reserve space in the header. In that case, one MUST invoke the function again to set the final value before the file is closed.  Keys must be at most 64 chars long and not contain colons (:).  In case custom code is used to truncate particle lists, this function should also be used to modify the statistics of such files.

Finally, the function `mcpl_hdr_scale_stat_sums` is intended by usage for people who might be implementing custom editing, filtering or splitting of files via the C API (normally in conjunction with the `mcpl_transfer_metadata` function). If simply filtering based upon particle properties (i.e. picking only certain particle types or energies), this is typically not needed. But if somehow splitting a file or otherwise selecting particles based on their position in the file (e.g. if producing a file containing the first N particles of another file), the stat:sum values in the new file should probably be reduced somehow, and this can be done with the `mcpl_hdr_scale_stat_sums` function. If in doubt, invoking `mcpl_hdr_scale_stat_sums` with a value of -1 ensures that the output file will at least not contain any misleading numbers.

### Command-line API

As the new stat:sum values are encoded in MCPL comments, it is trivially true that `mcpltool`, `pymcpltool`, or any other custom tool showing such comments will already show the stat:sum values.

Additionally, the `mcpltool --extract` mode has been updated to properly deal with stat:sum's. Specifically, it will leave them unaltered if only using the `-p` flag to extract particles of a particular type. However, if using the `-l` and `-s` flags to extract particles based on position in the file, the `mcpltool` code will set all stat:sum values in the resulting file to -1, since

## Guidelines for custom code

Depending on the scenario, code dealing with MCPL file may or may not have to be updated in order to properly deal with the new `stat:sum:...` entries:

* Custom code *filtering* files based only on individual particle properties will most likely not require any changes.

* Custom code *splitting* files, or extracting particles based on position in files, or manually editing particle weights, will most likely require an application-specific calculation of the scaling factor required to preserve the correct meaning of stat:sum entries. The `mcpl_hdr_scale_stat_sums` function can be used to apply such a scale. If nothing else, such code should at least invoke `mcpl_hdr_scale_stat_sums` with a scale of -1, to effectively mark all the stat:sum numbers in the file as unavailable.

* Custom code *merging* files will have to carefully add up any stat:sum values with the same keys. If a key has a value of -1 (or is absent) in either of the input files, it should get a value of -1 in the new file. It should also get a value of -1 in the hypothetical scenario where addition of the values from the two files would end up with a value overflowing the range of 64 bit floating point numbers (i.e. store -1 instead of infinity).
