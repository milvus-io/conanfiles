#!/bin/bash
set -e

# Download a package from ConanCenter and upload it (with all transitive
# dependencies) to a JFrog Artifactory remote.
#
# Usage:
#   ./scripts/sync-to-artifactory.sh <package> <version> [options]
#
# Required arguments:
#   <package>       Package name (e.g. openssl, libcurl)
#   <version>       Package version (e.g. 3.3.2, 8.10.1)
#
# Optional arguments:
#   --repository <repo>  Target Artifactory repository: production or testing (default: production)
#   --no-upload          Download only, skip uploading to Artifactory
#
# Examples:
#   ./scripts/sync-to-artifactory.sh openssl 3.3.2
#   ./scripts/sync-to-artifactory.sh libcurl 8.10.1 --repository testing
#   ./scripts/sync-to-artifactory.sh prometheus-cpp 1.2.4 --no-upload

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Remote configuration
REMOTE_NAME_PRODUCTION="default-conan-local2"
REMOTE_URL_PRODUCTION="https://milvus01.jfrog.io/artifactory/api/conan/default-conan-local2"
REMOTE_NAME_TESTING="testing2"
REMOTE_URL_TESTING="https://milvus01.jfrog.io/artifactory/api/conan/testing2"

# Common conan settings
CONAN_SETTINGS="-s compiler=gcc -s compiler.version=11 -s compiler.libcxx=libstdc++11 -s compiler.cppstd=17 -s build_type=Release"

# CMake 4.x compatibility
export CMAKE_POLICY_VERSION_MINIMUM=3.5

# ============================================================================
# Parse arguments
# ============================================================================
PACKAGE=""
VERSION=""
REPOSITORY="production"
DO_UPLOAD=true

while [ $# -gt 0 ]; do
    case "$1" in
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
    echo "Usage: $0 <package> <version> [--repository production|testing] [--no-upload]" >&2
    exit 1
fi

# Resolve remote name and URL based on repository choice
if [ "$REPOSITORY" = "production" ]; then
    REMOTE_NAME="$REMOTE_NAME_PRODUCTION"
    REMOTE_URL="$REMOTE_URL_PRODUCTION"
else
    REMOTE_NAME="$REMOTE_NAME_TESTING"
    REMOTE_URL="$REMOTE_URL_TESTING"
fi

PACKAGE_REF="${PACKAGE}/${VERSION}"

# ============================================================================
# Step 1: Install package from ConanCenter
# ============================================================================
echo "=============================================="
echo "Step 1: Installing $PACKAGE_REF from ConanCenter"
echo "=============================================="

INSTALL_GRAPH=$(mktemp /tmp/conan-install-graph-XXXXXX.json)
trap "rm -f $INSTALL_GRAPH ${INSTALL_GRAPH%.json}-pkglist.json" EXIT

conan install --requires="$PACKAGE_REF" \
    $CONAN_SETTINGS \
    --format=json > "$INSTALL_GRAPH"

# ============================================================================
# Step 2: Generate package list from install graph
# ============================================================================
echo ""
echo "=============================================="
echo "Step 2: Generating package list from install graph"
echo "=============================================="

PKGLIST="${INSTALL_GRAPH%.json}-pkglist.json"
conan list --graph="$INSTALL_GRAPH" --graph-binaries="*" --format=json > "$PKGLIST"

echo "Packages in the install graph:"
conan list --graph="$INSTALL_GRAPH" --graph-binaries="*"

# ============================================================================
# Step 3: Upload to Artifactory
# ============================================================================
if [ "$DO_UPLOAD" = true ]; then
    echo ""
    echo "=============================================="
    echo "Step 3: Uploading to '$REMOTE_NAME' ($REPOSITORY)"
    echo "=============================================="

    # Add remote if not already configured
    if ! conan remote list 2>/dev/null | grep -q "$REMOTE_NAME"; then
        echo "Adding remote '$REMOTE_NAME'..."
        conan remote add "$REMOTE_NAME" "$REMOTE_URL"
    fi

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

    # Upload only the target package and its dependencies (recipes and binaries)
    conan upload --list="$PKGLIST" -r "$REMOTE_NAME" -c

    echo ""
    echo "=============================================="
    echo "Upload complete: $PACKAGE_REF and all transitive dependencies"
    echo "=============================================="
else
    echo ""
    echo "Download complete: $PACKAGE_REF (upload skipped, use without --no-upload to upload)"
fi
