
# Tests which can be run when only mcpl_core is built, and which is even OK
# to use before an installation step (this is not the case with the tests in
# <reporoot>/tests).

include_guard()

function( mcpl_core_setup_tests )
#  set_source_files_properties(
#    "${Project_SOURCE_DIR}/app_test/main.cc"
#    PROPERTIES LANGUAGE CXX
#  )
  add_executable( "testapp_testwritegzip" "${PROJECT_SOURCE_DIR}/tests/src/app_testwritegzip/main.c" )
  target_link_libraries( "testapp_testwritegzip" PRIVATE MCPL::MCPL )
  add_test( NAME "testapp_testwritegzip" COMMAND "testapp_testwritegzip" )
  set_property( TEST "testapp_testwritegzip" PROPERTY TIMEOUT "$<IF:$<CONFIG:Debug>,20,7>" )
endfunction()

mcpl_core_setup_tests()
