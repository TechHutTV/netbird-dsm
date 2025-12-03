# NetBird DSM Package

A Synology DSM 7.0+ package for [NetBird](https://netbird.io/) - a WireGuard-based mesh network that connects your devices into a secure private network.

## Features

- **Easy Installation**: Install NetBird directly from the Synology Package Center
- **Configuration Wizard**: Set up your management URL and setup key during installation
- **Web-based Settings**: Configure NetBird through the DSM web interface
- **Service Management**: Start, stop, and monitor NetBird through DSM
- **Auto-start**: NetBird automatically starts when your NAS boots
- **Multi-architecture**: Supports x86_64, ARM64, and ARMv7 Synology devices

## Requirements

- Synology DSM 7.0 or later
- TUN device support (standard on most Synology devices)
- Network access to NetBird management server (default: api.netbird.io)

## Installation

### Method 1: Manual Installation (SPK File)

1. Download the `.spk` file from the [Releases](https://github.com/TechHutTV/netbird-dsm/releases) page
2. Open Synology DSM and go to **Package Center**
3. Click **Manual Install** and select the downloaded `.spk` file
4. Follow the installation wizard to configure:
   - **Management URL**: Your NetBird management server (default for NetBird Cloud)
   - **Setup Key**: Your setup key from the NetBird dashboard
5. Complete the installation

### Method 2: Build from Source

See the [Building](#building) section below.

## Configuration

### During Installation

The installation wizard prompts for:
- **Management URL**: The NetBird management server URL
  - Default: `https://api.netbird.io:443` (NetBird Cloud)
  - For self-hosted: Enter your management server URL
- **Setup Key**: Obtained from your NetBird dashboard under Setup Keys

### After Installation

1. Open the **NetBird** app from the DSM main menu
2. Update settings as needed:
   - Management URL
   - Setup Key
3. Use the **Save & Connect** button to apply changes and connect to your network

### Command Line

SSH into your Synology and use the NetBird CLI:

```bash
# Check status
/var/packages/netbird/target/bin/netbird status

# Connect with a setup key
/var/packages/netbird/target/bin/netbird up --setup-key YOUR_SETUP_KEY

# Disconnect
/var/packages/netbird/target/bin/netbird down
```

## Building

### Prerequisites

Choose one of the following methods:

#### Option A: Using Synology Toolkit (Recommended for Production)

1. Set up the [Synology Package Toolkit](https://help.synology.com/developer-guide/getting_started/toolkit_setup.html)
2. Clone this repository into the toolkit's source directory
3. Build with PkgCreate.py

#### Option B: Simple Build (Development/Testing)

Requirements:
- Bash shell
- tar
- (Optional) ImageMagick for icon generation

### Build Steps

#### Simple Build (without Synology Toolkit)

```bash
# Clone the repository
git clone https://github.com/TechHutTV/netbird-dsm.git
cd netbird-dsm

# Generate icons (optional, requires ImageMagick)
./icons/create_icons.sh

# Build the SPK package
make

# The SPK file will be created in dist/
ls -la dist/netbird-*.spk
```

#### Using Synology Toolkit

```bash
# Clone pkgscripts-ng
git clone https://github.com/SynologyOpenSource/pkgscripts-ng.git
cd pkgscripts-ng

# Deploy build environment for DSM 7.0 (example: x86_64)
./EnvDeploy -v 7.0 -p x64

# Clone this repository
git clone https://github.com/TechHutTV/netbird-dsm.git /toolkit/source/netbird

# Build the package
./PkgCreate.py -v 7.0 -p x64 -c netbird

# Find the SPK in result_spk/
ls -la /toolkit/result_spk/netbird-*/
```

### Build Output

The build process creates:
- `dist/netbird-{version}.spk` - The installable Synology package

### Package Structure

```
netbird-dsm/
├── INFO.sh                    # Package metadata
├── Makefile                   # Build system
├── SynoBuildConf/             # Synology toolkit configuration
│   ├── build                  # Build script
│   ├── depends                # Dependencies
│   └── install                # Install script
├── conf/                      # Package configuration
│   ├── privilege              # Privilege settings (run as root)
│   ├── resource               # Resource declarations
│   └── netbird.sc             # Firewall port configuration
├── scripts/                   # Lifecycle scripts
│   ├── preinst                # Pre-installation
│   ├── postinst               # Post-installation (downloads binary)
│   ├── preuninst              # Pre-uninstallation
│   ├── postuninst             # Post-uninstallation
│   ├── preupgrade             # Pre-upgrade (backup config)
│   ├── postupgrade            # Post-upgrade (restore config)
│   └── start-stop-status      # Service control
├── WIZARD_UIFILES/            # Installation wizard
│   ├── install_uifile         # Install wizard configuration
│   └── uninstall_uifile       # Uninstall wizard configuration
├── ui/                        # Web interface
│   ├── config                 # DSM app configuration
│   ├── index.cgi              # Settings web page
│   └── images/                # UI icons
└── icons/                     # Package icons
    ├── create_icons.sh        # Icon generation script
    ├── PACKAGE_ICON.PNG       # 64x64 package icon
    └── PACKAGE_ICON_256.PNG   # 256x256 package icon
```

## How It Works

1. **Installation**: The package downloads the appropriate NetBird binary for your system architecture during installation
2. **Service**: NetBird runs as a background service managed by DSM
3. **Configuration**: Settings are stored in `/var/packages/netbird/target/etc/`
4. **Logs**: Service logs are written to `/var/packages/netbird/target/var/netbird.log`

## Troubleshooting

### NetBird won't connect

1. Verify your setup key is correct and not expired
2. Check the management URL is accessible from your NAS
3. Review logs: `cat /var/packages/netbird/target/var/netbird.log`

### Service won't start

1. Check if TUN device is available: `ls -la /dev/net/tun`
2. Review package logs: `cat /var/log/packages/netbird.log`
3. Try restarting: Go to Package Center → NetBird → Action → Restart

### Package won't install

1. Ensure DSM 7.0 or later is installed
2. Check available disk space
3. Verify your NAS architecture is supported (x86_64, ARM64, ARMv7)

## Uninstallation

1. Go to **Package Center** → **Installed**
2. Find **NetBird** and click **Uninstall**
3. Choose whether to remove configuration files

## Development

### Making Changes

1. Fork this repository
2. Make your changes
3. Test with `make validate` to check script syntax
4. Build with `make`
5. Test the SPK on a Synology device or VM

### Code Style

- Shell scripts use `/bin/bash`
- Follow Synology's [Package Developer Guide](https://help.synology.com/developer-guide/)
- Use meaningful variable names and comments

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

NetBird is a separate project with its own license. See [netbird.io](https://netbird.io/) for more information.

## Resources

### Synology Development
- [Synology Package Developer Guide](https://help.synology.com/developer-guide/getting_started/first_package.html)
- [Example Packages](https://github.com/SynologyOpenSource/ExamplePackages)
- [Package Toolkit](https://help.synology.com/developer-guide/toolkit/toolkit.html)
- [Package Structure](https://help.synology.com/developer-guide/synology_package/introduction.html)
- [Compile Examples](https://help.synology.com/developer-guide/examples/compile_nmap.html)

### NetBird
- [NetBird Documentation](https://docs.netbird.io/)
- [NetBird GitHub](https://github.com/netbirdio/netbird)
- [NetBird Releases](https://github.com/netbirdio/netbird/releases)

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Acknowledgments

- [NetBird](https://netbird.io/) for the excellent mesh networking solution
- [Synology](https://www.synology.com/) for the DSM platform and developer tools
- [SynoCommunity](https://synocommunity.com/) for package development references
