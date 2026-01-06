
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

def resolve( frel ):
    from .dirs import reporoot
    return reporoot.joinpath(frel)

def load( frel, ignore_section = None, validate_hdrtypes = True ):
    from .mdsimpleparser import parse_markdown
    f = resolve(frel)
    if not f.is_file():
        raise SystemExit(f"File not found: {frel}")
    try:
        m = parse_markdown(f)
    except RuntimeError as e:
        raise SystemExit(f'Problem in {frel} : {e}') from e
    if validate_hdrtypes:
        for i, s in enumerate(m):
            hdr_type = s[0][1]
            tgt_type = '=' if i==0 else '-'
            if hdr_type != tgt_type:
                raise SystemExit(f'Unexpected header underline type in {frel}. '
                                 f' Section number {i+1}, '
                                 f'expected type "{tgt_type*20}", '
                                 f'got "{hdr_type*20}".')
    for i, s in enumerate(m):
        if i+1 == len(m):
            if not s[1][-1]:
                raise SystemExit(f'Error in {frel}: Final section'
                                 ' ends with blank lines')
        else:
            if s[1][-3:] != ['','','']:
                raise SystemExit(f'Error in {frel}: Section number {i+1}'
                                 ' does not end with three blank lines')
    if ignore_section is not None:
        isectp1, tgt_title = ignore_section
        assert isectp1>=1
        isect = isectp1-1
        if isect >= len(m):
            raise SystemExit(f"Too few sections in {frel}")
        hdr_text,hdr_type = m[isect][0]
        if hdr_text != tgt_title:
            raise SystemExit(f'Unexpected section name in {frel}. '
                             f'Section number {isect+1}, '
                             f'expected title "{tgt_title}", '
                             f'got "{hdr_text}".')
        m[isect][1]=['<ignored>']
        m[isect][0][0]=['<ignored>']
    return frel, m

def identical(frel1,frel2):
    return resolve(frel1).read_text() == resolve(frel2).read_text()
def main():

    assert identical('mcpl_core/README.md','mcpl_core/empty_pypkg/README.md')

    variant_section = 2
    m_repo = load('README.md',
                  ignore_section=(variant_section,
                                  'The mcpl repository'))
    m_core = load('mcpl_core/README.md',
                  ignore_section=(variant_section,
                                  'The mcpl-core package'))
    m_py = load('mcpl_python/README.md',
                ignore_section=(variant_section,
                                'The mcpl-python package'))
    m_meta = load('mcpl_metapkg/README.md',
                  ignore_section=(variant_section,
                                  'The mcpl package'))
    m_extra = load('mcpl_extra/README.md',
                   ignore_section=(variant_section,
                                   'The mcpl-extra package'))
    m_ref = m_repo
    m_other_list = [m_repo,m_core,m_py,m_meta,m_extra]
    for m in m_other_list:
        if m[1] != m_ref[1]:
            raise SystemExit('Files differ outside of section 2:'
                             f' {m_ref[0]} {m[0]}')

    #Load other markdown files for minimal checking:
    load('INSTALL.md',validate_hdrtypes=False)
    load('NOTICE.md')
