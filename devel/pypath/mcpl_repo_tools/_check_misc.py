
################################################################################
##                                                                            ##
##  This file is part of MCPL (see https://mctools.github.io/mcpl/)           ##
##                                                                            ##
##  Copyright 2015-2025 MCPL developers.                                      ##
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

# Checks whitespace, encodings, line-endings, file-sizes, ...

from ._check_fixme import is_well_known_binary

ignore_list = set([
#    'tests/data/QE_pw_Al.out',
])

ignore_list_nonascii = set([
    'devel/misc/test_encodings.x',

#    'devel/plugin_database.yml',
#    'devel/plugin_database.yml',
])

def main():

    from .srciter import all_files_iter
    from .dirs import reporoot
    #For log files (and indeed all files) we simply test the size:
    max_size_kb_log = 300
    max_size_kb_other = 60
    max_size_overrides = {
        'mcpl_core/src/mcpl.c' : 150,
        'tests/scripts/forcemerge.log' : 500,
        'mcpl_python/src/mcpl/mcpl.py' : 80,
    }
    for f in all_files_iter():
        lim = max_size_kb_log if f.suffix == '.log' else max_size_kb_other
        lim = max_size_overrides.get(
            str(f.relative_to( reporoot )).replace('\\','/'), lim
        )
        size_kb =  len(f.read_bytes()) / 1024.
        if size_kb > lim:
            raise SystemExit(f'File too large ({size_kb:.4g} kb): {f}')

    for f in all_files_iter('!*.log'):
        frel = str(f.relative_to(reporoot)).replace('\\','/')
        if frel in ignore_list:
            continue
        #Check can always be read as utf8:
        content = '\n'
        if not is_well_known_binary(frel):
            try:
                content = f.read_text(encoding='utf8')
            except UnicodeDecodeError as e:
                raise RuntimeError(f"Binary file: {frel}") from e
            if len(content)==0:
                #never check empty files
                continue

        #always trailing newlines:
        if not content.endswith('\n'):
            import platform
            ignore_on_win = 'NCCFileUtils' in f.name
            if ignore_on_win and platform.system() == 'Windows':
                print("WARNING: Windows detected. Ignoring trailing"
                      f" newline error in {f} which might be false positive")
            else:
                raise SystemExit(f'No trailing newline in {f}')

        #Check file has only ascii characters:
        if frel not in ignore_list_nonascii:
            try:
                content.encode('ascii')
            except UnicodeEncodeError:
                raise SystemExit(f'Non-ascii chars found in {f}')

        lines = content.splitlines()
        for e in lines:
            if '\t' in e:
                raise SystemExit(f'TABs found in {f}')
            if ( e.endswith(' ')
                 and not frel.startswith('tests/data/refnc1/')
                 and not frel.startswith('tests/data/refnc2d5/') ):
                raise SystemExit(f'Trailing spaces at end-of-line found in {f}')
        #count trailing whitespace:
        nws = 0
        nlines = len(lines)
        for i in range(nlines):
            if not lines[nlines-i-1].strip():
                nws += 1
            else:
                break
        if nws > 1:
            raise SystemExit(f'Too many trailing empty lines in {f}')

    print('all ok')
