The "stat:sum" convention for statistics in MCPL headers
========================================================

This document describes a convention allowing the addition of custom statistics
to the headers of MCPL files, encoded into textual comments starting with the
string `stat:`.

Motivation and background
-------------------------

The MCPL-2 and MCPL-3 formats allows for custom text comments in file
headers. However, when merging files such comments have previously been required
to be identical in the files being merged, or the merge would fail. For many
(most?)  such comments, this makes perfect sense. However, for the particular
use-case of wanting to record various parameters related to simulation "size",
this is not ideal. Examples of simulation size could be something like "number
of initial particles used for the simulation", or even scaled quantities like
"number of seconds of beamtime simulated at nominal conditions". In this case,
one would ideally like the quantities to be combined via simple addition when
two files are merged (or somehow divided among files, if files are split or
truncated).

Example of encoding of new statistics parameters
------------------------------------------------

Imagine two MCPL files, `a.mcpl` and `b.mcpl`, both produced as outcome of two
separate simulation jobs, perhaps by capturing particles at a certain surface in
a particular neutron scattering beamline. The only difference between the files
might be the initial random number seed, and possibly the number of initial
neutrons entering the start of the instrument in the given simulation
job. Imagine that the header data of the two files is identical and thus
compatible for a merge operation, except for the comments which use the new
syntax to encode the number of initial neutrons used in each job (the files will
obviously also differ in the actual particles stored in the files). In `a.mcpl`
the comment in question might read:

`"stat:sum:sim_source_count:                 1000000"`

while in `b.mcpl` the corresponding comment might be:

`"stat:sum:sim_source_count:                 2000000"`

After merging the two files into a single file, `c.mcpl`, that file will have
the corresponding comment field as:

`"stat:sum:sim_source_count:                 3000000"`

We shall explain the general syntax allowed for such comments below.

The syntax
----------

The syntax of the comments defining a statistics with both a key and a value is:
`"stat:sum:<key>:<value>"` with the following additional constraints:

* The entire string must be encoded with printable ASCII values only.

* The user definable `<key>` must be from 1 to 64 characters long, begin with an
  ASCII letter (a-z or A-Z), and contain only ASCII letters, numbers (0-9) or
  underscores (_).

* The `<value>` must always be exactly 24 characters long, and contain an ascii
  representation of the value including only characters from the list
  `0123456789.+-eE`.  If less than 24 characters are needed for the value
  itself, the string can be padded with extra ASCII spaces (' ') at either end
  (and only at the ends).  If manually composing the strings in languages like
  C, C++, or Python, one can for instance encode the value using a print-format
  specifier like "%24.17g", which has the advantage of loss-less encoding of
  double-precision floating point values (assuming 64 bit IEEE-754 floating
  point encoding).

* The actual value represented in the `<value>` must not be negative, NaN
  (not-a-number) or infinity. The exception is that a value of -1 is allowed,
  with the special meaning of "not available". This can for instance be used to
  reserve space in a file with the intention of overwriting it with an actual
  value later. In case of an exceptional programme abort, where the file header
  had been written but the job ended before all particles could be written to
  the file, the header would in that case hold a value meaning "not available",
  rather than a misleading value. Any operations on statistics during file
  merges or splitting should yield -1 if any input value is -1 or if the result
  does not otherwise fit (i.e. if merges would lead to values of infinity)

* In addition to `stat:sum:...` entries, all entries starting with the string
  `stat:` are reserved for future usage. Thus, it is for now recommended that
  software dealing with MCPL files will prevent people from creating comments
  starting with `stat:`, except if it is a `stat:sum:<key>:value` entry
  compliant with the syntax defind above.

Software support
----------------

The MCPL software release from https://github.com/mctools/mcpl supports the
"stat:sum" convention starting with release 2.1.0. Earlier MCPL software
releases will simply treat the special comments as any regular comments, which
is likely OK as long as one is not merging or editing files, apart from imposing
global filtering constraints on all particles in a file (see the section on
filtering below). For consistency, it is therefore recommended that applications
modify their software dependency list to require at least version 2.1.0 of the
MCPL software release.

Applications or libraries interacting directly with MCPL files through their own
code, rather than via the MCPL software release, are recommended to double-check
the "guidelines for developers" section below to see if their software needs to
be updated to support the "stat:sum" convention. In general

Users of the C or Python API of the MCPL software release do not have to fiddle
with encoding or decoding `stat:sym:<key>:<value>` comments. Instead the `C` api
provides functions, `mcpl_hdr_add_stat_sum()` and `mcpl_hdr_stat_sum(..)`
for respectively adding or extracting the values from files. Likewise,
`MCPLFile` objects in the Python API now have `.stat_sum` properties, which are
dictionaries of `(key,value)` pairs.

The C API
---------

Guidelines for applications merging or otherwise editing files
--------------------------------------------------------------







Formal support
--------------

There is so far no change in the MCPL format associated with this new
`stat:sum:...` syntax, however it is intended that it will eventually be
adopted into a future MCPL format, and thus require all complient MCPL software
to support it.
