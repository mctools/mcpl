
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

# For checking some file that must be kept completely synchronised.

def get_content( relpath ):
    from .dirs import reporoot
    print(f'    {relpath}')
    return reporoot.joinpath(relpath).read_text()

def check_same( reffile, *otherfiles ):
    assert len(otherfiles) > 0
    print('  Checking for same contents:')
    ref = get_content( reffile )
    for o in otherfiles:
        if get_content(o) != ref:
            print()
            raise SystemExit(f'ERROR: Content of {o} and {reffile} differs')

def main():
    check_same( 'README.md',
                'mcpl_metapkg/README.md' )

    check_same( 'mcpl_core/README.md',
                'mcpl_core/empty_pypkg/README.md' )

    check_same( 'LICENSE',
                'mcpl_core/LICENSE',
                'mcpl_core/empty_pypkg/LICENSE',
                'mcpl_python/LICENSE',
                'mcpl_metapkg/LICENSE' )

    #fixme:
    #check_same( 'examples/mcpl_example_cpp.cc',
    #            'examples/downstream_cmake/main.cc' )

    #fixme:
    #check_same( 'mcpl_core/app_test/main.cc',
    #            'tests/src/app_cpp/main.cc' )

if __name__=='__main__':
    main()
