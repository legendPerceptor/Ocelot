#!/bin/bash
cd $COMPRESSOR_DIR
git clone https://github.com/legendPerceptor/SZ3.git
cd SZ3 && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX:PATH=$INSTALL_DIR ..
cmake --build .
make install
