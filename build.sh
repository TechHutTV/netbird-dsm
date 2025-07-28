#!/bin/bash

# Build script for NetBird DSM package
set -e

PACKAGE_NAME="NetBird"
PACKAGE_VERSION="0.28.0-1"
BUILD_DIR="build"
PACKAGE_DIR="$BUILD_DIR/$PACKAGE_NAME"

echo "Building NetBird DSM package..."

# Clean previous build
rm -rf "$BUILD_DIR"

# Create package structure
mkdir -p "$PACKAGE_DIR"/{scripts,conf,target}

# Copy package files
echo "Copying package files..."

# Copy INFO file
cp INFO "$PACKAGE_DIR/"

# Copy icon (you'll need to provide this)
if [ -f "PACKAGE_ICON.PNG" ]; then
    cp PACKAGE_ICON.PNG "$PACKAGE_DIR/"
else
    echo "Warning: PACKAGE_ICON.PNG not found. Creating placeholder..."
    # Create a simple 72x72 PNG placeholder
    convert -size 72x72 xc:lightblue -font Arial -pointsize 12 -gravity center \
            -annotate +0+0 "NetBird" "$PACKAGE_DIR/PACKAGE_ICON.PNG" 2>/dev/null || \
    echo "Note: Install ImageMagick to auto-generate icon, or provide PACKAGE_ICON.PNG manually"
fi

# Copy scripts
cp scripts/start-stop-status "$PACKAGE_DIR/scripts/"
cp scripts/postinst "$PACKAGE_DIR/scripts/"
cp scripts/preuninst "$PACKAGE_DIR/scripts/"
cp scripts/postuninst "$PACKAGE_DIR/scripts/"

# Make scripts executable
chmod +x "$PACKAGE_DIR/scripts/"*

# Copy privilege file
cp conf/privilege "$PACKAGE_DIR/conf/"

# Copy NetBird binary (you need to provide this)
if [ -f "netbird" ]; then
    cp netbird "$PACKAGE_DIR/target/"
    chmod +x "$PACKAGE_DIR/target/netbird"
    echo "NetBird binary copied successfully"
else
    echo "ERROR: NetBird binary not found!"
    echo "Please download or compile the NetBird binary for your target architecture:"
    echo "  - For x86_64: https://github.com/netbirdio/netbird/releases"
    echo "  - Or compile from source: https://github.com/netbirdio/netbird"
    echo "Place the binary in the current directory as 'netbird'"
    exit 1
fi

# Create the SPK package
echo "Creating SPK package..."
cd "$BUILD_DIR"

# Create tarball
tar czf package.tgz "$PACKAGE_NAME"

# Create the final SPK (which is just a tar file with specific structure)
tar cf "${PACKAGE_NAME}-${PACKAGE_VERSION}.spk" package.tgz

# Move SPK to root directory
mv "${PACKAGE_NAME}-${PACKAGE_VERSION}.spk" "../"

cd ..

echo "Package created successfully: ${PACKAGE_NAME}-${PACKAGE_VERSION}.spk"
echo ""
echo "Installation instructions:"
echo "1. Open DSM Package Center"
echo "2. Click 'Manual Install'"
echo "3. Upload the .spk file"
echo "4. Follow the installation wizard"
echo ""
echo "After installation:"
echo "1. Start the NetBird service"
echo "2. SSH into your DSM and run: netbird login"
echo "3. Follow the authentication process"
echo "4. Run: netbird status to verify connection"
