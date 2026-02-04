cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(milvus-sdk-cpp REQUIRED CONFIG)

add_executable(test_package test_package.cpp)
target_link_libraries(test_package milvus-sdk-cpp::milvus-sdk-cpp)
