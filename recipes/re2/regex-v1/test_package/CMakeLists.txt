cmake_minimum_required(VERSION 3.15)
project(re2_required_literals_consumer LANGUAGES CXX)

find_package(re2 REQUIRED CONFIG)
find_package(Threads REQUIRED)

add_executable(test_package test_package.cpp)
target_compile_features(test_package PRIVATE cxx_std_11)
target_link_libraries(test_package PRIVATE re2::re2 Threads::Threads)
