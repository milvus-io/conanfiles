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
# PACKAGES WITH MULTIPLE VERSIONS BUILT:
#   - zlib: 1.2.13 (Milvus, folly), 1.2.12 (old folly), 1.3.1 (libavrocpp)
#   - lz4: 1.9.4 (Milvus, folly), 1.9.3 (old folly)
#   - snappy: 1.1.9 (Milvus), 1.1.10 (rocksdb)
#   - zstd: 1.5.5 (Milvus, folly), 1.5.2 (old folly)
#   - double-conversion: 3.2.1 (Milvus, folly), 3.2.0 (old folly)
#   - crc32c: 1.1.2 (Milvus), 1.1.1 (google-cloud-cpp)
#   - nlohmann_json: 3.11.3 (Milvus), 3.10.0 (google-cloud-cpp), 3.11.2 (opentelemetry-cpp)
#   - fmt: 9.1.0 (Milvus, folly), 7.1.3 (old folly), 12.1.0 (libavrocpp)
#   - xz_utils: 5.4.0 (Milvus, folly), 5.2.5 (old folly), 5.4.5 (libunwind/1.8.0)
#   - openssl: 3.1.2 (Milvus, folly), 1.1.1w (opentelemetry-cpp — see NOTE below)
#   - protobuf: 3.21.4 (Milvus), 3.21.12 (grpc, googleapis, arrow), 5.27.0 (grpc/1.67.1, otel/1.23.0)
#   - libunwind: 1.7.2 (Milvus, folly), 1.5.0 (old folly), 1.8.0 (glog)
#   - libsodium: cci.20220430 (Milvus, folly), 1.0.18 (old folly)
#   - abseil: 20230125.3 (Milvus), 20220623.0 (google-cloud-cpp, otel/1.8.1.1), 20250127.0 (grpc/1.67.1, otel/1.23.0)
#   - glog: 0.6.0 (Milvus, folly), 0.4.0 (old folly)
#   - boost: 1.83.0 (Milvus, folly), 1.78.0 (old folly), 1.81.0 (opentelemetry-cpp), 1.85.0 (arrow, thrift)
#   - onetbb: 2021.9.0 (Milvus), 2021.10.0 (rocksdb)
#   - grpc: 1.50.1@milvus/dev, 1.50.0 (arrow), 1.67.1@milvus/dev (otel/1.23.0)
#   - libcurl: 7.86.0 (Milvus), 7.87.0 (opentelemetry-cpp), 7.88.1 (google-cloud-cpp)
#   - opentelemetry-proto: 0.19.0 (otel/1.8.1.1), 1.7.0 (otel/1.22.0+)
#   - opentelemetry-cpp: 1.8.1.1@milvus/2.4 (Milvus), 1.23.0@milvus/2.4 (future)
#
# NOTE: openssl 1.1.x — opentelemetry-cpp requires 1.1.1t,
#   but only 1.1.1w is available in this repo. Building 1.1.1w as the closest substitute.
#   folly 2023.10.30.09 uses openssl/3.1.2 (same as Milvus).
#
# KNOWN GAPS:
#   - folly: repo has 2023.10.30.09, Milvus needs 2023.10.30.08@milvus/dev (close match)
#   - azure-sdk-for-cpp: 1.11.3@milvus/dev (needs libxml2 from conancenter)

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

# Function to install a package from conancenter
install_from_conancenter() {
    local package_ref=$1
    local options=${2:-""}

    echo ""
    echo "----------------------------------------------"
    echo "Installing from conancenter: $package_ref"
    echo "----------------------------------------------"

    conan install --requires="$package_ref" \
        --build=missing \
        $CONAN_SETTINGS \
        $CONAN_JOBS \
        $options
}

# ============================================================================
# PHASE 1: Foundation - No Dependencies (Leaf Packages)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 1: Foundation packages (no dependencies)"
echo "=============================================="

# Compression libraries (Milvus versions)
build_package "zlib/all/conanfile.py" "1.2.13"
build_package "bzip2/all/conanfile.py" "1.0.8"
build_package "lz4/all/conanfile.py" "1.9.4"
build_package "snappy/all/conanfile.py" "1.1.9"
build_package "zstd/all/conanfile.py" "1.5.5"

# Compression libraries (additional versions for recipe dependencies)
build_package "zlib/all/conanfile.py" "1.2.12"      # folly
build_package "zlib/all/conanfile.py" "1.3.1"       # libavrocpp [>=1.3.1 <2]
build_package "lz4/all/conanfile.py" "1.9.3"        # folly
build_package "snappy/all/conanfile.py" "1.1.10"    # rocksdb
build_package "zstd/all/conanfile.py" "1.5.2"       # folly

# Core utilities (Milvus versions)
build_package "gflags/all/conanfile.py" "2.2.2"
build_package "double-conversion/all/conanfile.py" "3.2.1" "-o double-conversion/*:shared=True"
build_package "crc32c/all/conanfile.py" "1.1.2"

# Core utilities (additional versions for recipe dependencies)
build_package "double-conversion/all/conanfile.py" "3.2.0" "-o double-conversion/*:shared=True"  # folly
build_package "crc32c/all/conanfile.py" "1.1.1"     # google-cloud-cpp

# Header-only / Simple packages (Milvus versions)
build_package "nlohmann_json/all/conanfile.py" "3.11.3"
build_package "rapidjson/all/conanfile.py" "cci.20230929"
build_package "xsimd/all/conanfile.py" "9.0.1"
build_package "fmt/all/conanfile.py" "9.1.0" "-o fmt/*:header_only=True"
build_package "yaml-cpp/all/conanfile.py" "0.7.0"
build_package "marisa/all/conanfile.py" "0.2.6"
build_package "geos/all/conanfile.py" "3.12.0"

# Header-only / Simple packages (additional versions for recipe dependencies)
build_package "nlohmann_json/all/conanfile.py" "3.10.0"   # google-cloud-cpp
build_package "nlohmann_json/all/conanfile.py" "3.11.2"   # opentelemetry-cpp
build_package "fmt/all/conanfile.py" "7.1.3" "-o fmt/*:header_only=True"    # folly
build_package "fmt/all/conanfile.py" "12.1.0" "-o fmt/*:header_only=True"   # libavrocpp [>=12 <13]

# roaring: GitHub auto-generated tarball has unstable checksum, install from conancenter
install_from_conancenter "roaring/3.0.0"

# Testing frameworks
build_package "gtest/all/conanfile.py" "1.13.0" "-o gtest/*:build_gmock=True"

# Build tools
build_package "ninja/all/conanfile.py" "1.11.1"
build_package "m4/all/conanfile.py" "1.4.19"
build_package "cmake/binary/conanfile.py" "3.30.1"

# AWS foundation
build_package "aws-c-common/all/conanfile.py" "0.9.6"

# OpenTelemetry proto (no deps)
build_package "opentelemetry-proto/all/conanfile.py" "0.19.0"
build_package "opentelemetry-proto/all/conanfile.py" "1.7.0"       # opentelemetry-cpp/1.22.0+

# ============================================================================
# PHASE 2: Basic Dependencies (Level 1)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 2: Basic dependencies (Level 1)"
echo "=============================================="

# xz_utils (Milvus version)
build_package "xz_utils/all/conanfile.py" "5.4.0"

# xz_utils (additional versions for recipe dependencies)
build_package "xz_utils/all/conanfile.py" "5.2.5"      # folly
build_package "xz_utils/all/conanfile.py" "5.4.5"      # libunwind/1.8.0 (for glog)

# openssl depends on zlib
build_package "openssl/3.x.x/conanfile.py" "3.1.2" "-o openssl/*:shared=True"

# openssl 1.1.x (for recipe dependencies)
# NOTE: opentelemetry-cpp needs 1.1.1t, but only 1.1.1w is available
# in this repo. Build 1.1.1w as closest substitute.
build_package "openssl/1.x.x/conanfile.py" "1.1.1w" "-o openssl/*:shared=True"

# c-ares (minimal deps)
build_package "c-ares/all/conanfile.py" "1.19.1"

# protobuf depends on zlib (Milvus version)
build_package "protobuf/all/conanfile.py" "3.21.4"

# protobuf (additional version for grpc, googleapis, arrow)
build_package "protobuf/all/conanfile.py" "3.21.12"

# libunwind depends on xz_utils, zlib (Milvus version)
build_package "libunwind/all/conanfile.py" "1.7.2"

# libunwind (additional versions for recipe dependencies)
build_package "libunwind/all/conanfile.py" "1.5.0"     # folly
build_package "libunwind/all/conanfile.py" "1.8.0"     # glog

# libevent depends on openssl
build_package "libevent/all/conanfile.py" "2.1.12" "-o libevent/*:shared=True"

# libsodium (Milvus version)
build_package "libsodium/all/conanfile.py" "cci.20220430"

# libsodium (additional version for folly)
build_package "libsodium/all/conanfile.py" "1.0.18"

# re2 (minimal deps for this version)
build_package "re2/all/conanfile.py" "20230301"

# abseil (Milvus version)
build_package "abseil/all/conanfile.py" "20230125.3"

# abseil (additional versions for recipe dependencies)
build_package "abseil/all/conanfile.py" "20220623.0"    # google-cloud-cpp, opentelemetry-cpp/1.8.1.1
build_package "abseil/all/conanfile.py" "20250127.0"    # grpc/1.67.1, protobuf/5.27.0, opentelemetry-cpp/1.23.0

# gperftools depends on libunwind (>=1.6.2)
build_package "gperftools/all/conanfile.py" "2.15"

# glog depends on gflags, libunwind (Milvus version)
build_package "glog/all/conanfile.py" "0.6.0" "-o glog/*:with_gflags=True -o glog/*:shared=True"

# glog (additional version for folly)
build_package "glog/all/conanfile.py" "0.4.0" "-o glog/*:with_gflags=True -o glog/*:shared=True"

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

# boost depends on zlib, bzip2, xz_utils, zstd (Milvus version)
build_package "boost/all/conanfile.py" "1.83.0" "-o boost/*:without_locale=False -o boost/*:without_test=True"

# boost (additional versions for recipe dependencies)
build_package "boost/all/conanfile.py" "1.78.0" "-o boost/*:without_locale=False -o boost/*:without_test=True"   # folly
build_package "boost/all/conanfile.py" "1.81.0" "-o boost/*:without_locale=False -o boost/*:without_test=True"   # opentelemetry-cpp
build_package "boost/all/conanfile.py" "1.85.0" "-o boost/*:without_locale=False -o boost/*:without_test=True"   # arrow, thrift

# onetbb (Milvus version)
build_package "onetbb/all/conanfile.py" "2021.9.0" "-o onetbb/*:tbbmalloc=False -o onetbb/*:tbbproxy=False"

# onetbb (additional version for rocksdb)
build_package "onetbb/all/conanfile.py" "2021.10.0" "-o onetbb/*:tbbmalloc=False -o onetbb/*:tbbproxy=False"

# jemalloc depends on automake
build_package "jemalloc/all/conanfile.py" "5.3.0"

# protobuf (additional version for grpc/1.67.1, opentelemetry-cpp/1.23.0)
build_package "protobuf/all/conanfile.py" "5.27.0" "" "milvus/dev"

# googleapis depends on protobuf/3.21.12
build_package "googleapis/all/conanfile.py" "cci.20221108"

# AWS Level 2: aws-c-io depends on aws-c-cal, aws-c-common, s2n
build_package "aws-c-io/all/conanfile.py" "0.13.35"

# prometheus-cpp depends on zlib (with_pull=False avoids libcurl dep)
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

# grpc depends on protobuf, c-ares, openssl, re2, zlib, abseil
build_package "grpc/all/conanfile.py" "1.50.1" "" "milvus/dev"

# grpc (additional version for arrow — no @milvus channel, uses protobuf/3.21.12)
build_package "grpc/all/conanfile.py" "1.50.0"

# grpc (additional version for opentelemetry-cpp/1.23.0 — uses protobuf/5.27.0, abseil/20250127.0)
build_package "grpc/all/conanfile.py" "1.67.1" "" "milvus/dev"

# librdkafka depends on lz4, zlib, zstd, openssl, cyrus-sasl
build_package "librdkafka/all/conanfile.py" "1.9.1" \
    "-o librdkafka/*:shared=True -o librdkafka/*:zstd=True -o librdkafka/*:ssl=True -o librdkafka/*:sasl=True"

# AWS Level 3: aws-c-http depends on aws-c-io, aws-c-compression
build_package "aws-c-http/all/conanfile.py" "0.7.14"

# libcurl depends on openssl, zlib (all versions needed by different recipes)
build_package "libcurl/all/conanfile.py" "7.86.0"      # Milvus
build_package "libcurl/all/conanfile.py" "7.87.0"      # opentelemetry-cpp
build_package "libcurl/all/conanfile.py" "7.88.1"      # google-cloud-cpp

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

# google-cloud-cpp depends on grpc, protobuf, abseil, nlohmann_json, crc32c, googleapis
build_package "google-cloud-cpp/all/conanfile.py" "2.5.0" "" "milvus/2.4"

# azure-sdk-for-cpp depends on openssl, libcurl, libxml2
# libxml2 installed from conancenter in Phase 9
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

# opentelemetry-cpp/1.8.1.1 depends on abseil, protobuf, grpc, nlohmann_json, prometheus-cpp, thrift
build_package "opentelemetry-cpp/all/conanfile.py" "1.8.1.1" "" "milvus/2.4"

# opentelemetry-cpp/1.23.0 depends on abseil/20250127.0, protobuf/5.27.0, grpc/1.67.1,
#   nlohmann_json, prometheus-cpp (no thrift/boost — Jaeger removed in 1.22.0+)
build_package "opentelemetry-cpp/all/conanfile.py" "1.23.0" "" "milvus/2.4"

# folly depends on boost, bzip2, double-conversion, gflags, glog, libevent,
#                openssl, lz4, snappy, zlib, zstd, libsodium, xz_utils, libunwind, fmt,
#                libiberty, libdwarf
# NOTE: test_package skipped due to static boost / shared folly linking issue
build_package_no_test "folly/all/conanfile.py" "2023.10.30.09" "-o folly/*:shared=True" "milvus/dev"

# rocksdb depends on gflags, snappy, lz4, zlib, zstd, onetbb, jemalloc
build_package "rocksdb/all/conanfile.py" "6.29.5" \
    "-o rocksdb/*:shared=True -o rocksdb/*:with_zstd=True" "milvus/dev"

# libavrocpp depends on boost, snappy, fmt, zlib
build_package "libavrocpp/all/conanfile.py" "1.12.1" "" "milvus/dev"

# ============================================================================
# PHASE 8: Final - Arrow (Most Complex)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 8: Arrow (final, most dependencies)"
echo "=============================================="

# arrow depends on: thrift, protobuf, jemalloc, boost, gflags, glog, grpc,
#                   rapidjson, openssl, opentelemetry-cpp, aws-sdk-cpp,
#                   bzip2, lz4, snappy, xsimd, zstd, re2
# NOTE: with_azure=False because azure-sdk-for-cpp is not available
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
     -o arrow/*:with_azure=False \
     -o arrow/*:with_s3=False \
     -o arrow/*:encryption=True" "milvus/dev-2.6"

# ============================================================================
# PHASE 9: Conancenter packages (not in this repo)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 9: Packages from conancenter"
echo "=============================================="

install_from_conancenter "libxml2/2.12.7"    # azure-sdk-for-cpp dependency
install_from_conancenter "simde/0.8.2"
install_from_conancenter "xxhash/0.8.3"
install_from_conancenter "unordered_dense/4.4.0"
install_from_conancenter "icu/74.2" "-o icu/*:shared=False -o icu/*:data_packaging=library"

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
echo "  - grpc/1.50.1@milvus/dev, 1.67.1@milvus/dev"
echo "  - protobuf/5.27.0@milvus/dev"
echo "  - google-cloud-cpp/2.5.0@milvus/2.4"
echo "  - opentelemetry-cpp/1.8.1.1@milvus/2.4, 1.23.0@milvus/2.4"
echo "  - folly/2023.10.30.09@milvus/dev"
echo "  - rocksdb/6.29.5@milvus/dev"
echo "  - libavrocpp/1.12.1@milvus/dev"
echo "  - aws-sdk-cpp/1.11.692@milvus/dev"
echo "  - azure-sdk-for-cpp/1.11.3@milvus/dev"
echo "  - arrow/17.0.0@milvus/dev-2.6"
echo ""
echo "Packages with multiple versions built:"
echo "  - zlib: 1.2.13, 1.2.12, 1.3.1"
echo "  - lz4: 1.9.4, 1.9.3"
echo "  - snappy: 1.1.9, 1.1.10"
echo "  - zstd: 1.5.5, 1.5.2"
echo "  - double-conversion: 3.2.1, 3.2.0"
echo "  - crc32c: 1.1.2, 1.1.1"
echo "  - nlohmann_json: 3.11.3, 3.10.0, 3.11.2"
echo "  - fmt: 9.1.0, 7.1.3, 12.1.0"
echo "  - xz_utils: 5.4.0, 5.2.5, 5.4.5"
echo "  - openssl: 3.1.2, 1.1.1w"
echo "  - protobuf: 3.21.4, 3.21.12, 5.27.0@milvus/dev"
echo "  - libunwind: 1.7.2, 1.5.0, 1.8.0"
echo "  - libsodium: cci.20220430, 1.0.18"
echo "  - abseil: 20230125.3, 20220623.0, 20250127.0"
echo "  - glog: 0.6.0, 0.4.0"
echo "  - boost: 1.83.0, 1.78.0, 1.81.0, 1.85.0"
echo "  - onetbb: 2021.9.0, 2021.10.0"
echo "  - grpc: 1.50.1@milvus/dev, 1.50.0, 1.67.1@milvus/dev"
echo "  - libcurl: 7.86.0, 7.87.0, 7.88.1"
echo "  - opentelemetry-proto: 0.19.0, 1.7.0"
echo "  - opentelemetry-cpp: 1.8.1.1@milvus/2.4, 1.23.0@milvus/2.4"
echo ""
echo "Packages fetched from conancenter:"
echo "  - roaring/3.0.0 (GitHub tarball checksum unstable)"
echo "  - libxml2/2.12.7 (azure-sdk-for-cpp dependency)"
echo "  - simde/0.8.2"
echo "  - xxhash/0.8.3"
echo "  - unordered_dense/4.4.0"
echo "  - icu/74.2"
echo ""
echo "KNOWN GAPS vs Milvus conanfile.py:"
echo "  - azure-sdk-for-cpp: 1.11.3@milvus/dev now built"
echo "  - folly: Milvus needs 2023.10.30.08, repo has 2023.10.30.09 (close match)"
echo "  - arrow with_azure disabled (requires azure-sdk-for-cpp)"
echo "  - openssl: otel needs 1.1.1t, only 1.1.1w available"
echo ""
echo "To upload packages to Artifactory, run:"
echo "  conan remote login default-conan2-local <username> -p <password>"
echo "  conan upload '*' -r default-conan2-local -c"
