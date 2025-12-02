cmake_minimum_required(VERSION 3.15)
project(test_package)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

# Set FMT_HEADER_ONLY for the test_package subdirectory
if(TARGET fmt::fmt-header-only)
    set(FMT_HEADER_ONLY TRUE)
else()
    set(FMT_HEADER_ONLY FALSE)
endif()

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../test_package/
                 ${CMAKE_CURRENT_BINARY_DIR}/test_package/)
