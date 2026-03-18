cmake_minimum_required(VERSION 3.15)
project(cmake_wrapper LANGUAGES C)

# We want to discover the crypto library through CMakeDeps and create a `crypto`
# target for linking. s2n's CMakeLists.txt expects a `crypto` target when
# SEARCH_LIBCRYPTO=OFF.
#
# Two modes:
# 1. OpenSSL (default): find_package(OpenSSL) -> create `crypto` alias
# 2. aws-lc (FIPS): find_package(crypto) -> aws-lc provides AWS::crypto target
#    S2N_INTERN_LIBCRYPTO handles symbol prefixing to avoid conflicts with
#    system OpenSSL used by other components (Arrow, gRPC, libcurl).
#    crypto_STATIC_LIBRARY and crypto_INCLUDE_DIR are set by CMakeToolchain
#    from the Conan generate() step.

if (S2N_INTERN_LIBCRYPTO)
    # aws-lc mode: CMakeDeps generates crypto-config.cmake from aws-lc recipe.
    # crypto_STATIC_LIBRARY and crypto_INCLUDE_DIR are already set via
    # CMakeToolchain variables from the s2n conanfile.py generate() method.
    find_package(crypto REQUIRED)
    if (NOT TARGET crypto)
        add_library(crypto INTERFACE IMPORTED)
        if (TARGET AWS::crypto)
            set_target_properties(crypto PROPERTIES INTERFACE_LINK_LIBRARIES "AWS::crypto")
        elseif (TARGET aws-lc::crypto)
            set_target_properties(crypto PROPERTIES INTERFACE_LINK_LIBRARIES "aws-lc::crypto")
        endif()
    endif()
else()
    # OpenSSL mode (original behavior)
    # https://github.com/aws/s2n-tls/blob/v1.3.31/CMakeLists.txt#L27-L28
    # https://github.com/aws/s2n-tls/blob/v1.3.31/CMakeLists.txt#L379-L381
    find_package(OpenSSL REQUIRED)
    add_library(crypto INTERFACE IMPORTED)
    set_target_properties(crypto PROPERTIES INTERFACE_LINK_LIBRARIES "OpenSSL::Crypto")
endif()

add_subdirectory(src)
