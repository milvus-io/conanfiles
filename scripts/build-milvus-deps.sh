#!/bin/bash
set -e

# Build all Milvus dependencies from this conanfiles repo and optionally upload
# recipes to default-conan-local2 artifactory.
#
# Usage:
#   ./scripts/build-milvus-deps.sh                # build only
#   ./scripts/build-milvus-deps.sh --upload       # build and upload recipes
#
# Uses the same conan create pattern from .github/workflows/build-and-push.yml
# To upload recipes, requires JFROG_USERNAME2 and JFROG_PASSWORD2 environment variables for authentication.
#
# Reference:
#   https://github.com/milvus-io/milvus/blob/master/internal/core/conanfile.py
#   https://github.com/zilliztech/milvus-common/blob/master/conanfile.py
#   https://github.com/milvus-io/milvus-storage/blob/main/cpp/conanfile.py
#   https://github.com/zilliztech/knowhere/blob/main/conanfile.py
#
# APPROACH: Build ALL required versions of each package into the local Conan cache.
# Each `conan create` builds independently, so multiple versions coexist.
#
#
# Recipes built by this script (56 packages):
#   zlib/1.3.1, bzip2/1.0.8, lz4/1.9.4, snappy/1.2.1, zstd/1.5.5,
#   gflags/2.2.2, double-conversion/3.3.0, crc32c/1.1.2,
#   nlohmann_json/3.11.3, rapidjson/cci.20230929, xsimd/9.0.1, fmt/11.0.2,
#   yaml-cpp/0.7.0, marisa/0.2.6, geos/3.12.0, roaring/3.0.0, xxhash/0.8.3, gtest/1.13.0,
#   ninja/1.11.1, m4/1.4.19, cmake/3.31.11, opentelemetry-proto/1.7.0,
#   xz_utils/5.4.5, c-ares/1.19.1, abseil/20250127.0,
#   protobuf/5.27.0@milvus/dev, libunwind/1.8.1, s2n/1.6.0, libevent/2.1.12,
#   libsodium/cci.20220430, re2/20230301, glog/0.7.1, benchmark/1.7.0,
#   flex/2.6.4, autoconf/2.71, libiberty/9.1.0,
#   automake/1.16.5, meson/1.2.2, boost/1.83.0, onetbb/2021.9.0,
#   jemalloc/5.3.0, googleapis/cci.20221108, libdwarf/20191104,
#   libtool/2.4.7, bison/3.8.2, grpc/1.67.1@milvus/dev, librdkafka/1.9.1,
#   thrift/0.17.0, azure-sdk-for-cpp/1.11.3@milvus/dev,
#   aws-sdk-cpp/1.11.692@milvus/dev,
#   opentelemetry-cpp/1.23.0@milvus/dev, folly/2024.08.12.00@milvus/dev,
#   google-cloud-cpp/2.28.0@milvus/dev, rocksdb/6.29.5@milvus/dev,
#   libavrocpp/1.12.1.1@milvus/dev, arrow/17.0.0@milvus/dev-2.6
#
# Installed from conancenter (not from this repo's recipes):
#   - openssl/3.3.2
#   - libcurl/8.10.1
#   - prometheus-cpp/1.2.4
#
# Transitive downloaded from conancenter (NOT built here, install separately):
#   - simde/0.8.2
#   - unordered_dense/4.4.0
#   - icu/74.2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Parse arguments
DO_UPLOAD=false
for arg in "$@"; do
    case "$arg" in
        --upload) DO_UPLOAD=true ;;
        *) echo "Unknown argument: $arg"; exit 1 ;;
    esac
done

REMOTE_NAME="default-conan-local2"
REMOTE_URL="https://milvus01.jfrog.io/artifactory/api/conan/default-conan-local2"

# Track all explicitly built package references for upload
BUILT_PACKAGES=()

# Common conan settings (from build-and-push.yml)
CONAN_SETTINGS="-s compiler=gcc -s compiler.version=11 -s compiler.libcxx=libstdc++11 -s compiler.cppstd=17 -s build_type=Release -s:b compiler.cppstd=17"

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
    local pkg_ref
    if [ -n "$user_channel" ]; then
        local user="${user_channel%%/*}"
        local channel="${user_channel#*/}"
        user_flags="--user=$user --channel=$channel"
    fi

    # Extract package name from recipe path (e.g. "recipes/zlib/all/conanfile.py" -> "zlib")
    local pkg_name
    # Strip leading "recipes/" prefix if present
    local stripped="${package_path#recipes/}"
    pkg_name="${stripped%%/*}"
    if [ -n "$user_channel" ]; then
        pkg_ref="${pkg_name}/${version}@${user_channel}"
    else
        pkg_ref="${pkg_name}/${version}"
    fi

    echo ""
    echo "----------------------------------------------"
    echo "Building: $pkg_ref"
    echo "----------------------------------------------"

    conan create "$package_path" \
        --version="$version" \
        --build=missing \
        $CONAN_SETTINGS \
        $CONAN_JOBS \
        $user_flags \
        $options

    BUILT_PACKAGES+=("$pkg_ref")
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

    # Extract package name from recipe path
    local pkg_name
    local stripped="${package_path#recipes/}"
    pkg_name="${stripped%%/*}"
    local pkg_ref
    if [ -n "$user_channel" ]; then
        pkg_ref="${pkg_name}/${version}@${user_channel}"
    else
        pkg_ref="${pkg_name}/${version}"
    fi

    echo ""
    echo "----------------------------------------------"
    echo "Building (no test): $pkg_ref"
    echo "----------------------------------------------"

    conan create "$package_path" \
        --version="$version" \
        --build=missing \
        -tf="" \
        $CONAN_SETTINGS \
        $CONAN_JOBS \
        $user_flags \
        $options

    BUILT_PACKAGES+=("$pkg_ref")
}

# ============================================================================
# PHASE 1: Foundation - No Dependencies (Leaf Packages)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 1: Foundation packages (no dependencies)"
echo "=============================================="

# Compression libraries (Milvus version)
build_package "recipes/zlib/all/conanfile.py" "1.3.1"
build_package "recipes/bzip2/all/conanfile.py" "1.0.8"
build_package "recipes/lz4/all/conanfile.py" "1.9.4"
build_package "recipes/snappy/all/conanfile.py" "1.2.1"
build_package "recipes/zstd/all/conanfile.py" "1.5.5"

# Core utilities (Milvus versions)
build_package "recipes/gflags/all/conanfile.py" "2.2.2" "-o gflags/*:shared=True"
build_package "recipes/double-conversion/all/conanfile.py" "3.3.0" "-o double-conversion/*:shared=True"
build_package "recipes/crc32c/all/conanfile.py" "1.1.2"

# Header-only / Simple packages (Milvus versions)
build_package "recipes/nlohmann_json/all/conanfile.py" "3.11.3"
build_package "recipes/rapidjson/all/conanfile.py" "cci.20230929"
build_package "recipes/xsimd/all/conanfile.py" "9.0.1"
build_package "recipes/fmt/all/conanfile.py" "11.0.2" "-o fmt/*:header_only=False"
build_package "recipes/yaml-cpp/all/conanfile.py" "0.7.0"
build_package "recipes/marisa/all/conanfile.py" "0.2.6"
build_package "recipes/geos/all/conanfile.py" "3.12.0"
build_package "recipes/roaring/all/conanfile.py" "3.0.0"
build_package "recipes/xxhash/all/conanfile.py" "0.8.3"

# Testing frameworks
build_package "recipes/gtest/all/conanfile.py" "1.13.0" "-o gtest/*:build_gmock=True"

# Build tools
build_package "recipes/ninja/all/conanfile.py" "1.11.1"
build_package "recipes/m4/all/conanfile.py" "1.4.19"
build_package "recipes/cmake/binary/conanfile.py" "3.31.11"

# OpenTelemetry proto
build_package "recipes/opentelemetry-proto/all/conanfile.py" "1.7.0"    # opentelemetry-cpp/1.23.0

# ============================================================================
# PHASE 2: Basic Dependencies (Level 1)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 2: Basic dependencies (Level 1)"
echo "=============================================="

# xz_utils (Milvus version, shared=True)
build_package "recipes/xz_utils/all/conanfile.py" "5.4.5" "-o xz_utils/*:shared=True"

# c-ares (minimal deps)
build_package "recipes/c-ares/all/conanfile.py" "1.19.1"

# abseil (Milvus version, needed before protobuf/5.27.0)
build_package "recipes/abseil/all/conanfile.py" "20250127.0"

# protobuf depends on zlib, abseil (Milvus version)
build_package "recipes/protobuf/all/conanfile.py" "5.27.0" "-o protobuf/*:shared=True" "milvus/dev"

# libunwind depends on xz_utils, zlib (Milvus version)
build_package "recipes/libunwind/all/conanfile.py" "1.8.1"

# s2n depends on openssl (Milvus overrides s2n/1.4.1 from aws-c-io to 1.6.0 for OpenSSL 3.x FIPS)
build_package "recipes/s2n/all/conanfile.py" "1.6.0"

# libevent depends on openssl (now a direct Milvus dep)
build_package "recipes/libevent/all/conanfile.py" "2.1.12" "-o libevent/*:shared=True"

# libsodium (Milvus version, also used by folly)
build_package "recipes/libsodium/all/conanfile.py" "cci.20220430"

# re2 (minimal deps for this version)
build_package "recipes/re2/all/conanfile.py" "20230301"

# glog depends on gflags, libunwind (Milvus version)
build_package "recipes/glog/all/conanfile.py" "0.7.1" "-o glog/*:with_gflags=True -o glog/*:shared=True"

# benchmark depends on cmake
build_package "recipes/benchmark/all/conanfile.py" "1.7.0"

# Build tools Level 1
build_package "recipes/flex/all/conanfile.py" "2.6.4"
build_package "recipes/autoconf/all/conanfile.py" "2.71"

# Folly dependencies (needed in Phase 7)
build_package "recipes/libiberty/all/conanfile.py" "9.1.0"

# ============================================================================
# PHASE 3: Intermediate Dependencies (Level 2)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 3: Intermediate dependencies (Level 2)"
echo "=============================================="

# automake depends on autoconf
build_package "recipes/automake/all/conanfile.py" "1.16.5"

# meson depends on ninja
build_package "recipes/meson/all/conanfile.py" "1.2.2"

# boost depends on zlib, bzip2, xz_utils, zstd (Milvus version, also used by folly)
build_package "recipes/boost/all/conanfile.py" "1.83.0" "-o boost/*:without_locale=False -o boost/*:without_test=True"

# onetbb (Milvus version)
build_package "recipes/onetbb/all/conanfile.py" "2021.9.0" "-o onetbb/*:tbbmalloc=False -o onetbb/*:tbbproxy=False"

# jemalloc depends on automake
build_package "recipes/jemalloc/all/conanfile.py" "5.3.0"

# googleapis depends on protobuf
build_package "recipes/googleapis/all/conanfile.py" "cci.20221108"

# libdwarf (needed by folly)
build_package "recipes/libdwarf/all/conanfile.py" "20191104"

# ============================================================================
# PHASE 4: Complex Libraries (Level 3)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 4: Complex libraries (Level 3)"
echo "=============================================="

# libtool depends on automake
build_package "recipes/libtool/all/conanfile.py" "2.4.7"

# bison depends on m4, automake, flex
build_package "recipes/bison/all/conanfile.py" "3.8.2"

# grpc depends on protobuf/5.27.0@milvus/dev, c-ares, openssl, re2, zlib, abseil/20250127.0
build_package "recipes/grpc/all/conanfile.py" "1.67.1" "" "milvus/dev"

# librdkafka depends on lz4, zlib, zstd, openssl, cyrus-sasl
build_package "recipes/librdkafka/all/conanfile.py" "1.9.1" \
    "-o librdkafka/*:shared=True -o librdkafka/*:zstd=True -o librdkafka/*:ssl=True -o librdkafka/*:sasl=True"

# ============================================================================
# PHASE 5: High-Level Libraries (Level 4)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 5: High-level libraries (Level 4)"
echo "=============================================="

# thrift depends on boost, openssl, zlib, libevent, flex, bison
build_package "recipes/thrift/all/conanfile.py" "0.17.0"

# azure-sdk-for-cpp depends on openssl, libcurl, libxml2
build_package "recipes/azure-sdk-for-cpp/all/conanfile.py" "1.11.3" "" "milvus/dev"

# ============================================================================
# PHASE 6: AWS SDK (Level 5-6)
# ============================================================================
echo ""
echo "=============================================="
echo "PHASE 6: AWS SDK chain (Level 5-6)"
echo "=============================================="

# aws-sdk-cpp (uses CCI 0.12.5-based aws-c-* chain, built as --build=missing)
build_package "recipes/aws-sdk-cpp/all/conanfile.py" "1.11.692" \
    "-o aws-sdk-cpp/*:config=True -o aws-sdk-cpp/*:s3-crt=True -o aws-sdk-cpp/*:text-to-speech=False -o aws-sdk-cpp/*:transfer=False" \
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
build_package_no_test "recipes/opentelemetry-cpp/all/conanfile.py" "1.23.0" \
    "-o opentelemetry-cpp/*:with_stl=True" "milvus/dev"

# folly depends on boost, bzip2, double-conversion, gflags, glog, libevent,
#   openssl, lz4, snappy, zlib, zstd, libsodium, xz_utils, libunwind, fmt,
#   libiberty, libdwarf
build_package_no_test "recipes/folly/v2024/conanfile.py" "2024.08.12.00" "-o folly/*:shared=True" "milvus/dev"

# google-cloud-cpp depends on abseil, nlohmann_json, crc32c, libcurl, openssl, zlib
# (storage-only build, no grpc/protobuf needed)
build_package "recipes/google-cloud-cpp/2.28.0/conanfile.py" "2.28.0" "" "milvus/dev"

# rocksdb depends on gflags, snappy, lz4, zlib, zstd, onetbb, jemalloc
build_package "recipes/rocksdb/all/conanfile.py" "6.29.5" \
    "-o rocksdb/*:shared=True -o rocksdb/*:with_zstd=True" "milvus/dev"

# libavrocpp depends on boost, snappy, fmt, zlib
build_package "recipes/libavrocpp/v2/conanfile.py" "1.12.1.1" "" "milvus/dev"

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
build_package "recipes/arrow/all/conanfile.py" "17.0.0" \
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
# Step 3: Summary
# ============================================================================
echo ""
echo "=============================================="
echo "Build complete! ${#BUILT_PACKAGES[@]} packages built from repo recipes."
echo "=============================================="
echo ""
echo "Built packages:"
for pkg in "${BUILT_PACKAGES[@]}"; do
    echo "  - $pkg"
done
echo ""
echo "Installed from conancenter (not uploaded):"
echo "  - openssl/3.3.2"
echo "  - libcurl/8.10.1"
echo "  - prometheus-cpp/1.2.4"
echo ""
echo "Transitive downloaded from conancenter (not uploaded):"
echo "  - simde/0.8.2"
echo "  - unordered_dense/4.4.0"
echo "  - icu/74.2"

# ============================================================================
# Step 4: Upload (optional, --upload flag)
# ============================================================================

# Function to upload all built recipes to the remote
upload_recipes() {
    echo ""
    echo "=============================================="
    echo "Step 4: Uploading recipes to '$REMOTE_NAME'"
    echo "=============================================="

    # Add remote if not already configured
    if ! conan remote list 2>/dev/null | grep -q "$REMOTE_NAME"; then
        echo "Adding remote '$REMOTE_NAME'..."
        conan remote add "$REMOTE_NAME" "$REMOTE_URL"
    fi

    # Login if not already authenticated
    if ! conan remote auth "$REMOTE_NAME" 2>/dev/null; then
        if [ -n "${JFROG_USERNAME2:-}" ] && [ -n "${JFROG_PASSWORD2:-}" ]; then
            conan remote login "$REMOTE_NAME" "$JFROG_USERNAME2" -p "$JFROG_PASSWORD2"
        else
            echo "JFROG_USERNAME2 or JFROG_PASSWORD2 not set, attempting interactive login..."
            read -rp "JFrog Username: " JFROG_USERNAME2
            read -rsp "JFrog Password: " JFROG_PASSWORD2
            echo ""
            conan remote login "$REMOTE_NAME" "$JFROG_USERNAME2" -p "$JFROG_PASSWORD2"
        fi
    fi

    echo ""
    echo "Recipes to upload:"
    for pkg in "${BUILT_PACKAGES[@]}"; do
        echo "  $pkg"
    done
    echo ""

    for pkg in "${BUILT_PACKAGES[@]}"; do
        echo "Uploading $pkg ..."
        conan upload "$pkg" -r "$REMOTE_NAME" -c --only-recipe
    done

    echo ""
    echo "=============================================="
    echo "Upload complete! ${#BUILT_PACKAGES[@]} recipes uploaded."
    echo "=============================================="
}

if [ "$DO_UPLOAD" = true ]; then
    upload_recipes
else
    echo ""
    echo "To upload recipes to Artifactory, re-run with --upload:"
    echo "  ./scripts/build-milvus-deps.sh --upload"
fi
