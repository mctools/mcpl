---
title: Get MCPL
weight: 9999
underconstruction: true
---

The easiest way to install MCPL is via the prebuilt Python or Conda packages. The package named `mcpl` provides both [command-line tools](LOCAL:usage_cmdline), and API's for [C/C++](LOCAL:usage_c), [Python](LOCAL:usage_python), and CMake configuration.

Additionally, the package named `mcpl-extra` provides (as the name indicates) extra optional utilities such as optional converters between MCPL and other file formats.

## Install via Python tools

Complete MCPL packages are provided as wheels on PyPI, and installation is as simple as:

```
pip install mcpl mcpl-extra
```

As noted above, the `mcpl-extra` package is optional.

## Install via Conda

If using conda, you can simply install MCPL from the [conda-forge](https://conda-forge.org/) channel.  Thus:

```
conda install -c conda-forge mcpl mcpl-extra
```

As noted above, the `mcpl-extra` package is optional.

For consistency, it is recommended that your conda environment ONLY uses packages from the conda-forge channel.

## Custom builds (expert only)

Experts might wish to build MCPL packages manually. Please refer to the instructions [here](https://github.com/mctools/mcpl/blob/path_to_mcpl2/INSTALL.md) for more details.
