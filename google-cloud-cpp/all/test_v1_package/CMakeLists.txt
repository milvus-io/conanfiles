cmake_minimum_required(VERSION 3.10...3.24)
project(google-cloud-cpp-test LANGUAGES CXX)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../test_package/
                 ${CMAKE_CURRENT_BINARY_DIR}/test_package/)
