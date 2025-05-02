
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

"""

   A utility Lib class which can be used to access compiled test libraries, and
   the extern "C" functions defined within. If the library defines a
   mcpltest_ctypes_dictionary() function, it can even be loaded directly and the
   returned dictionary string will be inspected to set up functions
   automatically.

   Example of such a dictionary function:

   extern "C" const char * mcpltest_ctypes_dictionary()
   {
     return
       "int mcpltest_file_exists( const char * );"
       "const char * mcpltest_getsomestr();"
     ;
   }

"""

import ctypes

_libdb = {}
def getlib( libname ):
    n = _normalise_testmod_name(libname)
    if n not in _libdb:
        _libdb[n] = Lib(n)
    return _libdb[n]

def _run_fail_fct(libname,realfct,*args,**kwargs):
    lib = getlib(libname)
    with lib.mcplerror_print_prefix_mgr('Got expected MCPL ERROR'):
        realfct(*args,**kwargs)

class Lib:
    def __init__( self, test_shlib_name ):
        self.__name = _normalise_testmod_name( test_shlib_name )
        self.__lib = _ctypes_load_testmod( test_shlib_name )
        self.__fcts = set()
        if not hasattr(self.__lib,'mcpltest_ctypes_dictionary'):
            print("Warning: No mcpltest_ctypes_dictionary symbol"
                  " in testmod %s"%self.__name)
        else:
            dictfct = _ctypes_create_fct( self.__lib,
                                          'mcpltest_ctypes_dictionary',
                                          ctypes.c_char_p )
            dictfctlist = dictfct().split(';')
            dictfctlist += [
                'void mcpltestdetail_set_print_handler(VOIDFCT_CSTR_ARG)',
                'void mcpltestdetail_set_error_handler(VOIDFCT_CSTR_ARG)',
                'void mcpltestdetail_exit1()'
            ]
            for e in dictfctlist:
                e=e.strip()
                if e:
                    self.add_signature(e)
            del dictfct
        self._redirect_stdout()

    def _redirect_stdout(self):
        #Make sure mcpl printouts go via Python stdout stream:
        self.mcpltestdetail_set_print_handler(
            lambda msg : print( msg,end='',flush=True)
        )

    def mcplerror_print_prefix(self, prefix):
        if prefix is None:
            #Revert to builtin:
            self.mcpltestdetail_set_error_handler(None)
            return
        #Make sure mcpl printouts go via Python stdout stream:
        exit1_fct = self.mcpltestdetail_exit1
        def error_handler(msg):
            print('%s: %s'%(prefix,msg),flush=True)
            exit1_fct()
        self.mcpltestdetail_set_error_handler(error_handler)

    def mcplerror_print_prefix_mgr(self, prefix):
        ppfct = self.mcplerror_print_prefix
        class M:
            def __enter__(self):
                ppfct(prefix)
            def __exit__(self,*args):
                ppfct(None)
        return M()

    def run_fct_expected_to_fail(self,fct,*args,**kwargs):
        import multiprocessing as mp
        mp = mp.get_context(None) # Note: None->'spawn' can be used to emulate
                                  # macos/windows behaviour (it is perhaps ~10
                                  # times slower).
        p = mp.Process( target =_run_fail_fct,
                        args =[ self.__name,fct,*args],
                        kwargs=kwargs )
        p.start()
        p.join()
        if p.exitcode == 0:
            raise RuntimeError('Function call did not fail as expected')

    def add_signature( self, fct_signature ):
        return self.add(fct_signature,
                        '__include_fct_name__')

    def add( self, fctname, restype, *argtypes ):
        if restype=='__include_fct_name__':
            ( fctname,
              restype,
              argtypes) = _decode_signature_str(fctname,
                                                include_fct_name = True)
        elif len(argtypes)==0 and isinstance(restype,str) and '(' in restype:
            ( restype,
              argtypes ) = _decode_signature_str(restype,
                                                 include_fct_name = False)
        fct = _ctypes_create_fct( self.__lib,
                                  fctname,
                                  restype,
                                  *argtypes,
                                  libobj = self )
        fct.__name__ = fctname
        assert not hasattr(self,fctname),f'Fct {repr(fctname)} already added!'
        self.__fcts.add( (fctname,restype,argtypes) )
        setattr(self,fctname,fct)

    @property
    def functions(self):
        """Get the name of all available functions in this library"""
        return sorted([f for f,_,_ in self.__fcts])

    def dump(self,prefix=''):
        """Print available functions in this library"""
        print('%sLibrary "%s" (%i functions):'%(prefix,
                                                self.__name,
                                                len(self.__fcts)))
        if not self.__fcts:
            print(f"{prefix}  <no functions defined>")
        for fctname,restype,argtypes in sorted(self.__fcts):
            rt = _ctype_2_str(restype)
            a=', '.join([_ctype_2_str(e) for e in argtypes])
            print(f"{prefix}  {rt} {fctname}({a})")


VOIDFCT_NO_ARG = ctypes.CFUNCTYPE( None )
VOIDFCT_CSTR_ARG = ctypes.CFUNCTYPE( None, ctypes.c_char_p )

_map_str2ctype = { 'const char *':ctypes.c_char_p,
                   'void' : 'void',
                   'int':ctypes.c_int,
                   'uint':ctypes.c_uint,
                   'unsigned':ctypes.c_uint,
                   'double':ctypes.c_double,
                   'VOIDFCT_NO_ARG': VOIDFCT_NO_ARG,
                   'VOIDFCT_CSTR_ARG': VOIDFCT_CSTR_ARG,
                  }

def _decode_type_str( s ):
    s=' '.join(s.replace('*',' * ').strip().split())
    return _map_str2ctype.get(s,s)

def _ctype_2_str( ct ):
    for k,v in _map_str2ctype.items():
        if ct is v:
            return k
    raise ValueError("ctype not in map: %s"%ct)

def _decode_signature_str( signature, include_fct_name ):
    signature=signature.strip()
    assert signature.count('(')==1
    assert signature.count(')')==1
    assert signature.index(')')+1==len(signature)
    r,args = signature[:-1].split('(',2)
    args = list( a for a in args.split(',') ) if args.strip() else []

    if include_fct_name:
        r = r.split()
        assert len(r) >= 2
        fctname = r[-1]
        r = ' '.join(r[:-1])
    else:
        fctname = None
    r = _decode_type_str(r)
    args = tuple( _decode_type_str(a) for a in args )
    if fctname is None:
        return r,args
    else:
        return fctname,r,args

_keepalive_mcpllib = [None]
def _load_lib_with_ctypes( path ):
    assert path.is_file()

    import platform
    if platform.system()=='Windows':
        #NOTE: Avoid DLL load errors by preloading MCPL lib.
        if _keepalive_mcpllib[0] is None:
            from .dirs import mcpllib
            _keepalive_mcpllib[0] = ctypes.CDLL(str(mcpllib))

    try:
        lib = ctypes.CDLL(path)
    except TypeError:
        lib = None

    if lib is None:
        #For some reason, on windows we get a TypeError and must pass a string
        #rather than a pathlib object:
        lib = ctypes.CDLL(str(path))
        #NB: We might also get here a FileNotFoundError here in case of missing
        #symbols.

    return lib

def _ctypes_load_testmod( test_shlib_name ):
    libpath = _find_testmod(test_shlib_name)
    return _load_lib_with_ctypes(libpath)

def _str2cstr(s):
    #converts any string (str,bytes,unicode,path) to bytes
    if hasattr(s,'__fspath__'):
        s = str(s)
    try:
        return s if isinstance(s,bytes) else s.encode('utf8')
    except UnicodeEncodeError as e:
        raise RuntimeError("Only unicode strings are supported") from e

def _cstr2str(s):
    #converts bytes object to str
    try:
        return s if isinstance(s,str) else s.decode('utf8')
    except UnicodeDecodeError as e:
        raise RuntimeError("Only UTF8-encoded C-strings are supported") from e

_keepalive_fcts = []

def _ctypes_create_fct( lib, fctname, restype, *argtypes, libobj = None ):

    def resolve_type( tpe ):
        if tpe is None or tpe=='void':
            return None
        return ( getattr(ctypes,tpe)
                 if isinstance(tpe,str) and hasattr(ctypes,tpe)
                 else tpe )
    assert hasattr(lib,fctname), f"Missing symbol: {fctname}"
    rawfct = getattr(lib,fctname)
    rawfct.restype = resolve_type(restype)
    argtypes = tuple( resolve_type(a) for a in argtypes )
    rawfct.argtypes = argtypes
    def fct( *args ):
        if len(args) != len(argtypes):
            raise RuntimeError(f"{fctname}(..) takes {len(argtypes)} "
                               f"args ({len(args)} provided)")
        al = []
        for a,at in zip(args,argtypes):
            if at == ctypes.c_char_p:
                al.append( _str2cstr(a) )
            elif at == VOIDFCT_NO_ARG:
                if a is not None:
                    _keepalive_fcts.append(a)
                al.append( ctypes.cast( a, VOIDFCT_NO_ARG ) )
            elif at == VOIDFCT_CSTR_ARG:
                if a is None:
                    al.append( ctypes.cast( None, VOIDFCT_CSTR_ARG ) )
                else:
                    def afct( arg_cstr ):
                        pystr = _cstr2str(arg_cstr)#todo: allow binary (non-utf8)?
                        a(pystr)
                    afct2 = VOIDFCT_CSTR_ARG(afct)
                    _keepalive_fcts.append(afct)
                    _keepalive_fcts.append(afct2)
                    al.append( ctypes.cast( afct2, VOIDFCT_CSTR_ARG ) )
            else:
                al.append( a )
        rv = rawfct( *al )
        if restype == ctypes.c_char_p:
            rv = _cstr2str( rv )
        return rv
    return fct

def _normalise_testmod_name(name):
    return name if name.startswith('TestMod_') else f'TestMod_{name}'

def _find_testmod(name):
    import pathlib
    import os
    tln = _normalise_testmod_name(name)
    #Normal cmake:
    locdir = pathlib.Path(os.environ.get('MCTOOLS_TESTMODULES_LOCDIR'))
    assert locdir.is_dir()
    f = locdir / f'module_loc_{tln}.txt'
    lib = pathlib.Path(f.read_text().strip())
    assert lib.is_file()
    return lib
