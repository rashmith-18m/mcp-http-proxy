#!/usr/bin/env bash
#
# publish.sh — Upload platform binaries + publish npm package to Artifactory
#
# Usage:
#   ./publish.sh                    # Uses version from npm/package.json
#   ./publish.sh 1.2.0              # Override version
#
# Prerequisites:
#   - Built binaries in build/ (from GitHub Actions artifacts)
#   - Node.js / npm installed
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
NPM_DIR="$SCRIPT_DIR/npm"

# Artifactory config
ARTIFACTORY_BASE="https://wal-artifactory.rocketsoftware.com/artifactory"
ARTIFACTORY_REPO="cypf-npm-dev-wal"
AUTH="Basic Ymx3bW9iZjpBS0NwOG1Zb1VmS0RUUlNoTWFYQnhUamg4TDQ1Zk5zelRueDJyVGlucGJoeWlmZFl0SnQ4Nkp6d2FwZDVERE5oWVp0eGJLdk42"

# Version — from argument or package.json
VERSION="${1:-$(node -p "require('$NPM_DIR/package.json').version")}"

echo "=========================================="
echo " Publishing rocket-mcp-proxy v${VERSION}"
echo "=========================================="

# --- Verify binaries exist ---
BINARIES=(
  "rocket_mcp_proxy-windows-latest/rocket_mcp_proxy-windows-latest.exe"
  "rocket_mcp_proxy-macos-arm64/rocket_mcp_proxy-macos-arm64"
  "rocket_mcp_proxy-macos-x64/rocket_mcp_proxy-macos-x64"
  "rocket_mcp_proxy-ubuntu-latest/rocket_mcp_proxy-ubuntu-latest"
)

echo ""
echo "Checking binaries in $BUILD_DIR ..."
for bin in "${BINARIES[@]}"; do
  if [[ ! -f "$BUILD_DIR/$bin" ]]; then
    echo "ERROR: Missing binary: $BUILD_DIR/$bin"
    echo "Run GitHub Actions build first and download artifacts into build/"
    exit 1
  fi
  echo "  ✓ $bin ($(du -h "$BUILD_DIR/$bin" | cut -f1))"
done

# --- Upload binaries to Artifactory ---
UPLOAD_BASE="$ARTIFACTORY_BASE/$ARTIFACTORY_REPO/rocket-mcp-proxy/$VERSION"

echo ""
echo "Uploading binaries to $UPLOAD_BASE ..."

for bin in "${BINARIES[@]}"; do
  filename=$(basename "$bin")
  echo ""

  # Check if already uploaded
  CHECK_CODE=$(curl --retry 3 -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: $AUTH" \
    -I "$UPLOAD_BASE/$filename")

  if [[ "$CHECK_CODE" == "200" ]]; then
    echo "  ⏭ $filename already exists — skipping"
    continue
  fi

  echo "  Uploading $filename ..."
  HTTP_CODE=$(curl --retry 5 --retry-connrefused --retry-delay 3 -s -w "%{http_code}" \
    -H "Authorization: $AUTH" \
    -T "$BUILD_DIR/$bin" \
    "$UPLOAD_BASE/$filename" -o /tmp/artifactory_response.json)

  if [[ "$HTTP_CODE" == "201" ]]; then
    echo "  ✓ $filename uploaded (HTTP $HTTP_CODE)"
  else
    echo "  ✗ $filename failed (HTTP $HTTP_CODE)"
    cat /tmp/artifactory_response.json 2>/dev/null
    exit 1
  fi
done

# --- Update version in package.json if needed ---
CURRENT_PKG_VERSION=$(node -p "require('$NPM_DIR/package.json').version")
if [[ "$CURRENT_PKG_VERSION" != "$VERSION" ]]; then
  echo ""
  echo "Updating package.json version: $CURRENT_PKG_VERSION → $VERSION"
  cd "$NPM_DIR"
  npm version "$VERSION" --no-git-tag-version
fi

# --- Publish npm package ---
echo ""
echo "Publishing npm package v${VERSION} ..."
cd "$NPM_DIR"
npm publish

echo ""
echo "=========================================="
echo " ✓ Published successfully!"
echo "=========================================="
echo ""
echo "Artifacts in Artifactory ($ARTIFACTORY_REPO):"
echo "  npm package: @aicoe/rocket-mcp-proxy@$VERSION"
echo "  Windows:     $UPLOAD_BASE/rocket_mcp_proxy-windows-latest.exe"
echo "  macOS:       $UPLOAD_BASE/rocket_mcp_proxy-macos-latest"
echo "  Linux:       $UPLOAD_BASE/rocket_mcp_proxy-ubuntu-latest"
