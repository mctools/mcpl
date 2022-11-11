include_guard()

function( setup_zlib )
  #Function which detects and/provide ZLib support and sets the variable
  #MCPL_ZLIB in the surrounding scope. If this variable evaluates to True, zlib
  #support is enabled.
  set( zlib_fetch_sources https://github.com/madler/zlib/archive/v1.2.13.tar.gz )
  set( zlib_fetch_sources_sha256 1525952a0a567581792613a9723333d7f8cc20b87a81f920fb8bc7e3f2251428 )

  set( MCPL_ZLIB OFF PARENT_SCOPE )
  if ( MCPL_ENABLE_ZLIB STREQUAL NEVER OR MCPL_ENABLE_ZLIB STREQUAL OFF )
    return()
  endif()
  if ( NOT MCPL_ENABLE_ZLIB STREQUAL FETCH )
    #look for preinstalled:
    find_package( ZLIB )
    if( ZLIB_FOUND )
      set ( MCPL_ZLIB standardzlibtarget PARENT_SCOPE )#FindZLIB module provides ZLIB::ZLIB target
      return()
    else()
      if ( MCPL_ENABLE_ZLIB STREQUAL IFAVAILABLE )
        return()
      endif()
      if ( MCPL_ENABLE_ZLIB STREQUAL USEPREINSTALLED )
        message(FATAL_ERROR "MCPL_ENABLE_ZLIB set to USEPREINSTALLED but failed to find zlib preinstalled.")
        return()
      endif()
    endif()
  endif()

  #Ok, must try to fetch + build! It is well that we do it here inside a
  #function, to prevent poluting most of our code with variables dealing with
  #this.
  message("Will fetch ZLib from ${zlib_fetch_sources} and build into all relevant MCPL binaries.")
  include(FetchContent)
  FetchContent_Declare( zlib URL "${zlib_fetch_sources}" URL_HASH "SHA256=${zlib_fetch_sources_sha256}" )

  #Variable used in zlib's CMakeLists.txt to prevent zlib files being installed
  #as a side-effect:
  set( SKIP_INSTALL_ALL True )
  FetchContent_MakeAvailable(zlib)
  get_target_property( zlib_source_files zlibstatic SOURCES)
  set(tmp "")
  foreach( zlibfile ${zlib_source_files} )
    if ( IS_ABSOLUTE ${zlibfile} )
      list( APPEND tmp "${zlibfile}" )
    else()
      list( APPEND tmp "${zlib_SOURCE_DIR}/${zlibfile}" )
    endif()
  endforeach()
  set( MCPL_ZLIB "${tmp}" PARENT_SCOPE )
endfunction()

setup_zlib()

function( add_zlib_dependency targetname )
  #Adds private ZLib dependency to target. Any extra arguments are assumed to be
  #compile definitions which should only be added if ZLib support is present.
  if ( NOT MCPL_ZLIB )
    return()
  endif()
  if ( MCPL_ZLIB STREQUAL standardzlibtarget )
    target_link_libraries( ${targetname} PRIVATE ZLIB::ZLIB )
  else()
    target_sources( ${targetname} PRIVATE ${MCPL_ZLIB} )
  endif()
  if ( ARGN )
    target_compile_definitions( ${targetname} PRIVATE ${ARGN} )
  endif()
endfunction()
