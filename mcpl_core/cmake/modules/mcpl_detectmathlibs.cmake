
include_guard()

function( detect_math_libs )
  #Make sure we link in math functions correctly (typically the linker needs
  #libm on unix, but nothing on Windows). Sets MCPL_MATH_LIBRARIES in calling
  #scope unless already defined.
  if ( DEFINED MCPL_MATH_LIBRARIES )
    return()
  endif()
  set( result "" )
  set(TMP_TESTLIBMSRC
    "#include <math.h>\nint main(int argc,char** argv) { (void)argv;double a=(exp)(argc+1.0); return (int)(a*0.1); }\n")
  set(TMP_TESTDIR ${PROJECT_BINARY_DIR}/test_libm)
  file(WRITE ${TMP_TESTDIR}/test.c "${TMP_TESTLIBMSRC}")
  try_compile(ALWAYS_HAS_MATH "${TMP_TESTDIR}" "${TMP_TESTDIR}/test.c")
  if (NOT ALWAYS_HAS_MATH)
    set(TMP_TESTDIR ${PROJECT_BINARY_DIR}/test_libm2)
    file(WRITE ${TMP_TESTDIR}/test.c "${TMP_TESTLIBMSRC}")
    try_compile(MATH_NEEDS_LIBM "${TMP_TESTDIR}" "${TMP_TESTDIR}/test.c" LINK_LIBRARIES m)
    if (MATH_NEEDS_LIBM)
      set( result "m" )
    else()
      message( FATAL_ERROR "Could not figure out link flags needed to enable math functions" )
    endif()
  endif()
  set( "MCPL_MATH_LIBRARIES" "${result}" PARENT_SCOPE )
endfunction()
