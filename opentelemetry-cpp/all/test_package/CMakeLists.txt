cmake_minimum_required(VERSION 3.8)

project(test_package CXX)

find_package(opentelemetry-cpp REQUIRED CONFIG)

set(CMAKE_CXX_STANDARD 17)

add_executable(${CMAKE_PROJECT_NAME} test_package.cpp)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE opentelemetry-cpp::opentelemetry-cpp)
