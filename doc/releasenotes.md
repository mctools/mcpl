MCPL 2.1.0 release notes (and website)
========================

This release finally brings an often-requested feature to MCPL: Statistics in the header which are automatically combined when files are merged!

For now, this concerns statistics which should be accumulated via simple addition when files are merged. Examples of such statistics could for instance be "number of seed particles in simulation run", "number of seconds of beamtime simulated", or "number of proton collisions modelled".

The new statistics will show up as human-readable comments where the value will usually be a non-negative number (in rare cases you might also see the special value "-1" which means "not available"). Here is how it might look when using the `mcpltool` to inspect such a file:

```
  Custom meta data
    Source             : "my_cool_program_name"
    Number of comments : 2
          -> comment 1 : "stat:sum:my_custom_source_stat:                 1.2345e6"
          -> comment 2 : "Some other comment."
    Number of blobs    : 0
```

Imagine a second (otherwise compatible) file with:

```
  Custom meta data
    Source             : "my_cool_program_name"
    Number of comments : 2
          -> comment 1 : "stat:sum:my_custom_source_stat:                    2.0e6"
          -> comment 2 : "Some other comment."
    Number of blobs    : 0
```

In the past, the two files would not have been possible to merge with the usual tools (`mcpltool` or the API), but now they are not only mergeable, the values are actually summed up as they should. The resulting file thus ends up with all the particles from both files as well as the header:

```
  Custom meta data
    Source             : "my_cool_program_name"
    Number of comments : 2
          -> comment 1 : "stat:sum:my_custom_source_stat:                 3.2345e6"
          -> comment 2 : "Some other comment."
    Number of blobs    : 0
```

If desired, users or developers interacting with MCPL files through the MCPL software can interact with these `stat:sum:<key>:<value>` entries programmatically through the C or Python APIs. For instance, they can be extracted easily into a dictionary in the Python API:

```py
>>> import mcpl
>>> f = mcpl.MCPLFile('somefile.mcpl')
>>> print( f.stat_sum )
{'my_custom_source_stat': 3.2345e6}
```

In addition to file merging, official MCPL software has been updated to deal correctly with files being *split* (as opposed to *filtered*). So for instance, selecting ranges of particles using `mcpltool --extract` with `-l` or -`s` flags would cause the value of statistics to be reduced, whereas selecting particles by type using the `-p` flag would not.

It is expected that most user code dealing with MCPL files will not have to be updated to deal with these new statistics entries, but anyone using custom code to deal with raw MCPL data directly, should check that any code which either splits or merges data is doing the right thing. Fortunately, while the MCPL developers are aware of third party code dealing with MCPL data directly, we are not aware of any such custom implementations dealing with either file-splitting or file-merging, which is the crucial point.

Full details of the new feature and related advice is available on the website (FIXME: LINK).




-------------------------------------------------------


This new feature of statistics interacts in a non-trivial manner with


Note that although this encoding of statistics into comments is merely a convention and not a change of the underlying MCPL format as such, software in the MCPL distribution itself will emit an error if it encounters any comment starting with `stat:` but which is not conforming exactly to the convention. Anyone intending to interact directly with raw MCPL data is thus encouraged to familiarize themselves with the full details of the new convention.

 It is intended that when one day the MCPL format specification is updated to MCPL-4, that this convention will become part fo the  if the It is the hope that any third-party implementation of file splitting or merging which does not use the official MCPL software to interact with the files, will respect any `stat:sum:` entries

:

```C
   void mcpl_hdr_add_stat_sum( mcpl_outfile_t, const char * key, double value );
   double mcpl_hdr_stat_sum( mcpl_file_t, const char * key );



either through manual inspection as above, or via the via the C api:




applicate


reserved but not actually available" and comes out as None in the Python


, so for instance




The feature is NOT associated with an update of the on-disk MCPL format, rather the new statistics are contained in the MCPL comments field, using a dedicated syntax. This means that
