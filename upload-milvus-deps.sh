#!/bin/bash
set -euo pipefail

# Upload all local Conan packages to JFrog Artifactory
# Usage:
#   ./upload-milvus-deps.sh
#
# Environment variables:
#   JFROG_USERNAME - JFrog username (or prompted interactively)
#   JFROG_PASSWORD - JFrog password (or prompted interactively)

REMOTE_NAME="default-conan-local2"
REMOTE_URL="https://milvus01.jfrog.io/artifactory/api/conan/default-conan-local2"

echo "=============================================="
echo "Upload Milvus dependencies to Artifactory"
echo "=============================================="
echo "Remote: $REMOTE_NAME ($REMOTE_URL)"
echo ""

# Add remote if not already configured
if ! conan remote list 2>/dev/null | grep -q "$REMOTE_NAME"; then
    echo "Adding remote '$REMOTE_NAME'..."
    conan remote add "$REMOTE_NAME" "$REMOTE_URL"
fi

# Login
if [ -n "${JFROG_USERNAME:-}" ] && [ -n "${JFROG_PASSWORD:-}" ]; then
    conan remote login "$REMOTE_NAME" "$JFROG_USERNAME" -p "$JFROG_PASSWORD"
else
    echo "JFROG_USERNAME or JFROG_PASSWORD not set, attempting interactive login..."
    read -rp "JFrog Username: " JFROG_USERNAME
    read -rsp "JFrog Password: " JFROG_PASSWORD
    echo ""
    conan remote login "$REMOTE_NAME" "$JFROG_USERNAME" -p "$JFROG_PASSWORD"
fi

# List packages to be uploaded
echo ""
echo "Packages in local cache:"
conan list '*'

# Upload recipes only (no binaries)
echo ""
echo "=============================================="
echo "Uploading all recipes to '$REMOTE_NAME'..."
echo "=============================================="
conan upload '*' -r "$REMOTE_NAME" -c --only-recipe

echo ""
echo "=============================================="
echo "Upload complete!"
echo "=============================================="
