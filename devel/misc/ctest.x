#!/usr/bin/env bash
set -e
set -u
set -x
SRCDIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
test -f "${SRCDIR}/CMakeLists.txt"
test -f "${SRCDIR}/mcpl_core/include/mcpl.h"

TGT="/tmp/${USER}/mcpl_bldlocal"
rm -rf "${TGT}/bld" "${TGT}/inst"
mkdir -p "${TGT}/bld" "${TGT}/inst"

THE_BUILD_TYPE=Release
cmake \
    -S "${SRCDIR}" \
    -B "${TGT}/bld" \
    -DCMAKE_BUILD_TYPE="${THE_BUILD_TYPE}" \
    -DCMAKE_INSTALL_PREFIX="${TGT}/inst" \
    -DMCPL_BUILD_STRICT=99 \
    -DMCPL_ENABLE_TESTING=ON
#    -DMCPL_ENABLE_ZLIB=FETCH \

#\
#    "$@"

cmake --build "${TGT}/bld" --config "${THE_BUILD_TYPE}"
echo "Build dir was: ${TGT}/bld"
ctest  --test-dir "${TGT}/bld" --build-config  "${THE_BUILD_TYPE}"  --output-on-failure --test-output-size-failed 10000 --test-output-truncation middle "$@"
cmake --install "${TGT}/bld"
echo "Build dir was: ${TGT}/bld"
