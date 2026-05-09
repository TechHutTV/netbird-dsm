# NetBird Synology DSM Package Builder
# Usage:
#   make download package VERSION=0.70.5                          # x86_64
#   make download package VERSION=0.70.5 SYNOLOGY_ARCH=aarch64    # aarch64
#   make build   package VERSION=0.70.5 NETBIRD_SRC=/path/to/src  # build from source
#   make clean                                                    # remove artifacts

# Architecture (defaults: x86_64 / amd64). NETBIRD_ARCH is auto-derived from
# SYNOLOGY_ARCH; override either explicitly if needed.
SYNOLOGY_ARCH ?= x86_64
ifeq ($(SYNOLOGY_ARCH),aarch64)
NETBIRD_ARCH ?= arm64
else
NETBIRD_ARCH ?= amd64
endif

SPK_NAME := netbird_$(VERSION)_synology_$(NETBIRD_ARCH).spk

# For building from source (optional)
NETBIRD_SRC ?= .
GOFLAGS := CGO_ENABLED=0 GOOS=linux GOARCH=$(NETBIRD_ARCH)

# GitHub release URL for downloading pre-built binary
RELEASE_URL := https://github.com/netbirdio/netbird/releases/download/v$(VERSION)/netbird_$(VERSION)_linux_$(NETBIRD_ARCH).tar.gz

# Directories
SPK_DIR := spk
PKG_DIR := $(SPK_DIR)/package
BIN_DIR := $(PKG_DIR)/bin
BUILD_DIR := build
WRAPPER_SRC := $(SPK_DIR)/wrapper/netbird

.PHONY: all build download package clean check-binary check-version

all: package

# Verify VERSION is set before targets that need it
check-version:
	@test -n "$(VERSION)" || { \
		echo "ERROR: VERSION is required."; \
		echo "Example: make download package VERSION=0.70.5"; \
		exit 1; \
	}

# Download pre-built NetBird binary from GitHub releases
download: check-version
	@echo "Downloading NetBird v$(VERSION) for linux/$(NETBIRD_ARCH)..."
	@mkdir -p $(BIN_DIR) $(BUILD_DIR)
	curl -fSL "$(RELEASE_URL)" -o $(BUILD_DIR)/netbird.tar.gz
	tar -xzf $(BUILD_DIR)/netbird.tar.gz -C $(BUILD_DIR)/
	cp $(BUILD_DIR)/netbird $(BIN_DIR)/netbird.bin
	chmod +x $(BIN_DIR)/netbird.bin
	@echo "Binary downloaded to $(BIN_DIR)/netbird.bin"

# Build NetBird from source (requires Go 1.23+ and NetBird source)
build: check-version
	@echo "Building NetBird v$(VERSION) from source..."
	@mkdir -p $(BIN_DIR)
	cd $(NETBIRD_SRC) && $(GOFLAGS) go build \
		-ldflags "-s -w -X github.com/netbirdio/netbird/version.version=$(VERSION)" \
		-o $(abspath $(BIN_DIR))/netbird.bin \
		./client/
	@echo "Binary built at $(BIN_DIR)/netbird.bin"

# Verify binary exists before packaging
check-binary:
	@test -f $(BIN_DIR)/netbird.bin || { echo "Error: $(BIN_DIR)/netbird.bin not found. Run 'make download' or 'make build' first."; exit 1; }

# Build the SPK package
package: check-version check-binary
	@echo "Building SPK package..."
	@mkdir -p $(BUILD_DIR)

	# Stage the CLI wrapper alongside the binary so usr-local-linker symlinks it
	@echo "Staging CLI wrapper..."
	cp $(WRAPPER_SRC) $(BIN_DIR)/netbird
	chmod +x $(BIN_DIR)/netbird

	# Create package.tgz from package/ contents
	@echo "Creating package.tgz..."
	cd $(PKG_DIR) && tar -czf ../../$(BUILD_DIR)/package.tgz --owner=0 --group=0 *

	# Calculate extract size (KB)
	$(eval EXTRACTSIZE := $(shell du -sk $(PKG_DIR) | cut -f1))

	# Generate INFO file
	@echo "Generating INFO..."
	sh $(SPK_DIR)/INFO.sh "$(VERSION)" "$(EXTRACTSIZE)" "$(SYNOLOGY_ARCH)" > $(BUILD_DIR)/INFO

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

	cd $(BUILD_DIR)/spk_staging && tar -cf ../../$(SPK_NAME) --owner=0 --group=0 *

	@rm -rf $(BUILD_DIR)/spk_staging
	@echo ""
	@echo "SPK package built: $(SPK_NAME)"
	@echo "  Version:  $(VERSION)"
	@echo "  Arch:     $(SYNOLOGY_ARCH) (netbird: $(NETBIRD_ARCH))"
	@echo "  Size:     $$(du -sh $(SPK_NAME) | cut -f1)"

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(BIN_DIR)/netbird $(BIN_DIR)/netbird.bin
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
	@echo "  make download package VERSION=0.70.5"
	@echo ""
	@echo "Variables:"
	@echo "  VERSION        - NetBird upstream version (REQUIRED, e.g. 0.70.5)"
	@echo "  SYNOLOGY_ARCH  - Synology arch token (default: x86_64; e.g. aarch64)"
	@echo "  NETBIRD_ARCH   - NetBird arch token (auto from SYNOLOGY_ARCH; amd64/arm64)"
	@echo "  NETBIRD_SRC    - Path to NetBird source for 'make build' (default: .)"
