---
title: Using MCPL from Python
navtitle: Python
weight: 5
underconstruction: true
---

- two magic lines for toc
{:toc}


**NOTE: The python interface being documented on this page is only available once MCPL 1.2.0 is released (early July 2017)**

Supports both Python2 and Python3.

```python
import mcpl
with mcpl.MCPLFile("example.mcpl") as f:
    print( Number of particles in file: %i' % f.nparticles )
    for p in f.particles:
        print( p.x, p.y, p.z, p.ekin )

```
