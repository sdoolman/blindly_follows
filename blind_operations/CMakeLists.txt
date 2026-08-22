cmake_minimum_required(VERSION 3.14)
project(blind_operations CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(helib REQUIRED)

add_executable(bgv_binary_reduction BGV_binary_modulo_reduction.cpp)
target_link_libraries(bgv_binary_reduction PRIVATE helib::helib)
