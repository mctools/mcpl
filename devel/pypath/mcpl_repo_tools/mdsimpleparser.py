
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

def parse_markdown( f ):
    if hasattr(f,'__fspath__') or '\n' not in f:
        import pathlib
        f = pathlib.Path(f)
        assert f.is_file()
        t = f.read_text()
        return parse_markdown( t )

    import re

    lines = f.splitlines()
    nlines = len(lines)
    def is_header_underline( t ):
        t = (t or '').strip()
        return bool(re.match('\\A----+',t) or re.match('\\A====+',t))

    def is_header( iline ):
        assert iline < nlines
        line = lines[iline]
        nextline = lines[iline+1] if iline+1<nlines else None
        if not is_header_underline(nextline):
            return False
        if len(line)!=len(nextline):
            raise RuntimeError("Wrong length of markdown header underline "
                               f"in line {iline+2}")
        return True

    def provide():
        iline = 0
        while iline < nlines:
            linedata = lines[iline].rstrip()
            if is_header(iline):
                yield lines[iline+1].strip()[0], linedata
                iline += 2
            else:
                yield None, linedata
                iline += 1

    if not nlines or not is_header(0):
        raise RuntimeError('Markdown does not begin with header')

    current_section = None
    sections = []
    for hdr_type, line in provide():
        if hdr_type is None:
            assert current_section is not None
            current_section[1].append(line)
        else:
            if current_section is not None:
                sections.append(current_section)
            current_section = [ [line,hdr_type], [] ]
    if current_section is not None:
        sections.append(current_section)
    return sections
