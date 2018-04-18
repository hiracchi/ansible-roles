#!/bin/bash

GTEST_SRC_DIR=/usr/src/gtest

cd ${GTEST_SRC_DIR}

if [ -d "${GTEST_SRC_DIR}/build" ]; then
    rm -rf "${GTEST_SRC_DIR}/build"
fi
mkdir -p "${GTEST_SRC_DIR}/build"

cd "${GTEST_SRC_DIR}/build"
cmake ..
make
cp *.a /usr/lib
