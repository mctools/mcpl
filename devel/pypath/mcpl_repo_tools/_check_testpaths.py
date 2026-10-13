
################################################################################
##                                                                            ##
##  This file is part of MCPL (see https://mctools.github.io/mcpl/)           ##
##                                                                            ##
##  Copyright 2015-2026 MCPL developers.                                      ##
##                                                                            ##
##  Licensed under the Apache License, Version 2.0 (the "License");           ##
##  you may not use this file except in compliance with the License.          ##
##  You may obtain a copy of the License at                                   ##
##                                                                            ##
##      http://www.apache.org/licenses/LICENSE-2.0                            ##
##                                                                            ##
##  Unless required by applicable law or agreed to in writing, software       ##
##  distributed under the License is distributed on an "AS IS" BASIS,         ##
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  ##
##  See the License for the specific language governing permissions and       ##
##  limitations under the License.                                            ##
##                                                                            ##
################################################################################

# Check that the tests only use files under the tests directory (so they can
# also run from elsewhere, e.g. from a separate package with the tests). This
# forbids constructs like test_data_dir.parent.parent or paths with "..", which
# reach outside tests/. Files used by tests which also live elsewhere in the
# repository (e.g. the examples) are copied into tests/ and kept in sync by the
# copies check.

import re

#Patterns which reach outside the directory of the test data or scripts
#(".." and os.pardir are only a problem when combined with the locations of
#the test data or the scripts themselves, not for paths in the working
#directory of a test):
_srcloc = re.compile(r'test_data_dir|__file__|_pymoddir')
_forbidden = [
    ( re.compile(r'\.parent\s*\.\s*parent'), None, '.parent.parent' ),
    ( re.compile(r'''['"]\.\.['"/\\]'''), _srcloc, 'path component ".."' ),
    ( re.compile(r'os\.pardir'), _srcloc, 'os.pardir' ),
]

#Known and allowed exceptions: the lookups of the data directories themselves.
_allowed = {
    'tests/pypath/MCPLTestUtils/dirs.py',
    'tests/extra/pypath/MCPLExtraTestUtils/dirs.py',
}

def main():
    from .dirs import reporoot
    testdir = reporoot.joinpath('tests')
    print('  Checking that tests do not use files outside tests/:')
    nbad = 0
    nfiles = 0
    for f in sorted(testdir.rglob('*.py')):
        rel = f.relative_to(reporoot).as_posix()
        if rel in _allowed:
            continue
        nfiles += 1
        for i, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            if line.lstrip().startswith('#'):
                continue
            for pattern, also_needed, what in _forbidden:
                if pattern.search(line) and ( also_needed is None
                                              or also_needed.search(line) ):
                    print(f'ERROR: {rel}:{i} uses {what} (tests must only use'
                          ' files under tests/):')
                    print(f'    {line.strip()}')
                    nbad += 1
    print(f'    {nfiles} files checked')
    if nbad:
        raise SystemExit(f'ERROR: {nbad} problem(s) found by the test paths check')

if __name__=='__main__':
    main()
