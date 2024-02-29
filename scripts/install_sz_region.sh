#!/bin/bash
cd $COMPRESSOR_DIR
git clone https://github.com/legendPerceptor/SZ3.git SZ_REGION
cd SZ_REGION && git checkout region
git submodule update --init --recursive
cd tools/zstd-1.4.5/lib && make libzstd && cd ../../..
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX:PATH=$INSTALL_DIR ..
cmake --build . --target sz_region
cp test/sz_region $INSTALL_DIR/sz_region

