include_guard()

include( mcpl_utils )

#Variables. Note that if changing the default value of a variable with a
#corresponding deprecated variable below, the default value should be modified
#in the add_deprecated_boolvar(..) call as well!

enum_option( MCPL_ENABLE_ZLIB "Whether to enable zlib support" IFAVAILABLE FETCH USEPREINSTALLED ALWAYS OFF NEVER )
option( MCPL_ENABLE_EXAMPLES  "Whether to build and install various examples." OFF )
option( MCPL_ENABLE_SSW  "Whether to build and install the MCPL-SSW converters (for MCNP)." ON )
option( MCPL_ENABLE_PHITS  "Whether to build and install the MCPL-PHITS converters." ON )
option( MCPL_ENABLE_GEANT4  "Whether to build and install Geant4 plugins." OFF )
option( MCPL_ENABLE_FATBINARIES  "Whether to also build the fat binaries." OFF )
option( MCPL_ENABLE_PYTHON  "Whether to also install python files." ON )
option( MCPL_ENABLE_RPATHMOD "Whether to try to set RPATH in installed binaries (if disabled all special RPATH handling is skipped)." ON )

#Note that the code supports several "hidden" options which are only intended for experts
#(MCPL_NOTOUCH_CMAKE_BUILD_TYPE, MCPL_DISABLE_CXX, MCPL_ENABLE_CPACK, ...).

#Older deprecated variables:
add_deprecated_boolvar( BUILD_WITHZLIB "Whether to enable zlib support" MCPL_ENABLE_ZLIB IFAVAILABLE IFAVAILABLE NEVER )
add_deprecated_boolvar( BUILD_EXAMPLES "Whether to build examples." MCPL_ENABLE_EXAMPLES OFF ON OFF )
add_deprecated_boolvar( BUILD_WITHSSW "Whether to build and install the MCPL-SSW converters." MCPL_ENABLE_SSW ON ON OFF )
add_deprecated_boolvar( BUILD_WITHPHITS "Whether to build and install the MCPL-PHITS converters." MCPL_ENABLE_PHITS ON ON OFF )
add_deprecated_boolvar( BUILD_WITHG4 "Whether to build Geant4 plugins." MCPL_ENABLE_GEANT4 OFF ON OFF )
add_deprecated_boolvar( BUILD_FAT "Whether to also build the fat binaries." MCPL_ENABLE_FATBINARIES OFF ON OFF )
add_deprecated_boolvar( INSTALL_PY "Whether to also install python files." MCPL_ENABLE_PYTHON ON ON OFF )
add_deprecated_boolvar( MODIFY_RPATH  "Whether to try to set RPATH in installed binaries (if disabled all special RPATH handling is skipped)." MCPL_ENABLE_RPATHMOD ON ON OFF )
