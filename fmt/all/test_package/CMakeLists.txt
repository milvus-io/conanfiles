cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(fmt REQUIRED CONFIG)

# Determine which target to use based on what's available
if(TARGET fmt::fmt-header-only)
    set(FMT_TARGET fmt::fmt-header-only)
elseif(TARGET fmt::fmt)
    set(FMT_TARGET fmt::fmt)
else()
    message(FATAL_ERROR "Neither fmt::fmt nor fmt::fmt-header-only target found")
endif()

add_executable(test_package test_package.cpp)
target_compile_features(test_package PRIVATE cxx_std_14)
target_link_libraries(test_package PRIVATE ${FMT_TARGET})

add_executable(test_ranges test_ranges.cpp)
target_compile_features(test_ranges PRIVATE cxx_std_14)
target_link_libraries(test_ranges PRIVATE ${FMT_TARGET})
