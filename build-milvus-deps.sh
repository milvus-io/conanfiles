#!/bin/bash
set -e

# Build all Milvus dependencies from this conanfiles repo
# Uses the same conan create pattern from .github/workflows/build-and-push.yml
#
# Reference: https://github.com/milvus-io/milvus/blob/master/internal/core/conanfile.py
#
# APPROACH: Build ALL required versions of each package into the local Conan cache.
# Each `conan create` builds independently, so multiple versions coexist.
#
#
# TODO: MISSING RECIPES - These versions need to be added to the repo:
#   - prometheus-cpp/1.2.4 (recipe only has up to 1.1.0)
#   - libavrocpp/1.12.1.1 (recipe only has 1.12.1)
#   - openssl/3.3.2 (recipe only has up to 3.2.1)
#   - libcurl/8.10.1 (recipe only has up to 8.8.0)
#
# Conancenter-only packages (NOT built here, install separately):
#   - google-cloud-cpp/2.28.0
#   - roaring/3.0.0
#   - simde/0.8.2
#   - xxhash/0.8.3
#   - unordered_dense/4.4.0
#   - icu/74.2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Common conan settings (from build-and-push.yml)
CONAN_SETTINGS="-s compiler=gcc -s compiler.version=11 -s compiler.libcxx=libstdc++11 -s compiler.cppstd=17 -s build_type=Release"

# Use 6 parallel jobs for building
CONAN_JOBS="-c tools.build:jobs=6"

# CMake 4.x compatibility: Allow older cmake_minimum_required versions
# This is needed because CMake 4.x dropped support for CMake < 3.5
export CMAKE_POLICY_VERSION_MINIMUM=3.5

# ============================================================================
# Step 1: Check Conan setup
# ============================================================================
echo "=============================================="
echo "Step 1: Checking Conan setup"
echo "=============================================="

conan --version

# Only run profile detect if no default profile exists
if ! conan profile show &>/dev/null; then
    echo "No default profile found, detecting..."
    conan profile detect
else
    echo "Default profile already exists, skipping profile detect"
fi

echo ""
echo "Current remotes:"
conan remote list

# ============================================================================
# Step 2: Build packages using conan create
# ============================================================================
echo ""
echo "=============================================="
echo "Step 2: Building packages with conan create"
echo "=============================================="

# Function to build a package
# Usage: build_package <recipe_path> <version> [options] [user/channel]
# If user/channel is provided (e.g. "milvus/dev"), adds --user and --channel flags
build_package() {
    local package_path=$1
    local version=$2
    local options=${3:-""}
    local user_channel=${4:-""}

    local user_flags=""
    if [ -n "$user_channel" ]; then
        local user="${user_channel%%/*}"
        local channel="${user_channel#*/}"
        user_flags="--user=$user --channel=$channel"
    fi

    echo ""
    echo "----------------------------------------------"
    echo "Building: $package_path --version=$version ${user_channel:+@$user_channel}"
    echo "----------------------------------------------"

    conan create "$package_path" \
        --version="$version" \
        --build=missing \
        $CONAN_SETTINGS \
        $CONAN_JOBS \
        $user_flags \
        $options
}

# Function to build a package, skipping test_package
build_package_no_test() {
    local package_path=$1
    local version=$2
    local options=${3:-""}
    local user_channel=${4:-""}

    local user_flags=""
    if [ -n "$user_channel" ]; then
        local user="${user_channel%%/*}"
        local channel="${user_channel#*/}"
        user_flags="--user=$user --channel=$channel"
    fi

    echo ""
    echo "----------------------------------------------"
    echo "Building (no test): $package_path --version=$version ${user_channel:+@$user_channel}"
    echo "----------------------------------------------"

    conan create "$package_path" \
        --version="$version" \
        --build=missing \
        -tf="" \
        $CONAN_SETTINGS \
        $CONAN_JOBS \
        $user_flags \
        $options
}

# ============================================================================
# PHASE 1: Foundation - No Dependencies (Leaf Packages)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 1: Foundation packages (no dependencies)"
echo "=============================================="

# Compression libraries (Milvus version)
build_package "zlib/all/conanfile.py" "1.3.1"
build_package "bzip2/all/conanfile.py" "1.0.8"
build_package "lz4/all/conanfile.py" "1.9.4"
build_package "snappy/all/conanfile.py" "1.2.1"
build_package "zstd/all/conanfile.py" "1.5.5"

# Core utilities (Milvus versions)
build_package "gflags/all/conanfile.py" "2.2.2" "-o gflags/*:shared=True"
build_package "double-conversion/all/conanfile.py" "3.3.0" "-o double-conversion/*:shared=True"
build_package "crc32c/all/conanfile.py" "1.1.2"

# Header-only / Simple packages (Milvus versions)
build_package "nlohmann_json/all/conanfile.py" "3.11.3"
build_package "rapidjson/all/conanfile.py" "cci.20230929"
build_package "xsimd/all/conanfile.py" "9.0.1"
build_package "fmt/all/conanfile.py" "11.0.2" "-o fmt/*:header_only=False"
build_package "yaml-cpp/all/conanfile.py" "0.7.0"
build_package "marisa/all/conanfile.py" "0.2.6"
build_package "geos/all/conanfile.py" "3.12.0"

# Testing frameworks
build_package "gtest/all/conanfile.py" "1.13.0" "-o gtest/*:build_gmock=True"

# Build tools
build_package "ninja/all/conanfile.py" "1.11.1"
build_package "m4/all/conanfile.py" "1.4.19"
build_package "cmake/binary/conanfile.py" "3.31.11"

# AWS foundation
build_package "aws-c-common/all/conanfile.py" "0.9.6"

# OpenTelemetry proto
build_package "opentelemetry-proto/all/conanfile.py" "1.7.0"    # opentelemetry-cpp/1.23.0

# ============================================================================
# PHASE 2: Basic Dependencies (Level 1)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 2: Basic dependencies (Level 1)"
echo "=============================================="

# xz_utils (Milvus version, shared=True)
build_package "xz_utils/all/conanfile.py" "5.4.5" "-o xz_utils/*:shared=True"

# openssl depends on zlib
# TODO: openssl/3.3.2 recipe is missing (max is 3.2.1), using 3.2.1 as placeholder
build_package "openssl/3.x.x/conanfile.py" "3.2.1" "-o openssl/*:shared=False -o openssl/*:no_apps=True"

# c-ares (minimal deps)
build_package "c-ares/all/conanfile.py" "1.19.1"

# abseil (Milvus version, needed before protobuf/5.27.0)
build_package "abseil/all/conanfile.py" "20250127.0"

# protobuf depends on zlib, abseil (Milvus version)
build_package "protobuf/all/conanfile.py" "5.27.0" "-o protobuf/*:shared=True" "milvus/dev"

# libunwind depends on xz_utils, zlib (Milvus version)
build_package "libunwind/all/conanfile.py" "1.8.1"

# libevent depends on openssl (now a direct Milvus dep)
build_package "libevent/all/conanfile.py" "2.1.12" "-o libevent/*:shared=True"

# libsodium (Milvus version, also used by folly)
build_package "libsodium/all/conanfile.py" "cci.20220430"

# re2 (minimal deps for this version)
build_package "re2/all/conanfile.py" "20230301"

# glog depends on gflags, libunwind (Milvus version)
build_package "glog/all/conanfile.py" "0.7.1" "-o glog/*:with_gflags=True -o glog/*:shared=True"

# benchmark depends on cmake
build_package "benchmark/all/conanfile.py" "1.7.0"

# s2n depends on openssl
build_package "s2n/all/conanfile.py" "1.3.55"

# AWS Level 1: depend on aws-c-common
build_package "aws-checksums/all/conanfile.py" "0.1.17"
build_package "aws-c-cal/all/conanfile.py" "0.6.9"
build_package "aws-c-compression/all/conanfile.py" "0.2.17"
build_package "aws-c-sdkutils/all/conanfile.py" "0.1.12"

# Build tools Level 1
build_package "flex/all/conanfile.py" "2.6.4"
build_package "autoconf/all/conanfile.py" "2.71"

# Folly dependencies (needed in Phase 7)
build_package "libiberty/all/conanfile.py" "9.1.0"

# ============================================================================
# PHASE 3: Intermediate Dependencies (Level 2)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 3: Intermediate dependencies (Level 2)"
echo "=============================================="

# automake depends on autoconf
build_package "automake/all/conanfile.py" "1.16.5"

# meson depends on ninja
build_package "meson/all/conanfile.py" "1.2.2"

# boost depends on zlib, bzip2, xz_utils, zstd (Milvus version, also used by folly)
build_package "boost/all/conanfile.py" "1.83.0" "-o boost/*:without_locale=False -o boost/*:without_test=True"

# onetbb (Milvus version)
build_package "onetbb/all/conanfile.py" "2021.9.0" "-o onetbb/*:tbbmalloc=False -o onetbb/*:tbbproxy=False"

# jemalloc depends on automake
build_package "jemalloc/all/conanfile.py" "5.3.0"

# googleapis depends on protobuf
build_package "googleapis/all/conanfile.py" "cci.20221108"

# AWS Level 2: aws-c-io depends on aws-c-cal, aws-c-common, s2n
build_package "aws-c-io/all/conanfile.py" "0.13.35"

# prometheus-cpp depends on zlib (with_pull=False avoids libcurl dep)
# TODO: prometheus-cpp/1.2.4 recipe is missing (max is 1.1.0)
# Using 1.1.0 as placeholder (also needed by opentelemetry-cpp/1.23.0 recipe)
build_package_no_test "prometheus-cpp/all/conanfile.py" "1.1.0" "-o prometheus-cpp/*:with_pull=False"

# libdwarf (needed by folly)
build_package "libdwarf/all/conanfile.py" "20191104"

# ============================================================================
# PHASE 4: Complex Libraries (Level 3)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 4: Complex libraries (Level 3)"
echo "=============================================="

# libtool depends on automake
build_package "libtool/all/conanfile.py" "2.4.7"

# bison depends on m4, automake, flex
build_package "bison/all/conanfile.py" "3.8.2"

# grpc depends on protobuf/5.27.0@milvus/dev, c-ares, openssl, re2, zlib, abseil/20250127.0
build_package "grpc/all/conanfile.py" "1.67.1" "" "milvus/dev"

# librdkafka depends on lz4, zlib, zstd, openssl, cyrus-sasl
build_package "librdkafka/all/conanfile.py" "1.9.1" \
    "-o librdkafka/*:shared=True -o librdkafka/*:zstd=True -o librdkafka/*:ssl=True -o librdkafka/*:sasl=True"

# AWS Level 3: aws-c-http depends on aws-c-io, aws-c-compression
build_package "aws-c-http/all/conanfile.py" "0.7.14"

# libcurl depends on openssl, zlib
# TODO: libcurl/8.10.1 recipe is missing (max is 8.8.0)
# Using 8.8.0 as placeholder for Milvus
build_package "libcurl/all/conanfile.py" "8.8.0"

# ============================================================================
# PHASE 5: High-Level Libraries (Level 4)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 5: High-level libraries (Level 4)"
echo "=============================================="

# AWS Level 4: depend on aws-c-http, aws-c-io
build_package "aws-c-auth/all/conanfile.py" "0.7.8"
build_package "aws-c-mqtt/all/conanfile.py" "0.9.10"

# thrift depends on boost, openssl, zlib, libevent, flex, bison
build_package "thrift/all/conanfile.py" "0.17.0"

# azure-sdk-for-cpp depends on openssl, libcurl, libxml2
build_package "azure-sdk-for-cpp/all/conanfile.py" "1.11.3" "" "milvus/dev"

# ============================================================================
# PHASE 6: AWS SDK (Level 5-6)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 6: AWS SDK chain (Level 5-6)"
echo "=============================================="

# AWS Level 5: depend on aws-c-auth, aws-c-http, aws-c-io
build_package "aws-c-event-stream/all/conanfile.py" "0.3.1"
build_package "aws-c-s3/all/conanfile.py" "0.3.24"

# AWS Level 6: aws-crt-cpp depends on most aws-c-* packages
build_package "aws-crt-cpp/all/conanfile.py" "0.24.1"

# AWS Level 7: aws-sdk-cpp
build_package "aws-sdk-cpp/all/conanfile.py" "1.11.692" \
    "-o aws-sdk-cpp/*:s3-crt=True -o aws-sdk-cpp/*:text-to-speech=False -o aws-sdk-cpp/*:transfer=False" \
    "milvus/dev"

# ============================================================================
# PHASE 7: Application Libraries (Level 5+)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 7: Application libraries"
echo "=============================================="

# opentelemetry-cpp/1.23.0 depends on abseil/20250127.0, protobuf/5.27.0@milvus/dev,
#   grpc/1.67.1@milvus/dev, opentelemetry-proto/1.7.0, nlohmann_json, prometheus-cpp
build_package_no_test "opentelemetry-cpp/all/conanfile.py" "1.23.0" \
    "-o opentelemetry-cpp/*:with_stl=True" "milvus/dev"

# folly depends on boost, bzip2, double-conversion, gflags, glog, libevent,
#   openssl, lz4, snappy, zlib, zstd, libsodium, xz_utils, libunwind, fmt,
#   libiberty, libdwarf
build_package_no_test "folly/2024.x/conanfile.py" "2024.08.12.00" "-o folly/*:shared=True" "milvus/dev"

# rocksdb depends on gflags, snappy, lz4, zlib, zstd, onetbb, jemalloc
build_package "rocksdb/all/conanfile.py" "6.29.5" \
    "-o rocksdb/*:shared=True -o rocksdb/*:with_zstd=True" "milvus/dev"

# libavrocpp depends on boost, snappy, fmt, zlib
# TODO: libavrocpp/1.12.1.1 recipe is missing (only has 1.12.1)
# Using 1.12.1 as placeholder
build_package "libavrocpp/all/conanfile.py" "1.12.1" "" "milvus/dev"

# ============================================================================
# PHASE 8: Final - Arrow (Most Complex)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 8: Arrow (final, most dependencies)"
echo "=============================================="

# arrow depends on: thrift, protobuf, jemalloc, boost, gflags, glog, grpc,
#                   rapidjson, openssl, aws-sdk-cpp (with_s3),
#                   azure-sdk-for-cpp (with_azure),
#                   bzip2, lz4, snappy, xsimd, zstd, re2
build_package "arrow/all/conanfile.py" "17.0.0" \
    "-o arrow/*:filesystem_layer=True \
     -o arrow/*:parquet=True \
     -o arrow/*:compute=True \
     -o arrow/*:with_re2=True \
     -o arrow/*:with_zstd=True \
     -o arrow/*:with_boost=True \
     -o arrow/*:with_thrift=True \
     -o arrow/*:with_jemalloc=True \
     -o arrow/*:with_openssl=True \
     -o arrow/*:shared=False \
     -o arrow/*:with_azure=True \
     -o arrow/*:with_s3=True \
     -o arrow/*:encryption=True \
     -o aws-sdk-cpp/*:config=True \
     -o aws-sdk-cpp/*:text-to-speech=False \
     -o aws-sdk-cpp/*:transfer=False \
     -o aws-sdk-cpp/*:s3-crt=True" "milvus/dev-2.6"

# ============================================================================
# Step 3: List all built packages
# ============================================================================
echo ""
echo "=============================================="
echo "Step 3: Listing all built packages"
echo "=============================================="
conan list '*:*'

# ============================================================================
# Step 4: Summary
# ============================================================================
echo ""
echo "=============================================="
echo "Build complete!"
echo "=============================================="
echo ""
echo "Packages built with @milvus channels:"
echo "  - protobuf/5.27.0@milvus/dev"
echo "  - grpc/1.67.1@milvus/dev"
echo "  - opentelemetry-cpp/1.23.0@milvus/dev"
echo "  - folly/2024.08.12.00@milvus/dev"
echo "  - rocksdb/6.29.5@milvus/dev"
echo "  - libavrocpp/1.12.1@milvus/dev (TODO: update to 1.12.1.1)"
echo "  - aws-sdk-cpp/1.11.692@milvus/dev"
echo "  - azure-sdk-for-cpp/1.11.3@milvus/dev"
echo "  - arrow/17.0.0@milvus/dev-2.6"
echo ""
echo "Packages NOT built (from conancenter, install separately):"
echo "  - google-cloud-cpp/2.28.0"
echo "  - roaring/3.0.0"
echo "  - simde/0.8.2"
echo "  - xxhash/0.8.3"
echo "  - unordered_dense/4.4.0"
echo "  - icu/74.2"
echo ""
echo "TODO: Missing recipes that need to be added:"
echo "  - openssl/3.3.2 (currently using 3.2.1)"
echo "  - libcurl/8.10.1 (currently using 8.8.0)"
echo "  - prometheus-cpp/1.2.4 (currently using 1.1.0)"
echo "  - libavrocpp/1.12.1.1 (currently using 1.12.1)"
echo ""
echo "To upload packages to Artifactory, run:"
echo "  conan remote login default-conan-local2 <username> -p <password>"
echo "  conan upload '*' -r default-conan-local2 -c"
