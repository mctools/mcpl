
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

#NB: Written carefully with __name__ protection we can call functions with
#pythons multiprocessing

from MCPLTestUtils.loadlib import getlib
import pathlib
lib = getlib('statcumul')

def dump( filename ):
    lib.mcpltest_dump( filename )

def create( filename='f.mcpl', *,
            statcumul = None,
            comment = None,
            nparticles = 0,
            do_dump = True ):
    p = pathlib.Path(filename)
    if p.is_file():
        p.unlink()
    if statcumul:
        sc_name,sc_val = statcumul
    else:
        sc_name,sc_val = '<NONE>',-99.0
    if comment is None:
        comment = '<NONE>'
    assert 0 <= nparticles <= 4294967295
    lib.mcpltest_createstatcumulfile( filename,
                                      sc_name,
                                      sc_val,
                                      comment,
                                      int(nparticles) )
    assert p.is_file()
    if do_dump:
        dump(filename)

def create_bad( *a, **kw ):
    lib.run_fct_expected_to_fail(create,*a,**kw)

def main():
    lib.dump()
    create()
    create(statcumul=('a'*63,0.0))
    create(statcumul=('a'*64,0.0))
    create_bad(statcumul=('a'*65,0.0))
    create(statcumul=('hello',1.7976931348623157e+308))#largest dbl not inf
    create_bad(statcumul=('hello',1.7976931348623159e+308))#a bit larger
    create_bad(statcumul=('hello',float('inf')))
    create_bad(statcumul=('hello',-float('inf')))
    create_bad(statcumul=('hello',float('nan')))
    create(statcumul=('hello',-1))
    create_bad(statcumul=('hello',-1.000000001))
    create(statcumul=('hello',-0.0))
    create(statcumul=('hello',5.0))

    create_bad(statcumul=(' hello',5.0))
    create_bad(statcumul=('hello ',5.0))
    oslash='\u00f8'
    create_bad(statcumul=(f'hell{oslash}',5.0))
    create_bad(statcumul=('hel lo',5.0))
    create_bad(statcumul=('hel\rlo',5.0))
    create_bad(statcumul=('hel.lo',5.0))
    create_bad(statcumul=('hel\tlo',5.0))
    create_bad(statcumul=('',5.0))
    create_bad(statcumul=(' ',5.0))
    create(statcumul=('hel_lo',5.0))
    create_bad(statcumul=('1hello',5.0))
    create_bad(statcumul=('_hello',5.0))

if __name__ == '__main__':
    main()
