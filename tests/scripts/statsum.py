
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
from MCPLTestUtils.dirs import test_data_dir
import pathlib
lib = getlib('statsum')

def dump( filename ):
    lib.mcpltest_dump( filename )

def create( filename='f.mcpl', *,
            statsum = None,
            comment = None,
            comment2 = None,
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
    if comment2 is None:
        comment2 = '<NONE>'
    assert 0 <= nparticles <= 4294967295
    lib.mcpltest_createstatsumfile( filename,
                                    sc_name,
                                    sc_val,
                                    comment,
                                    comment2,
                                    int(nparticles) )
    assert p.is_file()
    if do_dump:
        dump(filename)
        print_pystatsum(filename)

def create_bad( *a, **kw ):
    lib.run_fct_expected_to_fail(create,*a,**kw)

def decodestatsum(s):
    assert s.isascii()
    assert s.startswith('stat:sum:')
    _,_,key,value = s.split(':')
    assert 1<=len(key)<=64
    assert key.isidentifier()
    assert len(value)==24
    if not all(e in '0123456789.-+eE' for e in value.strip(' ')):
        raise RuntimeError('Issues with statsum valstr: "%s"'%value)
    val = float(value.strip(' '))
    return key, val

def print_pystatsum( filename ):
    filenamebn = str(filename).replace('\\','/').split('/')[-1]
    s = f"=== PyAPI view of {filenamebn} stat:sum: ==="
    print(s,flush=True)
    import mcpldev as mcplpy

    m = mcplpy.MCPLFile(filename)
    d = m.stat_sum
    expected_comments = []
    if not d:
        print( "<no stat sum entries>",flush=True)
    else:
        for k,v in d.items():
            expected_comments.append(mcplpy.encode_stat_sum( k, v ))
            if v is not None:
                v = '%.15g'%v
            print(f'    {k} = {v}',flush=True)
    print('='*len(s),flush=True)

    actual_statsums = [ decodestatsum(e) for e in m.comments
                        if e.startswith('stat:sum:') ]

    for e in expected_comments:
        keyval = decodestatsum( e )
        if keyval not in actual_statsums:
            raise SystemExit('Problems with python encoding to "%s"'%e)


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
    create(    comment='stat:sum:bla: .1234567801234567891234')
    create_bad(comment='stat:sum:bla:\t.1234567801234567891234')
    create(    comment='stat:sum:bla:1.123456780123456789123 ')
    create(    comment='stat:sum:bla:               1.123e102')
    create_bad(comment='stat:sum:bla:               1.123e1.2')
    create_bad(comment='stat:sum:bla:1.123456780123456789123\t')
    create_bad(comment='stat:sum:bla: 1e999                  ')
    create_bad(comment='stat:whatever')
    create_bad(comment='stat:sum:bla:                        ')
    create(    comment='stat:sum:bla:                     1.2',
               comment2='stat:sum:bla2:                     3.4')
    create_bad(comment='stat:sum:bla:                     1.2',
               comment2='stat:sum:bla:                     3.4')
    create_bad(statsum=('bla',4.0),
               comment='stat:sum:bla:                     1.2',
               comment2='stat:sum:bla2:                     3.4')

    for f in ['ref_statunsupported.mcpl.gz','ref_statsum.mcpl.gz']:
        print_pystatsum( test_data_dir.joinpath('ref',f))



if __name__ == '__main__':
    main()
