cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(bson-1.0 REQUIRED CONFIG)

add_executable(test_package test_package.c)
# libbson::libbson is an alias exposed for both shared and static builds.
target_link_libraries(test_package PRIVATE libbson::libbson)
