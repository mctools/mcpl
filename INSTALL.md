Standard installation
=====================

The recommended manner in which to install MCPL is via prebuilt Conda or Python
packages which are available for most modern platforms (including Linux, macOS,
and Windows for both Intel, AMD and ARM platforms):

If using conda, the `mcpl` package can be installed from the conda-forge
channel, by running the command (the `mcpl-extra` package can be installed in a
similar manner):

```
conda install conda-forge::mcpl
```

![Conda Version](https://img.shields.io/conda/v/conda-forge/mcpl)
![Conda Platform](https://img.shields.io/conda/pn/conda-forge/mcpl-core)
![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/mcpl)

For consistency, it is recommended that your conda environment ONLY uses
packages from the conda-forge channel.

If not using conda, MCPL packages can be installed via a Python installation
tool like `pip`, via the command (again, the `mcpl-extra` package can be
installed in a similar manner):

```
pip install mcpl
```

![PyPI - Version](https://img.shields.io/pypi/v/mcpl)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mcpl)



Building from source (experts)
==============================

Advanced users might wish to build MCPL code from the sources in the upstream
repository (https://github.com/mctools/mcpl). This is considered an
expert-only procedure, but it *is* based on standard tools such as CMake and
`pyproject.toml` so should hopefully be somewhat straight forward. A brief
high-level description will be given in the following, but feel free to reach
out and ask questions on https://github.com/mctools/mcpl/discussions in case
something is not clear, or if you run into issues.

Note that to avoid potential conflicts, it is highly recommended that you
uninstall any existing MCPL packages from your environment before performing
manual installations! If you are in a conda environment, you should ensure that
only the conda-forge channel is enabled, and that the following packages are
also installed into the conda environment: `c-compiler`, `cmake`, and `make`
(unix only), `zlib`, `numpy`, `pip`, and `python`.

Note that the CTests defined in `tests/` are only meant to be invoked by running
CMake on the root of the source repository, while actual packages with code is
meant to be build by running CMake on the `mcpl_xxx/` directory in
question. There is for various reasons (mostly lack of manpower) no support for
running CTests directly on a `mcpl_xxx/` subdirectory.
