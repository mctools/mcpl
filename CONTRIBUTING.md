# Contributing to MCPL

Contributions to MCPL are very welcome, whether they are questions, bug
reports, documentation fixes, support for more simulation codes, or code.
Everyone taking part is expected to follow our [code of
conduct](CODE_OF_CONDUCT.md).

## Questions, bugs, and ideas

Please ask questions in the [Q&A
section](https://github.com/mctools/mcpl/discussions/categories/q-a) of the
Discussions forum, and report bugs and feature requests in the [issue
tracker](https://github.com/mctools/mcpl/issues). Before starting on a larger
change, please open an issue or a discussion first, so we can agree on the
approach.

## Pull requests

- Base pull requests on the `develop` branch (not `main`, which only receives
  releases).
- Keep each pull request to one topic, and add tests where it makes sense.

All contributions are included under the same [Apache 2.0 license](LICENSE) as
the rest of MCPL.

## Developer tools

The developer tools are in `devel/`. In bash or zsh, `. devel/setup.sh` puts the
`mcpldevtool` command on your `PATH`. Before committing, please run:

- `mcpldevtool check`: static checks of the code and the repository,
- `mcpldevtool cmake`: build and run all tests with CMake.

`mcpldevtool --help` lists the other modes.

## AI-assisted contributions

Contributions made with the help of AI tools are welcome, but commits and pull
requests must be authored by people, not by agent or bot accounts. The author is
responsible for the contribution, and must understand and have tested it.
Please do not use `Co-Authored-By` lines or "Generated with" lines in commits
with AI tools, use `Assisted-by` instead, for example:

```
Assisted-by: claude-code:claude-opus-5.5
```
