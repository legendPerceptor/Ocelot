#!/bin/bash
export COMPRESSOR_DIR=/home/yuanjian/Development/playground/compressors
export INSTALL_DIR=/home/yuanjian/Development/playground/compressors/executables

mkdir -p $COMPRESSOR_DIR
mkdir -p $INSTALL_DIR

bash ./install_sz_region.sh
# bash ./install_sz3.sh