#!/bin/bash
set -e

# Build a single Conan package from this repo's recipes and upload the recipe
# (recipe-only) to the JFrog Artifactory remote.
#
# Usage:
#   ./scripts/build-and-push.sh <package> <version> [options]
#
# Required arguments:
#   <package>       Package name (e.g. zlib, folly, arrow)
#   <version>       Package version (e.g. 1.3.1, 2024.08.12.00)
#
# Optional arguments:
#   --conanfile <path>        Relative path to conanfile.py within the package dir (default: all/conanfile.py)
#   --user-channel <u/c>     User/channel for the package (e.g. milvus/dev)
#   --extra-options <opts>   Extra conan options (e.g. "-o pkg:opt=val -c conf=val")
#   --repository <repo>      Target Artifactory repository: production or testing (default: production)
#   --no-upload              Build only, skip uploading to Artifactory
#
# Examples:
#   ./scripts/build-and-push.sh zlib 1.3.1
#   ./scripts/build-and-push.sh folly 2024.08.12.00 --conanfile v2024/conanfile.py --user-channel milvus/dev --extra-options "-o folly/*:shared=True"
#   ./scripts/build-and-push.sh protobuf 5.27.0 --user-channel milvus/dev --repository testing
#   ./scripts/build-and-push.sh protobuf 5.27.0 --user-channel milvus/dev --no-upload

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Remote configuration
REMOTE_NAME_PRODUCTION="default-conan-local2"
REMOTE_URL_PRODUCTION="https://milvus01.jfrog.io/artifactory/api/conan/default-conan-local2"
ARTIFACTORY_STORAGE_URL_PRODUCTION="https://milvus01.jfrog.io/artifactory/api/storage/default-conan-local2"
REMOTE_NAME_TESTING="testing2"
REMOTE_URL_TESTING="https://milvus01.jfrog.io/artifactory/api/conan/testing2"
ARTIFACTORY_STORAGE_URL_TESTING="https://milvus01.jfrog.io/artifactory/api/storage/testing2"

# Common conan settings
CONAN_SETTINGS="-s compiler=gcc -s compiler.version=11 -s compiler.libcxx=libstdc++11 -s compiler.cppstd=17 -s build_type=Release -s:b compiler.cppstd=17"

# Use 6 parallel jobs for building
CONAN_JOBS="-c tools.build:jobs=6"

# CMake 4.x compatibility
export CMAKE_POLICY_VERSION_MINIMUM=3.5

# ============================================================================
# Parse arguments
# ============================================================================
PACKAGE=""
VERSION=""
CONANFILE_PATH="all/conanfile.py"
USER_CHANNEL=""
EXTRA_OPTIONS=""
REPOSITORY="production"
DO_UPLOAD=true

while [ $# -gt 0 ]; do
    case "$1" in
        --conanfile)
            CONANFILE_PATH="$2"
            shift 2
            ;;
        --user-channel)
            USER_CHANNEL="$2"
            shift 2
            ;;
        --extra-options)
            EXTRA_OPTIONS="$2"
            shift 2
            ;;
        --repository)
            REPOSITORY="$2"
            if [ "$REPOSITORY" != "production" ] && [ "$REPOSITORY" != "testing" ]; then
                echo "Error: --repository must be 'production' or 'testing'" >&2
                exit 1
            fi
            shift 2
            ;;
        --no-upload)
            DO_UPLOAD=false
            shift
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            if [ -z "$PACKAGE" ]; then
                PACKAGE="$1"
            elif [ -z "$VERSION" ]; then
                VERSION="$1"
            else
                echo "Unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$PACKAGE" ] || [ -z "$VERSION" ]; then
    echo "Usage: $0 <package> <version> [--conanfile <path>] [--user-channel <u/c>] [--extra-options <opts>] [--repository production|testing] [--no-upload]" >&2
    exit 1
fi

# Resolve remote name and URL based on repository choice
if [ "$REPOSITORY" = "production" ]; then
    REMOTE_NAME="$REMOTE_NAME_PRODUCTION"
    REMOTE_URL="$REMOTE_URL_PRODUCTION"
    ARTIFACTORY_STORAGE_URL="$ARTIFACTORY_STORAGE_URL_PRODUCTION"
else
    REMOTE_NAME="$REMOTE_NAME_TESTING"
    REMOTE_URL="$REMOTE_URL_TESTING"
    ARTIFACTORY_STORAGE_URL="$ARTIFACTORY_STORAGE_URL_TESTING"
fi

RECIPE_PATH="recipes/${PACKAGE}/${CONANFILE_PATH}"

if [ ! -f "$RECIPE_PATH" ]; then
    echo "Error: recipe not found at $RECIPE_PATH" >&2
    exit 1
fi

# Build package reference string for display
if [ -n "$USER_CHANNEL" ]; then
    PKG_REF="${PACKAGE}/${VERSION}@${USER_CHANNEL}"
else
    PKG_REF="${PACKAGE}/${VERSION}"
fi

# ============================================================================
# Step 1: Configure Conan remotes
# ============================================================================
echo "=============================================="
echo "Step 1: Configuring Conan remotes"
echo "=============================================="

# Add both remotes for dependency resolution (production first, testing second,
# conancenter remains as lowest priority)
if ! conan remote list 2>/dev/null | grep -q "$REMOTE_NAME_PRODUCTION"; then
    conan remote add "$REMOTE_NAME_PRODUCTION" "$REMOTE_URL_PRODUCTION" --index 0
fi
if ! conan remote list 2>/dev/null | grep -q "$REMOTE_NAME_TESTING"; then
    conan remote add "$REMOTE_NAME_TESTING" "$REMOTE_URL_TESTING" --index 1
fi

conan remote list

# ============================================================================
# Step 2: Export all local recipes
# ============================================================================
echo ""
echo "=============================================="
echo "Step 2: Exporting all local recipes"
echo "=============================================="

# Export all local recipes into the Conan cache so that cross-dependencies
# between recipes in this repo resolve locally instead of falling through
# to ConanCenter. Each recipe's config.yml specifies the folder (e.g. "all",
# "3.x.x", "v2024") containing the conanfile.py for each version.
for config in recipes/*/config.yml; do
    pkg_dir=$(dirname "$config")
    pkg_name=$(basename "$pkg_dir")
    python3 -c "
import yaml, sys
with open('$config') as f:
    data = yaml.safe_load(f)
for ver, info in (data.get('versions') or {}).items():
    folder = info.get('folder', 'all') if isinstance(info, dict) else 'all'
    print(f'{ver} {folder}')
" | while read -r ver folder; do
        recipe="$pkg_dir/$folder/conanfile.py"
        if [ -f "$recipe" ]; then
            conan export "$recipe" "$pkg_name/$ver@" 2>/dev/null || true
        fi
    done
done

# ============================================================================
# Step 3: Build the package
# ============================================================================
echo ""
echo "=============================================="
echo "Step 3: Building $PKG_REF"
echo "=============================================="

USER_FLAGS=""
if [ -n "$USER_CHANNEL" ]; then
    USER_FLAGS="--user=${USER_CHANNEL%%/*} --channel=${USER_CHANNEL#*/}"
fi

BUILD_GRAPH=$(mktemp /tmp/conan-graph-XXXXXX.json)
trap "rm -f $BUILD_GRAPH ${BUILD_GRAPH%.json}-pkglist.json" EXIT

conan create "$RECIPE_PATH" \
    --version="$VERSION" \
    --build=missing \
    $CONAN_SETTINGS \
    $CONAN_JOBS \
    $USER_FLAGS \
    $EXTRA_OPTIONS \
    --format=json > "$BUILD_GRAPH"

# ============================================================================
# Step 4: Generate package list from build graph
# ============================================================================
echo ""
echo "=============================================="
echo "Step 4: Generating package list from build graph"
echo "=============================================="

PKGLIST="${BUILD_GRAPH%.json}-pkglist.json"
conan list --graph="$BUILD_GRAPH" --graph-binaries="*" --format=json > "$PKGLIST"

echo "Packages in the build graph:"
conan list --graph="$BUILD_GRAPH" --graph-binaries="*"

# ============================================================================
# Step 5: Upload recipes to Artifactory
# ============================================================================
if [ "$DO_UPLOAD" = true ]; then
    echo ""
    echo "=============================================="
    echo "Step 5: Uploading recipes to '$REMOTE_NAME' ($REPOSITORY)"
    echo "=============================================="

    # Login
    if [ -n "${JFROG_USERNAME2:-}" ] && [ -n "${JFROG_PASSWORD2:-}" ]; then
        conan remote login "$REMOTE_NAME" "$JFROG_USERNAME2" -p "$JFROG_PASSWORD2"
    else
        echo "JFROG_USERNAME2 or JFROG_PASSWORD2 not set, attempting interactive login..."
        read -rp "JFrog Username: " JFROG_USERNAME2
        read -rsp "JFrog Password: " JFROG_PASSWORD2
        echo ""
        conan remote login "$REMOTE_NAME" "$JFROG_USERNAME2" -p "$JFROG_PASSWORD2"
    fi

    # Show which recipes will be uploaded (extracted from the package list)
    echo ""
    echo "Recipes to upload:"
    python3 -c "
import json
with open('$PKGLIST') as f:
    data = json.load(f)
for repo in data.values():
    for pkg_name, pkg_data in repo.items():
        for rev in pkg_data.get('revisions', {}):
            print(f'  {pkg_name}#{rev}')
"
    echo ""

    # Upload only the target recipe and its dependencies (recipe-only)
    conan upload --list="$PKGLIST" -r "$REMOTE_NAME" -c --only-recipe

    # ========================================================================
    # Step 6: Set build metadata properties on the uploaded recipe
    # ========================================================================
    echo ""
    echo "=============================================="
    echo "Step 6: Setting build metadata on '$PKG_REF'"
    echo "=============================================="

    # Get the recipe revision from local cache
    RECIPE_REV=$(conan list "${PKG_REF}#*" --format=json 2>/dev/null | \
        python3 -c "
import json, sys
data = json.load(sys.stdin)
for repo in data.values():
    for pkg_data in repo.values():
        revs = pkg_data.get('revisions', {})
        if revs:
            # Get the latest revision (last key)
            print(list(revs.keys())[-1])
            sys.exit(0)
" 2>/dev/null)

    if [ -n "$RECIPE_REV" ]; then
        BUILD_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
        BUILD_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
        BUILD_DATETIME=$(LC_ALL=C date -u +"%d %b %Y %H:%M:%S")
        BUILD_AUTHOR=$(git log -1 --format='%an' 2>/dev/null || echo "unknown")

        # URL-encode spaces for JFrog REST API
        ENCODED_DATETIME=$(echo "$BUILD_DATETIME" | sed 's/ /%20/g')
        ENCODED_AUTHOR=$(echo "$BUILD_AUTHOR" | sed 's/ /%20/g')

        PROPS="build.branch=${BUILD_BRANCH};build.commit=${BUILD_COMMIT};build.datetime=${ENCODED_DATETIME};build.author=${ENCODED_AUTHOR}"

        # Build artifact path: user/name/version/channel/revision for @user/channel,
        # or _/name/version/_/revision for packages without user/channel
        if [ -n "$USER_CHANNEL" ]; then
            ARTIFACT_USER="${USER_CHANNEL%%/*}"
            ARTIFACT_CHANNEL="${USER_CHANNEL#*/}"
        else
            ARTIFACT_USER="_"
            ARTIFACT_CHANNEL="_"
        fi
        ARTIFACT_PATH="${ARTIFACT_USER}/${PACKAGE}/${VERSION}/${ARTIFACT_CHANNEL}/${RECIPE_REV}/export/conanfile.py"

        curl -s -u "${JFROG_USERNAME2}:${JFROG_PASSWORD2}" -X PUT \
            "${ARTIFACTORY_STORAGE_URL}/${ARTIFACT_PATH}?properties=${PROPS}" > /dev/null

        echo "Properties set on ${PKG_REF}#${RECIPE_REV}:"
        echo "  build.branch   = ${BUILD_BRANCH}"
        echo "  build.commit   = ${BUILD_COMMIT}"
        echo "  build.datetime = ${BUILD_DATETIME}"
        echo "  build.author   = ${BUILD_AUTHOR}"
    else
        echo "Warning: could not determine recipe revision, skipping metadata"
    fi

    echo ""
    echo "=============================================="
    echo "Upload complete: $PKG_REF and dependencies (recipe-only)"
    echo "=============================================="
else
    echo ""
    echo "Build complete: $PKG_REF (upload skipped, use without --no-upload to upload)"
fi
