#!bin/sh
git clone https://github.com/ccache/ccache.git
cd ccache
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=Release ..
make
make install
cd ..
cd ..
rm -r ccache