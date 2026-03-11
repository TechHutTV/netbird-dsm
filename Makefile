# NetBird Synology DSM Package Builder
# Usage:
#   make download && make package   # Download pre-built binary and build SPK
#   make build && make package      # Build from source and build SPK
#   make clean                      # Remove build artifacts

VERSION := $(shell cat VERSION)
ARCH := x86_64
SPK_NAME := netbird-$(ARCH)-$(VERSION).spk

# For building from source (optional)
NETBIRD_SRC ?= .
GOFLAGS := CGO_ENABLED=0 GOOS=linux GOARCH=amd64

# GitHub release URL for downloading pre-built binary
RELEASE_URL := https://github.com/netbirdio/netbird/releases/download/v$(VERSION)/netbird_$(VERSION)_linux_amd64.tar.gz

# Directories
SPK_DIR := spk
PKG_DIR := $(SPK_DIR)/package
BIN_DIR := $(PKG_DIR)/bin
BUILD_DIR := build

.PHONY: all build download package clean check-binary

all: package

# Download pre-built NetBird binary from GitHub releases
download:
	@echo "Downloading NetBird v$(VERSION) for linux/amd64..."
	@mkdir -p $(BIN_DIR) $(BUILD_DIR)
	curl -fSL "$(RELEASE_URL)" -o $(BUILD_DIR)/netbird.tar.gz
	tar -xzf $(BUILD_DIR)/netbird.tar.gz -C $(BUILD_DIR)/
	cp $(BUILD_DIR)/netbird $(BIN_DIR)/netbird
	chmod +x $(BIN_DIR)/netbird
	@echo "Binary downloaded to $(BIN_DIR)/netbird"

# Build NetBird from source (requires Go 1.23+ and NetBird source)
build:
	@echo "Building NetBird v$(VERSION) from source..."
	@mkdir -p $(BIN_DIR)
	cd $(NETBIRD_SRC) && $(GOFLAGS) go build \
		-ldflags "-s -w -X github.com/netbirdio/netbird/version.version=$(VERSION)" \
		-o $(abspath $(BIN_DIR))/netbird \
		./client/
	@echo "Binary built at $(BIN_DIR)/netbird"

# Verify binary exists before packaging
check-binary:
	@test -f $(BIN_DIR)/netbird || { echo "Error: $(BIN_DIR)/netbird not found. Run 'make download' or 'make build' first."; exit 1; }

# Build the SPK package
package: check-binary
	@echo "Building SPK package..."
	@mkdir -p $(BUILD_DIR)

	# Create package.tgz from package/ contents
	@echo "Creating package.tgz..."
	cd $(PKG_DIR) && tar -czf ../../$(BUILD_DIR)/package.tgz --owner=0 --group=0 *

	# Calculate extract size (KB)
	$(eval EXTRACTSIZE := $(shell du -sk $(PKG_DIR) | cut -f1))

	# Generate INFO file
	@echo "Generating INFO..."
	sh $(SPK_DIR)/INFO.sh "$(VERSION)" "$(EXTRACTSIZE)" > $(BUILD_DIR)/INFO

	# Assemble SPK
	@echo "Assembling SPK..."
	@mkdir -p $(BUILD_DIR)/spk_staging
	cp $(BUILD_DIR)/INFO $(BUILD_DIR)/spk_staging/INFO
	cp $(BUILD_DIR)/package.tgz $(BUILD_DIR)/spk_staging/package.tgz
	cp $(SPK_DIR)/PACKAGE_ICON.PNG $(BUILD_DIR)/spk_staging/PACKAGE_ICON.PNG
	cp $(SPK_DIR)/PACKAGE_ICON_256.PNG $(BUILD_DIR)/spk_staging/PACKAGE_ICON_256.PNG
	cp $(SPK_DIR)/Netbird.sc $(BUILD_DIR)/spk_staging/Netbird.sc
	cp -r $(SPK_DIR)/scripts $(BUILD_DIR)/spk_staging/scripts
	cp -r $(SPK_DIR)/conf $(BUILD_DIR)/spk_staging/conf
	cp -r $(SPK_DIR)/WIZARD_UIFILES $(BUILD_DIR)/spk_staging/WIZARD_UIFILES

	cd $(BUILD_DIR)/spk_staging && tar -cf ../../$(SPK_NAME) --owner=0 --group=0 *

	@rm -rf $(BUILD_DIR)/spk_staging
	@echo ""
	@echo "SPK package built: $(SPK_NAME)"
	@echo "  Version:  $(VERSION)"
	@echo "  Arch:     $(ARCH)"
	@echo "  Size:     $$(du -sh $(SPK_NAME) | cut -f1)"

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(BIN_DIR)/netbird
	rm -f $(SPK_DIR)/INFO
	rm -f *.spk

help:
	@echo "NetBird Synology DSM Package Builder"
	@echo ""
	@echo "Targets:"
	@echo "  download  - Download pre-built NetBird binary from GitHub releases"
	@echo "  build     - Build NetBird from source (requires Go 1.23+)"
	@echo "  package   - Assemble the SPK package (run download or build first)"
	@echo "  clean     - Remove build artifacts"
	@echo "  help      - Show this help"
	@echo ""
	@echo "Quick start:"
	@echo "  make download && make package"
	@echo ""
	@echo "Variables:"
	@echo "  NETBIRD_SRC  - Path to NetBird source (default: .)"
	@echo "  VERSION      - Package version (default: from VERSION file)"
