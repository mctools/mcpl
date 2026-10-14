
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

#Tests that the C functions without _es raise the same errors (through the
#error handler) as their _es variants (which report errors in an error state).
#The functions without _es are wrappers which pass a NULL error state to the
#_es variants, so a few representative errors are enough here (all errors of
#the _es variants are tested in the app_errstate* tests). Errors raised through
#the error handler end the process, so these are run in subprocesses.

from MCPLTestUtils.loadlib import getlib

lib = getlib('errstate')

def call(name):
    lib.mcpltest_es_case(name,0)

def check(name):
    print(f'=== {name}')
    print(flush=True,end='')
    lib.mcpltest_es_case(name,1)
    print(flush=True,end='')
    lib.run_fct_expected_to_fail(call,name)
    print(flush=True,end='')

if __name__ == '__main__':
    lib.mcpltest_es_setup()
    for name in ( 'open_missing', 'open_truncated_header',
                  'read_truncated_data', 'comment_index', 'create_empty_name',
                  'add_nan_particle', 'srcname_too_late',
                  'transfer_before_read', 'merge_incompatible',
                  'merge_inplace_same_file', 'repair_not_broken' ):
        check(name)
