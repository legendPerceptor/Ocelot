#!/bin/bash
cd $COMPRESSOR_DIR
gdown https://drive.google.com/uc?id=1YppGgdlhMJysjOPxl0KFvgbTjeiTd3ku
tar -xf ./fastqZip.tar.xz
cd fastqZip
./build.sh
cp build/fastqZip $INSTALL_DIR/fastqZip
