include_guard()

function( setup_zlib )
  #Function which detects and/provide ZLib support and sets the variable
  #MCPL_ZLIB in the surrounding scope. If this variable evaluates to True, zlib
  #support is enabled.
  set( zlib_fetch_sources https://github.com/madler/zlib/archive/v1.2.13.tar.gz )
  set( zlib_fetch_sources_sha256 1525952a0a567581792613a9723333d7f8cc20b87a81f920fb8bc7e3f2251428 )

  set( MCPL_ZLIB OFF PARENT_SCOPE )
  set( _mcpl_zlib_extra_compile_definitions "" PARENT_SCOPE )
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

  #Avoid annoying warning (since zlib does not add VERSION in project call but
  #as standalone variable):
  set(CMAKE_POLICY_DEFAULT_CMP0048 NEW)

  #Populate and add_subdirectory:
  FetchContent_MakeAvailable(zlib)

  #Get zlib source files:
  get_target_property( zlib_source_files zlibstatic SOURCES)
  set( tmp_zlibsrcfiles "" )
  foreach( zlibfile ${zlib_source_files} )
    if ( IS_ABSOLUTE ${zlibfile} )
      list( APPEND tmp_zlibsrcfiles "${zlibfile}" )
    else()
      list( APPEND tmp_zlibsrcfiles "${zlib_SOURCE_DIR}/${zlibfile}" )
    endif()
  endforeach()

  #get compile definitions needed for these source files, both from the target and the directory:
  set( _mcpl_zlib_extra_compile_definitions "")
  #NB: The COMPILE_DEFINITIONS are the PRIVATE+PUBLIC definitions. If we need
  #the INTERFACE/PUBLIC definitions we would have to look at the
  #INTERFACE_COMPILE_DEFINITIONS. In principle we should add those to the OTHER
  #(i.e. non-zlib) source files for a given mcpl target.
  get_target_property( tmp_defs1 zlibstatic COMPILE_DEFINITIONS)
  if ( tmp_defs1 )
    list(APPEND _mcpl_zlib_extra_compile_definitions ${tmp_defs1} )
  endif()
  get_directory_property( tmp_defs2 DIRECTORY "${zlib_SOURCE_DIR}" COMPILE_DEFINITIONS )
  if ( tmp_defs2 )
    list(APPEND _mcpl_zlib_extra_compile_definitions ${tmp_defs2} )
  endif()

  #results:
  set( MCPL_ZLIB "${tmp_zlibsrcfiles}" PARENT_SCOPE )
  set( _mcpl_zlib_extra_compile_definitions "${_mcpl_zlib_extra_compile_definitions}" PARENT_SCOPE )
  message(STATUS "ZLIB sources built into MCPL code: ${tmp_zlibsrcfiles}")
  message(STATUS "Extra definitions for ZLIB sources built into MCPL code: ${_mcpl_zlib_extra_compile_definitions}")
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
    if ( _mcpl_zlib_extra_compile_definitions )
      set_source_files_properties( ${MCPL_ZLIB} PROPERTIES COMPILE_DEFINITIONS "${_mcpl_zlib_extra_compile_definitions}" )
    endif()
  endif()
  if ( ARGN )
    target_compile_definitions( ${targetname} PRIVATE ${ARGN} )
  endif()
endfunction()
