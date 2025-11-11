#!/bin/bash
# Build script for Firefox extension

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Building Zen Browser Bridge Firefox Extension${NC}"

# Get version from manifest.json
VERSION=$(grep '"version"' manifest.json | sed 's/.*"version": "\(.*\)".*/\1/')
echo -e "Version: ${GREEN}${VERSION}${NC}"

# Create build directory
BUILD_DIR="build"
mkdir -p "$BUILD_DIR"

# Package name
PACKAGE_NAME="zen-browser-bridge-${VERSION}.zip"
XPI_NAME="zen-browser-bridge-${VERSION}.xpi"

# Remove old packages
rm -f "$BUILD_DIR"/*.zip "$BUILD_DIR"/*.xpi

echo "Packaging extension..."

# Create zip file with all necessary files
zip -r "$BUILD_DIR/$PACKAGE_NAME" \
    manifest.json \
    background.js \
    content.js \
    popup/ \
    icons/ \
    -x "*.DS_Store" \
    -x "*/__pycache__/*"

# Copy zip to .xpi for Firefox
cp "$BUILD_DIR/$PACKAGE_NAME" "$BUILD_DIR/$XPI_NAME"

echo -e "${GREEN}✓${NC} Extension packaged successfully!"
echo -e "  Zip: ${BLUE}$BUILD_DIR/$PACKAGE_NAME${NC}"
echo -e "  XPI: ${BLUE}$BUILD_DIR/$XPI_NAME${NC}"
echo ""
echo "Next steps for permanent installation:"
echo "  1. Get Firefox Add-on Developer account: https://addons.mozilla.org/developers/"
echo "  2. Sign the extension: https://extensionworkshop.com/documentation/publish/signing-and-distribution-overview/"
echo ""
echo "For self-distribution (unsigned):"
echo "  • Use Firefox Developer Edition or Nightly"
echo "  • Set xpinstall.signatures.required = false in about:config"
echo "  • Drag and drop the .xpi file into Firefox"
