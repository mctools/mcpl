
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


"""Messages and warnings to the user, printed or sent to the logger "mcpl"."""

__all__ = ['use_logging']

_logger = None

def use_logging( enable = True ):
    """Send messages and warnings from MCPL to the logger named "mcpl" (as
    logging.INFO and logging.WARNING records), instead of printing them to
    stdout (prefixed with "MCPL:" and "MCPL WARNING:"), which is the default.
    After that, they are controlled by the logging configuration of the
    application, e.g.:

       import logging
       import mcpl
       mcpl.use_logging()
       logging.basicConfig(level=logging.INFO)

    Calling use_logging(False) switches back to printing. Note that this does
    not affect functions which are meant to print (like dump_file), nor the
    pymcpltool command, which always prints."""
    global _logger
    if enable:
        import logging
        _logger = logging.getLogger('mcpl')
    else:
        _logger = None

class _ForcePrinting:
    """Context manager for printing messages, even if use_logging() was
    called."""
    def __enter__(self):
        global _logger
        self._orig, _logger = _logger, None
    def __exit__(self, *args):
        global _logger
        _logger = self._orig

def _info( msg ):
    if _logger is None:
        print(f'MCPL: {msg}')
    else:
        _logger.info(msg)

def _warning( msg ):
    if _logger is None:
        print(f'MCPL WARNING: {msg}')
    else:
        _logger.warning(msg)
