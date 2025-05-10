---
title: The MCPL format
underconstruction: true
weight: 10
---

While there are often new releases of the MCPL software distribution, the actual binary MCPL *format* itself very rarely receives updates. Furthermore, since the format version is incoded at the beginning of all MCPL files, it is always possible for the latest MCPL software to read files in older formats (except `MCPL-1` which was a test format never released to the wider public). This is obviously an important design feature, intended to ensure that older MCPL files can always be read with the latest MCPL software releases.

# List of MCPL formats

* **MCPL-1**: An early prototype format. This format was never used beyond internal developments and is undocumented and unsupported.
* **MCPL-2**: The first publically released format, used briefly around 2015-2016.
* **MCPL-3**: The default format produced since the MCPL software release 1.0.0 in 2016.

## Full format specifications

The actual binary file formats `MCPL-2` and `MCPL-3` are described in great detail in {% include linkpaper.html linkname="section 2" section=2 %}. The two formats are in fact almost identical, with the only difference being which packing algorithm is used to pack particle direction vectors. `MCPL-3` uses the superior Adaptive Project Packing algorithm, while `MCPL-2` use Octahedral packing.


# Conventions

In addition the the actual format itself, release 2.1.0 of the MCPL software distribution introduced the notion of a convention for encoding statistics in MCPL comment fields, and aggregating these statistics appropriately when MCPL files. Refer to the dedicated [page describing the stat:sum convention](LOCAL:format_statsum/) for more details. Additionally, note than any comment starting with the 5 characters `stat:` is now considered to be reserved for future usage.
