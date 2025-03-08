include_guard()

include( mcpl_utils )

#Variables. Note that if changing the default value of a variable with a
#corresponding deprecated variable below, the default value should be modified
#in the add_deprecated_boolvar(..) call as well!

bool_option( MCPL_ENABLE_RPATHMOD "Whether to try to set RPATH in installed binaries (if disabled all special RPATH handling is skipped)." "ON" )
bool_option( MCPL_ENABLE_CFGAPP    "Whether to build and install the ncrystal-config command" "ON" )

#if ( DEFINED MCPL_ENABLE_RPATHMOD )
#  message( FATAL_ERROR
#    "MCPL_ENABLE_RPATHMOD not supported: The mcpl-core"
#    " project no longer provides any binaries needing RPATH handling."
#  )
#endif()
if ( DEFINED MCPL_ENABLE_ZLIB )
  message( FATAL_ERROR
    "MCPL_ENABLE_ZLIB not supported: MCPL now always"
    " requires a preinstalled zlib that CMake can locate."
  )
endif()
if ( DEFINED MCPL_BUILD_FATBINARIES )
  message( FATAL_ERROR
    "MCPL_ENABLE_PYTHON not supported: The mcpl-core"
    " project no longer contains any python code."
  )
endif()
if ( DEFINED MCPL_ENABLE_EXAMPLES )
  message( FATAL_ERROR
    "MCPL_ENABLE_EXAMPLES not supported: code examples"
    " are now maintained outside of the main project."
  )
endif()
if ( DEFINED MCPL_BUILD_FATBINARIES )
  message( FATAL_ERROR
    "MCPL_BUILD_FATBINARIES not supported: The MCPL project"
    " no longer provides code for fat binaries."
  )
endif()
if ( DEFINED MCPL_ENABLE_GEANT4 )
  message( FATAL_ERROR
    "MCPL_ENABLE_GEANT4 not supported: The MCPL-Geant4"
    " bindings are now provided in a standalone project."
  )
endif()
if ( DEFINED MCPL_ENABLE_PHITS )
  message( FATAL_ERROR
    "MCPL_ENABLE_GEANT4 not supported: The MCPL-Geant4"
    " bindings are now provided in a standalone project."
  )
endif()
if ( DEFINED MCPL_ENABLE_SSW )
  message( FATAL_ERROR
    "MCPL_ENABLE_GEANT4 not supported: The MCPL-Geant4"
    " bindings are now provided in a standalone project."
  )
endif()
