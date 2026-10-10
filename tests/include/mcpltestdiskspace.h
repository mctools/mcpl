
/******************************************************************************/
/*                                                                            */
/*  This file is part of MCPL (see https://mctools.github.io/mcpl/)           */
/*                                                                            */
/*  Copyright 2015-2026 MCPL developers.                                      */
/*                                                                            */
/*  Licensed under the Apache License, Version 2.0 (the "License");           */
/*  you may not use this file except in compliance with the License.          */
/*  You may obtain a copy of the License at                                   */
/*                                                                            */
/*      http://www.apache.org/licenses/LICENSE-2.0                            */
/*                                                                            */
/*  Unless required by applicable law or agreed to in writing, software       */
/*  distributed under the License is distributed on an "AS IS" BASIS,         */
/*  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  */
/*  See the License for the specific language governing permissions and       */
/*  limitations under the License.                                            */
/*                                                                            */
/******************************************************************************/

#ifndef mcpltestdiskspace_h
#define mcpltestdiskspace_h

/* Utilities for tests creating huge files. */

#ifndef _WIN32
#  include <sys/statvfs.h>
#  include <unistd.h>
#endif

/* Free disk space (bytes) in the file system of the current directory, or -1
   if it can not be determined. */
static double mcpltests_free_disk_space( void )
{
#ifdef _WIN32
  //NB: Implement on windows if ever needed
  return 1e18;
#else
  struct statvfs s;
  if ( statvfs( ".", &s ) != 0 )
    return -1.0;
  return (double)s.f_bavail * (double)s.f_frsize;
#endif
}

/* Wait (up to max_seconds) until there are at least nbytes of free disk space
   in the file system of the current directory. Some file systems (like UFS on
   FreeBSD) free the space of deleted files with a delay, so the space of huge
   files deleted by a previous test might not be available immediately. Returns
   the free disk space (or -1 if it can not be determined, in which case it
   does not wait). */
static double mcpltests_wait_for_disk_space( double nbytes, int max_seconds )
{
  double avail = mcpltests_free_disk_space();
  int i;
  for ( i = 0; i < max_seconds && avail >= 0.0 && avail < nbytes; ++i ) {
#ifndef _WIN32
    sleep( 1 );
#endif
    avail = mcpltests_free_disk_space();
  }
  return avail;
}

#endif
