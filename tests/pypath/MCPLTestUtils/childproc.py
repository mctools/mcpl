
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

"""

   Running functions in child processes, for instance functions of the C test
   libraries, which end the process at MCPL errors. A child process is reused
   until a call ends it, and the next children are always started in advance,
   since starting processes is slow on some platforms.

   Example (with fct defined in an importable module, not in the test script):

     from MCPLTestUtils.childproc import ChildProcess, exit_with_result

     def fct( x ):
         if x < 0:
             exit_with_result('negative')#ends the child process
         return 2*x

     with ChildProcess() as c:
         c.call( fct, 3 )#returns 6
         c.call( fct, -3 )#returns 'negative' (next call uses a new child)

   The children import only the modules of the functions called, and the
   arguments and results must be picklable.

"""

import os
import sys

_out = None#the stream for results in the child processes

def _send( value ):
    import pickle
    pickle.dump( value, _out )
    _out.flush()

def exit_with_result( value ):
    """Ends the child process, with value as the result of the current call
    (only to be used inside functions called through ChildProcess.call)."""
    _send( ( True, value ) )
    _out.close()
    os._exit(0)

def call_lib_fct( libname, fctname, args ):
    """Calls a function of a C test library, returning (error message or None,
    printouts, return value). To be called through ChildProcess.call, since
    MCPL errors end the process."""
    from .loadlib import getlib
    lib = getlib(libname)
    prints = []
    def on_print( msg ):
        prints.append(msg)
    def on_error( msg ):
        exit_with_result( ( msg, ''.join(prints), None ) )
    lib.mcpltestdetail_set_print_handler(on_print)
    lib.mcpltestdetail_set_error_handler(on_error)
    rv = getattr(lib,fctname)(*args)
    return None, ''.join(prints), rv

class ChildProcess:

    def __init__( self, nahead = 2 ):
        """nahead: the number of children started in advance"""
        self.__proc = None#the child process in use
        self.__ahead = [ self.__start() for i in range(nahead) ]

    def call( self, fct, *args, cwd = None ):
        """Calls fct(*args) in a child process (in the directory cwd, if
        given) and returns the result."""
        import pathlib
        import pickle
        if self.__proc is None:
            self.__proc = self.__ahead.pop(0)
            self.__ahead.append( self.__start() )#started while others are used
        if cwd is not None:
            cwd = str(pathlib.Path(cwd).absolute())
        p = self.__proc
        try:
            pickle.dump( ( fct.__module__, fct.__qualname__, args, cwd ), p.stdin )
            p.stdin.flush()
            ended, rv = pickle.load( p.stdout )
        except ( EOFError, OSError ):
            self.__proc = None
            _end_child( p )
            raise RuntimeError('Child process ended without a result')
        if ended:
            self.__proc = None
            _end_child( p )
        return rv

    def close( self ):
        """Ends the child processes (the one in use, if any, and those
        started in advance)."""
        procs = self.__ahead + ( [ self.__proc ] if self.__proc else [] )
        self.__proc, self.__ahead = None, []
        for p in procs:
            _end_child( p )

    def __enter__( self ):
        return self

    def __exit__( self, *exc ):
        self.close()

    def __start( self ):
        import subprocess
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join( p for p in sys.path if p )
        return subprocess.Popen( [ sys.executable, '-m', 'MCPLTestUtils.childproc' ],
                                 stdin = subprocess.PIPE, stdout = subprocess.PIPE,
                                 env = env )

def _end_child( p ):
    #Closing its input ends the child (if not already gone). Waiting until the
    #process is gone, so its files are closed (open files can not be removed
    #on Windows):
    try:
        p.stdin.close()
    except OSError:
        pass
    p.wait()
    p.stdout.close()

def _child_main():
    import importlib
    import pickle
    global _out
    #The results are sent through the original stdout, while any other output
    #to stdout goes to stderr:
    _out = os.fdopen( os.dup(1), 'wb' )
    os.dup2( 2, 1 )
    sys.stdout = sys.stderr
    while True:
        try:
            request = pickle.load( sys.stdin.buffer )
        except EOFError:
            return
        modname, fctname, args, cwd = request
        fct = importlib.import_module(modname)
        for n in fctname.split('.'):
            fct = getattr(fct,n)
        oldcwd = os.getcwd()
        if cwd is not None:
            os.chdir(cwd)
        try:
            rv = fct(*args)
        finally:
            os.chdir(oldcwd)
        _send( ( False, rv ) )

if __name__ == '__main__':
    #Not _child_main() of this __main__ module, but of the importable one used
    #by the called functions (for exit_with_result):
    from MCPLTestUtils.childproc import _child_main as main
    main()
