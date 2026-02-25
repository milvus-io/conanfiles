cmake_minimum_required(VERSION 3.10...3.24)
project(google-cloud-cpp-test CXX)

find_package(google-cloud-cpp CONFIG REQUIRED)

foreach(component IN ITEMS "storage")
    add_executable("${component}" "${component}.cpp")
    target_compile_features("${component}" PRIVATE cxx_std_14)
    target_link_libraries("${component}" google-cloud-cpp::${component})
endforeach()
