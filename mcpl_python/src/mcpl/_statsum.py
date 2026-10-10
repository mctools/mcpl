
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

"""Encoding and decoding of stat:sum: comments."""

__all__ = ['encode_stat_sum', 'is_valid_stat_sum_key']

from ._common import MCPLError


def encode_stat_sum( key, value ):
    """
    Function which can help encode a key and value into the special format
    needed for "stat:sum:..." comments in MCPL headers. A value of either None
    or -1.0 maps to -1.0 in the encoding.
    """
    import math
    if not is_valid_stat_sum_key(key):
        raise MCPLError(f'invalid key for scat:sum: entries: "{key}"')
    if hasattr(key,'decode'):
        key = key.decode('ascii')
    value = float(-1.0 if value is None else value)
    if ( math.isinf(value)
         or math.isnan(value)
         or not ( value==-1.0 or value>=0.0) ):
        raise MCPLError('stat:sum: values must be non-nan, '
                        'non-inf and either -1.0 or >=0.0')
    v = f'{value:24.15g}'
    if float(v)!=value:
        v = f'{value:24.17g}'
    return f'stat:sum:{key}:{v}'

def is_valid_stat_sum_key( key ):
    """
    Function which can be used to verify that a particular key has the correct
    format needed for "stat:sum:..." comments in MCPL headers.
    """
    if not ( ( 1<=len(key)<=64 ) and key.isascii() and key.isidentifier() ):
        return False
    k0 = key[0].lower()
    if hasattr(k0,'decode'):
        return b'a' <= k0 <= b'z'
    else:
        return 'a' <= k0 <= 'z'

def _parse_statsum_comment( comment ):
    prefix = b'stat:sum:'
    lval = 24
    err = ( False, (None, None) )
    if not comment.startswith(prefix):
        return err
    c = comment[len(prefix):].split(b':')
    if ( len(c) != 2 or len(c[1])!=lval ):
        return err
    keyb, valstr = c
    key = keyb.decode('ascii',errors='ignore')
    if len(keyb) != len(key) or not is_valid_stat_sum_key(key):
        return err
    valstr = valstr.strip(b' ')#remove leading and trailing simple spaces
    if not all(e in b'0123456789.-+eE' for e in valstr):
        return err
    try:
        val = float(valstr)
    except ValueError:
        val = None
    import math
    if ( val is None or math.isinf(val) or math.isnan(val)
         or not (val == -1.0 or val>=0.0) ):
        return err
    return ( True, (key,val) )

def _parse_statsum( comments ):
    #Parse list of byte strings for any stat:sum: entries.
    d = {}
    prefix = b'stat:sum:'
    error_comment = None
    for comment in comments:
        if not comment.startswith(prefix):
            continue
        ok, (key,val) = _parse_statsum_comment( comment)
        if ok:
            if key in d:
                raise MCPLError('Duplicate stat:sum: key. The key '
                                f'"{key}" appears more than once in the file.')
            d[key] = None if val == -1.0 else val
        else:
            error_comment = comment
            break
    if error_comment:
        example = error_comment.decode('utf-8',errors='backslashreplace')
        raise MCPLError('Input has "stat:sum:..." comment entry not'
                        f' following the specification: "{example}"')
    return d
