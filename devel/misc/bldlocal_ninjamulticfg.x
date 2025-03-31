#!/usr/bin/env bash
SRCDIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
set -e
set -u
set -x
test -f "${SRCDIR}/CMakeLists.txt"
test -f "${SRCDIR}/mcpl_core/include/mcpl.h"

TGT="/tmp/${USER}/mcpl_bldlocalninja"
rm -rf "${TGT}/bld" "${TGT}/inst"
mkdir -p "${TGT}/bld" "${TGT}/inst"
cd "${TGT}/bld"

THE_BUILD_TYPE=Release
THE_OTHER_BUILD_TYPE=Debug
#THE_OTHER_BUILD_TYPE=

cmake \
    -G 'Ninja Multi-Config' \
    -S "${SRCDIR}" \
    -B "${TGT}/bld" \
    -DCMAKE_INSTALL_PREFIX="${TGT}/inst" \
    -DMCPL_BUILD_STRICT=ON \
    -DMCPL_ENABLE_TESTING=ON \
    "$@"

cmake --build "${TGT}/bld" --config "${THE_BUILD_TYPE}"
if [ "x${THE_OTHER_BUILD_TYPE}" != "x" ]; then
    cmake --build "${TGT}/bld" --config "${THE_OTHER_BUILD_TYPE}"
fi
echo "Build dir was: ${TGT}/bld"
# -R app_selfpath -VV
ctest --build-config  "${THE_BUILD_TYPE}"  --output-on-failure --test-output-size-failed 10000 --test-output-truncation middle
if [ "x${THE_OTHER_BUILD_TYPE}" != "x" ]; then
    ctest --build-config  "${THE_OTHER_BUILD_TYPE}"  --output-on-failure --test-output-size-failed 10000 --test-output-truncation middle
fi

#--verbose --extra-verbose
cmake --install "${TGT}/bld"
echo "Build dir was: ${TGT}/bld"
