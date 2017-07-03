---
title: Using MCPL from Python
navtitle: Python
weight: 5
underconstruction: true
---

- two magic lines for toc
{:toc}

If desired, it is possible to access the content of MCPL files from Python code
by using the `mcpl` Python module described on this page, available since MCPL
release 1.2.0. Notice that most end-users should not normally have to write code in
order to use MCPL. Rather, they should be able to use pre-existing converters or
plugins for their Monte Carlo applications (c.f. [hooks](LOCAL:hooks/)).

**NOTE: The python interface being documented on this page is only available once MCPL 1.2.0 is released (early July 2017)**

## Using the MCPL Python module

### Opening MCPL files and accessing particle contents

The simplest usage, opening an MCPL file and accessing the particle contents in
order, is straightforward:

```python
import mcpl
myfile = mcpl.MCPLFile("myfile.mcpl")
for p in myfile.particles:
   print( p.x, p.y, p.z, p.ekin )
```

Here we access and print out the particle positions (units of cm) and kinetic
energies (units of MeV). The field names and units are the same as in the
[C/C++](LOCAL:usage_c/) interface, and are documented directly via the
integrated help system of Python.  Thus, one can get a full list of all
available data fields by adding a line `help(mcpl.MCPLFile)` statement anywhere.

### Access blocks of particles for efficiency

For large files, it can be much more efficient to load a large number of
particles as once, using instead the `particle_blocks` interface:

```python
import mcpl
myfile = mcpl.MCPLFile("myfile.mcpl")
for p in myfile.particle_blocks:
   print( p.x, p.y, p.z, p.ekin )
```

The code looks similar to the non-block case above, but each field like `p.x` or
`p.ekin` are now actually [NumPy](http://www.numpy.org/) arrays rather than
single numbers. By default each block encompasses 10000 particles, but this
number can be tuned adding the `blocklength` when instantiating a new `MCPLFile`
object.

### Access file-level meta-data

In addition to particle contents, it is of course also possible to access
file-level meta-data, as can be seen in this example:

```python
import mcpl
myfile = mcpl.MCPLFile("myfile.mcpl")
print( 'Number of particles in file: %i' % myfile.nparticles )
print( 'File created by: "%s"' % myfile.sourcename )
if myfile.opt_polarisation:
    print( 'File contains polarisation information' )
for c in myfile.comments:
    print( 'File has comment: "%s"' % c )
```

For a full list of all available meta-data fields, one can access the integrated
documentation by adding a line with `help(mcpl.MCPLFile)`.

## Where to find more documentation

Python support for MCPL was added after the release of the {% include
linkpaper.html %}, so currently the most comprehensive documentation for the API
provided by the `mcpl` Python module is to be found using Python's integrated
`help()` functionality, for instance by running one of the following commands in
a terminal:

```shell
python -c 'import mcpl;help(mcpl.MCPLFile)'     # get documentation of MCPLFile class
python -c 'import mcpl;help(mcpl.MCPLParticle)' # get documentation of MCPLParticle class
python -c 'import mcpl;help(mcpl)'              # get all documentation
```

## How to install the MCPL python module

The `mcpl.py` is a pure Python module which only requires Python (both Python 2
and 3 are supported) and the ubiquitous [NumPy](http://www.numpy.org/) module to
be available on the system.

### Just download a single file and use it...

As the entire MCPL Python module is implemented in a single pure-python file,
one can simply download the {% include linkfile.html file="src/python/mcpl.py"
download=true %} file and place it anywhere in the PYTHONPATH, such as the
directory from which you plan to run your Python scripts.

### ... or use it as part of the MCPL distribution
The `mcpl` Python module is part of the MCPL distribution starting with release
1.2.0, and can after installation be used by adding the python subdirectory of
the installation to your Python path. For example, if you installed the MCPL
distribution in `/path/to/mcplinstall`, the following line will make the Python
module available from your Python code (put it somewhere like your `.bashrc` to
make the setting permanent):

```shell
export PYTHONPATH=/path/to/mcplinstall/python:$PYTHONPATH
```
