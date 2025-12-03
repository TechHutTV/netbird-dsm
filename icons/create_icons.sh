#!/bin/bash
# Copyright (c) 2024 NetBird DSM Package
# SPDX-License-Identifier: MIT

# Script to create package icons
# Requires ImageMagick (convert command)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for ImageMagick
if ! command -v convert &> /dev/null; then
    echo "ImageMagick is required to generate icons."
    echo "Install with: apt-get install imagemagick"
    echo ""
    echo "Creating placeholder icons instead..."

    # Create minimal placeholder PNGs using base64
    # These are valid 1x1 blue PNG files that will be stretched
    # You should replace these with proper icons

    # Minimal blue PNG for placeholder
    echo "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAZElEQVR4Ae3OAQkAMAgAQN9/aGYJZYMo8+4+AAAAAAAAAAAAvGULLLDAAgsssMACCyywwAILLLDAAgsssMACCyywwAILLLDAAgsssMACCyywwAILLLDAAgsssMACCyywwAILeOsBfHwEQSxQKTgAAAAASUVORK5CYII=" | base64 -d > "${SCRIPT_DIR}/PACKAGE_ICON.PNG"

    echo "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAAaElEQVR4Ae3OAQkAMAgAQN9/aGYJZYMo8+4+AAAAAAAAAAAAvGULLLDAAgsssMACCyywwAILLLDAAgsssMACCyywwAILLLDAAgsssMACCyywwAILLLDAAgsssMACCyywwAILLLDAAgsssMACCyywwAILeOsBfHwEQSxQKTgAAAAASUVORK5CYII=" | base64 -d > "${SCRIPT_DIR}/PACKAGE_ICON_256.PNG"

    echo "Placeholder icons created."
    echo "Please replace with proper 64x64 and 256x256 PNG icons."
    exit 0
fi

# Create SVG source
SVG_ICON='<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4A90D9;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#2E5C8A;stop-opacity:1" />
    </linearGradient>
  </defs>
  <!-- Background circle -->
  <circle cx="128" cy="128" r="120" fill="url(#bgGrad)"/>
  <!-- Bird silhouette / network nodes -->
  <g fill="white">
    <!-- Central node -->
    <circle cx="128" cy="128" r="20"/>
    <!-- Network connections -->
    <path d="M128,108 L128,60 M128,148 L128,196" stroke="white" stroke-width="8" stroke-linecap="round"/>
    <path d="M108,128 L60,128 M148,128 L196,128" stroke="white" stroke-width="8" stroke-linecap="round"/>
    <path d="M114,114 L70,70 M142,114 L186,70" stroke="white" stroke-width="8" stroke-linecap="round"/>
    <path d="M114,142 L70,186 M142,142 L186,186" stroke="white" stroke-width="8" stroke-linecap="round"/>
    <!-- Outer nodes -->
    <circle cx="128" cy="50" r="12"/>
    <circle cx="128" cy="206" r="12"/>
    <circle cx="50" cy="128" r="12"/>
    <circle cx="206" cy="128" r="12"/>
    <circle cx="62" cy="62" r="10"/>
    <circle cx="194" cy="62" r="10"/>
    <circle cx="62" cy="194" r="10"/>
    <circle cx="194" cy="194" r="10"/>
  </g>
</svg>'

# Write SVG file
echo "${SVG_ICON}" > "${SCRIPT_DIR}/netbird.svg"

# Generate PNG icons
echo "Generating 64x64 icon..."
convert -background none -resize 64x64 "${SCRIPT_DIR}/netbird.svg" "${SCRIPT_DIR}/PACKAGE_ICON.PNG"

echo "Generating 256x256 icon..."
convert -background none -resize 256x256 "${SCRIPT_DIR}/netbird.svg" "${SCRIPT_DIR}/PACKAGE_ICON_256.PNG"

# Generate UI icons (various sizes needed by DSM)
for size in 16 24 32 48 64 72; do
    echo "Generating ${size}x${size} UI icon..."
    convert -background none -resize ${size}x${size} "${SCRIPT_DIR}/netbird.svg" "${SCRIPT_DIR}/../ui/images/netbird-${size}.png"
done

echo ""
echo "Icons generated successfully!"
echo "  - ${SCRIPT_DIR}/PACKAGE_ICON.PNG (64x64)"
echo "  - ${SCRIPT_DIR}/PACKAGE_ICON_256.PNG (256x256)"
echo "  - UI icons in ${SCRIPT_DIR}/../ui/images/"
