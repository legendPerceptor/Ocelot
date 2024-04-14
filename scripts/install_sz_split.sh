#!/bin/bash
cd $COMPRESSOR_DIR
wget https://github.com/legendPerceptor/\
SZ3/archive/refs/tags/0.1.1.tar.gz
tar -xzvf 0.1.1.tar.gz
cd SZ3-0.1.1/
mkdir build && cd build
cmake -DCMAKE_CXX_COMPILER=mpic++ -DCMAKE_C_COMPILER=mpicc .. && cmake --build .
cp tools/sz3-split/sz3_split $INSTALL_DIR/sz3_split
cp tools/sz3/sz3 $INSTALL_DIR/sz3