# NetBird DSM Package Makefile
# Copyright (c) 2024 NetBird DSM Package
# SPDX-License-Identifier: MIT

PKG_NAME = netbird
PKG_VERSION = 0.60.4
PKG_RELEASE = 0001
FULL_VERSION = $(PKG_VERSION)-$(PKG_RELEASE)

# Directories
BUILD_DIR = build
DIST_DIR = dist
SPK_DIR = $(BUILD_DIR)/spk

# Package components
SCRIPTS = scripts/preinst scripts/postinst scripts/preuninst scripts/postuninst \
          scripts/preupgrade scripts/postupgrade scripts/start-stop-status
CONF_FILES = conf/privilege conf/resource conf/netbird.sc
WIZARD_FILES = WIZARD_UIFILES/install_uifile WIZARD_UIFILES/uninstall_uifile
UI_FILES = ui/config ui/index.cgi

.PHONY: all clean package info spk

all: spk

# Create INFO file from INFO.sh
info: $(BUILD_DIR)/INFO

$(BUILD_DIR)/INFO: INFO.sh
	@mkdir -p $(BUILD_DIR)
	@echo "Generating INFO file..."
	@bash INFO.sh > $(BUILD_DIR)/INFO

# Create package.tgz
package: $(BUILD_DIR)/package.tgz

$(BUILD_DIR)/package.tgz:
	@mkdir -p $(BUILD_DIR)/package/target/bin
	@mkdir -p $(BUILD_DIR)/package/target/etc
	@mkdir -p $(BUILD_DIR)/package/target/var
	@touch $(BUILD_DIR)/package/target/bin/.placeholder
	@cp -r ui $(BUILD_DIR)/package/ 2>/dev/null || true
	@chmod 755 $(BUILD_DIR)/package/ui/index.cgi 2>/dev/null || true
	@echo "Creating package.tgz..."
	@cd $(BUILD_DIR)/package && tar -czf ../package.tgz *

# Build SPK package
spk: info package
	@mkdir -p $(SPK_DIR)
	@mkdir -p $(DIST_DIR)
	@echo "Building SPK package..."
	# Copy INFO
	@cp $(BUILD_DIR)/INFO $(SPK_DIR)/
	# Copy package.tgz
	@cp $(BUILD_DIR)/package.tgz $(SPK_DIR)/
	# Copy scripts
	@mkdir -p $(SPK_DIR)/scripts
	@cp $(SCRIPTS) $(SPK_DIR)/scripts/
	@chmod 755 $(SPK_DIR)/scripts/*
	# Copy conf files
	@mkdir -p $(SPK_DIR)/conf
	@cp $(CONF_FILES) $(SPK_DIR)/conf/
	# Copy wizard files
	@mkdir -p $(SPK_DIR)/WIZARD_UIFILES
	@cp $(WIZARD_FILES) $(SPK_DIR)/WIZARD_UIFILES/
	# Copy icons
	@cp icons/PACKAGE_ICON.PNG $(SPK_DIR)/ 2>/dev/null || echo "Warning: PACKAGE_ICON.PNG not found"
	@cp icons/PACKAGE_ICON_256.PNG $(SPK_DIR)/ 2>/dev/null || echo "Warning: PACKAGE_ICON_256.PNG not found"
	# Create SPK archive
	@cd $(SPK_DIR) && tar -cf ../../$(DIST_DIR)/$(PKG_NAME)-$(FULL_VERSION).spk *
	@echo ""
	@echo "========================================="
	@echo "SPK package created successfully!"
	@echo "Output: $(DIST_DIR)/$(PKG_NAME)-$(FULL_VERSION).spk"
	@echo "========================================="

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR) $(DIST_DIR)

# Development helper: validate scripts
validate:
	@echo "Validating shell scripts..."
	@for script in $(SCRIPTS); do \
		echo "Checking $$script..."; \
		bash -n $$script || exit 1; \
	done
	@echo "All scripts are valid!"

# Development helper: show package structure
show-structure:
	@echo "Package structure:"
	@echo ""
	@find . -type f -not -path './.git/*' -not -path './build/*' -not -path './dist/*' | sort
