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
<<<<<<< HEAD
rm -r ccache
=======
rm -r ccache
>>>>>>> 0f615d6116f518e071f9ff37d57ff3accfc6d305
