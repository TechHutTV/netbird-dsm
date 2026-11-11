# NetBird Synology DSM Package Builder
# Usage:
#   make download package                                      # x86_64, pinned VERSION
#   make download package SYNOLOGY_ARCH=aarch64                 # aarch64
#   make build package NETBIRD_SRC=/path/to/src                 # build from source
#   make clean                                                 # remove artifacts

# VERSION always selects the upstream binary. Package revisions are separate.
VERSION ?= $(shell cat VERSION)
PACKAGE_VERSION ?= $(VERSION)-0
CHECKSUMS_FILE ?= SHA256SUMS
TAR ?= tar

# Architecture (defaults: x86_64 / amd64). NETBIRD_ARCH is auto-derived from
# SYNOLOGY_ARCH; override either explicitly if needed.
SYNOLOGY_ARCH ?= x86_64
ifeq ($(SYNOLOGY_ARCH),aarch64)
NETBIRD_ARCH ?= arm64
else
NETBIRD_ARCH ?= amd64
endif

SPK_NAME := netbird_$(PACKAGE_VERSION)_synology_$(NETBIRD_ARCH).spk

# For building from source (optional)
NETBIRD_SRC ?= .
GOFLAGS := CGO_ENABLED=0 GOOS=linux GOARCH=$(NETBIRD_ARCH)

# GitHub release URL for downloading pre-built binary
RELEASE_URL := https://github.com/netbirdio/netbird/releases/download/v$(VERSION)/netbird_$(VERSION)_linux_$(NETBIRD_ARCH).tar.gz
RELEASE_FILE := netbird_$(VERSION)_linux_$(NETBIRD_ARCH).tar.gz

# Directories
SPK_DIR := spk
PKG_DIR := $(SPK_DIR)/package
BIN_DIR := $(PKG_DIR)/bin
BUILD_DIR := build
WRAPPER_SRC := $(SPK_DIR)/wrapper/netbird

.PHONY: all build download package clean check-binary check-version check-package-version test help

all: package

check-version:
	@python3 -B scripts/version.py check --upstream "$(VERSION)"
	@case "$(SYNOLOGY_ARCH):$(NETBIRD_ARCH)" in x86_64:amd64|aarch64:arm64) ;; *) echo "ERROR: architecture must be x86_64:amd64 or aarch64:arm64"; exit 1;; esac

check-package-version: check-version
	@python3 -B scripts/version.py check --upstream "$(VERSION)" --package "$(PACKAGE_VERSION)"

# Download pre-built NetBird binary from GitHub releases
download: check-version
	@echo "Downloading NetBird v$(VERSION) for linux/$(NETBIRD_ARCH)..."
	@mkdir -p $(BIN_DIR) $(BUILD_DIR)
	@awk '$$2 == "$(RELEASE_FILE)" { print }' "$(CHECKSUMS_FILE)" > $(BUILD_DIR)/netbird.checksum
	@test -s $(BUILD_DIR)/netbird.checksum || { echo "ERROR: no pinned checksum for $(RELEASE_FILE) in $(CHECKSUMS_FILE)"; exit 1; }
	curl -fSL "$(RELEASE_URL)" -o "$(BUILD_DIR)/$(RELEASE_FILE)"
	cd $(BUILD_DIR) && shasum -a 256 -c netbird.checksum
	$(TAR) -xzf "$(BUILD_DIR)/$(RELEASE_FILE)" -C $(BUILD_DIR)/ netbird
	cp $(BUILD_DIR)/netbird $(BIN_DIR)/netbird.bin
	chmod +x $(BIN_DIR)/netbird.bin
	@printf '%s\n' "$(VERSION) linux/$(NETBIRD_ARCH)" > $(BUILD_DIR)/binary-version
	@echo "Binary downloaded to $(BIN_DIR)/netbird.bin"

# Build NetBird from source (requires the toolchain in upstream's go.mod)
build: check-version
	@echo "Building NetBird v$(VERSION) from source..."
	@mkdir -p $(BIN_DIR) $(BUILD_DIR)
	cd $(NETBIRD_SRC) && $(GOFLAGS) go build \
		-ldflags "-s -w -X github.com/netbirdio/netbird/version.version=$(VERSION)" \
		-o $(abspath $(BIN_DIR))/netbird.bin \
		./client/
	@printf '%s\n' "$(VERSION) linux/$(NETBIRD_ARCH)" > $(BUILD_DIR)/binary-version
	@echo "Binary built at $(BIN_DIR)/netbird.bin"

# Verify binary exists before packaging
check-binary:
	@test -f $(BIN_DIR)/netbird.bin || { echo "Error: $(BIN_DIR)/netbird.bin not found. Run 'make download' or 'make build' first."; exit 1; }
	@test "$$(cat $(BUILD_DIR)/binary-version 2>/dev/null)" = "$(VERSION) linux/$(NETBIRD_ARCH)" || { echo "ERROR: binary version/architecture differs; run 'make download' or 'make build' again."; exit 1; }

# Build the SPK package
package: check-package-version check-binary
	@echo "Building SPK package..."
	@mkdir -p $(BUILD_DIR)

	# Stage the CLI wrapper alongside the binary so usr-local-linker symlinks it
	@echo "Staging CLI wrapper..."
	cp $(WRAPPER_SRC) $(BIN_DIR)/netbird
	chmod +x $(BIN_DIR)/netbird

	# Create package.tgz from package/ contents
	@echo "Creating package.tgz..."
	cd $(PKG_DIR) && $(TAR) -czf ../../$(BUILD_DIR)/package.tgz --owner=0 --group=0 *

	# Calculate extract size (KB)
	$(eval EXTRACTSIZE := $(shell du -sk $(PKG_DIR) | cut -f1))

	# Generate INFO file
	@echo "Generating INFO..."
	sh $(SPK_DIR)/INFO.sh "$(PACKAGE_VERSION)" "$(EXTRACTSIZE)" "$(SYNOLOGY_ARCH)" > $(BUILD_DIR)/INFO

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

	cd $(BUILD_DIR)/spk_staging && $(TAR) -cf ../../$(SPK_NAME) --owner=0 --group=0 *

	@rm -rf $(BUILD_DIR)/spk_staging
	@echo ""
	@echo "SPK package built: $(SPK_NAME)"
	@echo "  Version:  $(PACKAGE_VERSION) (NetBird $(VERSION))"
	@echo "  Arch:     $(SYNOLOGY_ARCH) (netbird: $(NETBIRD_ARCH))"
	@echo "  Size:     $$(du -sh $(SPK_NAME) | cut -f1)"

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(BIN_DIR)/netbird $(BIN_DIR)/netbird.bin
	rm -f $(SPK_DIR)/INFO
	rm -f *.spk

test:
	python3 -B -m unittest discover -s tests -v

help:
	@echo "NetBird Synology DSM Package Builder"
	@echo ""
	@echo "Targets:"
	@echo "  download  - Download pre-built NetBird binary from GitHub releases"
	@echo "  build     - Build NetBird from source (requires upstream's Go toolchain)"
	@echo "  package   - Assemble the SPK package (run download or build first)"
	@echo "  clean     - Remove build artifacts"
	@echo "  test      - Check service networking and status CGI (requires Python 3 and jq >= 1.5)"
	@echo "  help      - Show this help"
	@echo ""
	@echo "Quick start:"
	@echo "  make download package"
	@echo ""
	@echo "Variables:"
	@echo "  VERSION        - NetBird version (default: VERSION file; currently $(VERSION))"
	@echo "  PACKAGE_VERSION - DSM version (default: $(PACKAGE_VERSION); revision 0 is for development)"
	@echo "  CHECKSUMS_FILE - Pinned upstream archive checksums (default: SHA256SUMS)"
	@echo "  TAR            - GNU tar command (default: tar; use gtar on macOS)"
	@echo "  SYNOLOGY_ARCH  - Synology arch token (default: x86_64; e.g. aarch64)"
	@echo "  NETBIRD_ARCH   - NetBird arch token (auto from SYNOLOGY_ARCH; amd64/arm64)"
	@echo "  NETBIRD_SRC    - Path to NetBird source for 'make build' (default: .)"
