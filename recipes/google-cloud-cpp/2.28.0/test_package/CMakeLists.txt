cmake_minimum_required(VERSION 3.15)
project(google-cloud-cpp-test CXX)

find_package(google-cloud-cpp CONFIG REQUIRED)

add_executable(storage storage.cpp)
target_compile_features(storage PRIVATE cxx_std_14)
target_link_libraries(storage google-cloud-cpp::storage)
