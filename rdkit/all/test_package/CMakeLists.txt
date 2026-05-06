cmake_minimum_required(VERSION 3.18)
project(test_package CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(rdkit REQUIRED)

add_executable(test_package test_package.cpp)
target_link_libraries(test_package rdkit::rdkit)
