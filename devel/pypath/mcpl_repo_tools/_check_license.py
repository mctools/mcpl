
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

def do_check( files, allowed_file_hdr_list, *,
              allow_include_guards_if_hdr = False,
              ignore_fct = None ):

    def ignore_path( frel ):
        return ignore_fct(frel) if ignore_fct else False

    def text_ok( text ):
        return any(text.startswith(e) for e in allowed_file_hdr_list)

    def ok_with_incguard( f, text ):
        suffix = f.suffix
        if suffix.endswith('.in') and '.' in f.stem:
            suffix = '.' + f.stem.split('.')[-1]
        if not allow_include_guards_if_hdr or f.suffix not in ('.h','.hh'):
            return False
        lines = text.splitlines()
        if ( len(lines) > 10
             and lines[0].startswith('#ifndef ')
             and lines[1].startswith('#define ') ):
            return text_ok( '\n'.join(lines[2:]) )
        return False

    all_ok = True
    for f in files:
        text = f.read_text()
        if not text.strip():
            continue#allow empty files to not have license blurbs
        if not text_ok(text) and not ok_with_incguard(f,text):
            from .dirs import reporoot
            frel = str(f.relative_to(reporoot)).replace('\\','/')
            if ignore_path( frel ):
                print(f'  Ignoring known false positive: {frel}')
                continue
            print('bad license blurb:',f)
            all_ok = False
    return all_ok

def main():
    from .srciter import all_files_iter
    from .license import ( licenseblurb_data_with_doubledash_comments,
                           licenseblurb_data_with_hash_comments,
                           licenseblurb_data_with_ansic_comments )
    lbcpp = '\n' + licenseblurb_data_with_doubledash_comments()
    lbh = '\n' + licenseblurb_data_with_hash_comments()
    lbansic = '\n' + licenseblurb_data_with_ansic_comments()

    def ignore_c_headers(frel):
        return frel in [ 'tests/src/app_examples/example_filtermcpl.h',
                         'tests/src/app_examples/example_writemcpl.h',
                         'tests/src/app_examples/example_readmcpl.h' ]

    c1 = do_check( all_files_iter('py'),
                   [lbh,'#!/usr/bin/env python3\n'+lbh])
    c2 = do_check( all_files_iter('cpp'),
                   [lbcpp,lbcpp.lstrip()],
                   allow_include_guards_if_hdr = True )
    c3 = do_check( all_files_iter('c_headers'),
                   [lbansic,lbansic.lstrip()],
                   allow_include_guards_if_hdr = True,
                   ignore_fct = ignore_c_headers )
    c4 = do_check( all_files_iter('c_src'),
                   [lbcpp,lbcpp.lstrip()],
                   allow_include_guards_if_hdr = True )
    c5 = do_check( all_files_iter('cmake','toml'),
                   [lbh])
    if not (c1 and c2 and c3 and c4 and c5):
        raise SystemExit('ERROR: license blurb issues detected.')
    print("All ok!")

if __name__=='__main__':
    main()
