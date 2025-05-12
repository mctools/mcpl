
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
lib = getlib('statsum')

def dump( filename ):
    lib.mcpltest_dump( filename )

def create( filename='f.mcpl', *,
            statsum = None,
            comment = None,
            nparticles = 0,
            do_dump = True ):
    print(flush=True,end='')
    p = pathlib.Path(filename)
    if p.is_file():
        p.unlink()
    if statsum:
        sc_name,sc_val = statsum
    else:
        sc_name,sc_val = '<NONE>',-99.0
    if comment is None:
        comment = '<NONE>'
    assert 0 <= nparticles <= 4294967295
    lib.mcpltest_createstatsumfile( filename,
                                      sc_name,
                                      sc_val,
                                      comment,
                                      int(nparticles) )
    assert p.is_file()
    if do_dump:
        dump(filename)
        print_pystatsum(filename)

def create_bad( *a, **kw ):
    lib.run_fct_expected_to_fail(create,*a,**kw)

def print_pystatsum( filename ):
    s = f"=== PyAPI view of {filename} stat:sum: ==="
    print(s,flush=True)
    import mcpldev as mcpl
    m = mcpl.MCPLFile(filename)
    d = m.stat_sum
    if not d:
        print( "<no stat sum entries>",flush=True)
    else:
        for k,v in d.items():
            if v is not None:
                v = '%.15g'%v
            print(f'    {k} = {v}',flush=True)
    print('='*len(s),flush=True)

def main():
    lib.dump()
    create()
    create(statsum=('a'*63,0.0))
    create(statsum=('a'*64,0.0))
    create_bad(statsum=('a'*65,0.0))
    create(statsum=('hello',1.7976931348623157e+308))#largest dbl not inf
    create_bad(statsum=('hello',1.7976931348623159e+308))#a bit larger
    create_bad(statsum=('hello',float('inf')))
    create_bad(statsum=('hello',-float('inf')))
    create_bad(statsum=('hello',float('nan')))
    create(statsum=('hello',-1))
    create_bad(statsum=('hello',-1.000000001))
    create(statsum=('hello',-0.0))
    create(statsum=('hello',5.0))

    create_bad(statsum=(' hello',5.0))
    create_bad(statsum=('hello ',5.0))
    oslash='\u00f8'
    create_bad(statsum=(f'hell{oslash}',5.0))
    create_bad(statsum=('hel lo',5.0))
    create_bad(statsum=('hel\rlo',5.0))
    create_bad(statsum=('hel.lo',5.0))
    create_bad(statsum=('hel\tlo',5.0))
    create_bad(statsum=('',5.0))
    create_bad(statsum=(' ',5.0))
    create(statsum=('hel_lo',5.0))
    create_bad(statsum=('1hello',5.0))
    create_bad(statsum=('_hello',5.0))

    #Adding stat:sum: comments directly is allowed, but will result in a
    #warning in case of failure to adhere to the convention (but when writing or
    #reading).
    create_bad(comment='stat:sum:bla:1.2432245')#too short value buffer
    create(    comment='stat:sum:bla:1.1234567801234567891234')
    create(comment='stat:sum:bla:1.123456780123456789123 ')
    create_bad(comment='stat:sum:bla:1.123456780123456789123\t')
    create_bad(comment='stat:sum:bla: 1e999                  ')

if __name__ == '__main__':
    main()
