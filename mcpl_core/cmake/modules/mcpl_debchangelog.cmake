
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

#Converts the CHANGELOG in the repository root into a Debian changelog and
#installs it gzipped as share/doc/<pkgname>/changelog.gz. Does nothing if the
#CHANGELOG (absent in e.g. sdists) or gzip is not available.

#"YYYY-MM-DD" -> "Www, DD Mmm YYYY 00:00:00 +0000" (RFC 2822):
function( _mcpl_rfc2822_date date outvar )
  if ( NOT date MATCHES "^([0-9]+)-0?([0-9]+)-0?([0-9]+)$" )
    message( FATAL_ERROR "Invalid date in CHANGELOG: ${date}" )
  endif()
  set( y "${CMAKE_MATCH_1}" )
  set( m "${CMAKE_MATCH_2}" )
  set( d "${CMAKE_MATCH_3}" )
  #Day of week (Sakamoto's method, 0=Sunday):
  set( yy "${y}" )
  if ( m LESS 3 )
    math( EXPR yy "${y} - 1" )
  endif()
  math( EXPR mi "${m} - 1" )
  list( GET _mcpl_t "${mi}" t )
  math( EXPR dow "(${yy} + ${yy}/4 - ${yy}/100 + ${yy}/400 + ${t} + ${d}) % 7" )
  list( GET _mcpl_wdays "${dow}" wday )
  list( GET _mcpl_months "${mi}" mon )
  if ( d LESS 10 )
    set( d "0${d}" )
  endif()
  set( "${outvar}" "${wday}, ${d} ${mon} ${y} 00:00:00 +0000" PARENT_SCOPE )
endfunction()
set( _mcpl_t 0 3 2 5 0 3 5 1 4 6 2 4 )
set( _mcpl_wdays Sun Mon Tue Wed Thu Fri Sat )
set( _mcpl_months Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec )

function( mcpl_install_debian_changelog pkgname maintainer )
  set( infile "${PROJECT_SOURCE_DIR}/../CHANGELOG" )
  find_program( MCPL_GZIP_CMD gzip )
  if ( NOT MCPL_GZIP_CMD OR NOT EXISTS "${infile}" )
    return()
  endif()
  file( READ "${infile}" txt )
  #Entries are indented by 6 (bullets) or 8 (continuation) spaces, Debian
  #wants 2 and 4:
  string( REGEX REPLACE "\n    " "\n" txt "\n\n${txt}" )
  string( REGEX REPLACE "[ \n]+$" "" txt "${txt}" )
  #Release headers are "vX.Y.Z YYYY-MM-DD" (no date if work in progress):
  string( REGEX MATCHALL "\n\nv[0-9][^\n]*\n" headers "${txt}" )
  string( TIMESTAMP today "%Y-%m-%d" UTC )#respects SOURCE_DATE_EPOCH
  set( trailer "" )
  foreach( hdr IN LISTS headers )
    string( REGEX MATCH "v([0-9.]+) +([0-9-]*)" dummy "${hdr}" )
    set( ver "${CMAKE_MATCH_1}" )
    set( date "${CMAKE_MATCH_2}" )
    if ( NOT date )
      set( date "${today}" )
    endif()
    _mcpl_rfc2822_date( "${date}" date )
    string( REPLACE "${hdr}"
      "${trailer}\n\n${pkgname} (${ver}) unstable; urgency=medium\n\n"
      txt "${txt}" )
    set( trailer "\n\n -- ${maintainer}  ${date}" )
  endforeach()
  string( REGEX REPLACE "^\n+" "" txt "${txt}${trailer}\n" )
  set( outdir "${PROJECT_BINARY_DIR}/debian" )
  file( WRITE "${outdir}/changelog" "${txt}" )
  execute_process( COMMAND "${MCPL_GZIP_CMD}" -9nc "${outdir}/changelog"
    OUTPUT_FILE "${outdir}/changelog.gz" RESULT_VARIABLE rc )
  if ( NOT rc EQUAL 0 )
    message( FATAL_ERROR "Failed to gzip ${outdir}/changelog" )
  endif()
  install( FILES "${outdir}/changelog.gz" DESTINATION "share/doc/${pkgname}" )
endfunction()
