# NetBird Synology DSM Package

A Synology DSM 7.0+ package (.spk) for the [NetBird](https://netbird.io/) VPN client. Provides full DSM integration: daemon lifecycle, firewall rules, CLI symlink, log rotation, and a basic web UI.

**Target architecture:** x86_64 (Intel/AMD — Plus series and above)

## Prerequisites

- A Synology NAS running **DSM 7.0** or later (x86_64)
- `curl`, `tar`, `make` (for building the package)
- Go 1.23+ (only if building from source)

## Quick Start (Pre-built Binary)

```bash
make download    # Download NetBird binary from GitHub releases
make package     # Build the .spk package
```

This produces `netbird-x86_64-<version>.spk` in the repo root.

## Building from Source

```bash
git clone https://github.com/netbirdio/netbird.git /path/to/netbird
make build NETBIRD_SRC=/path/to/netbird
make package
```

## Installing on Synology

1. Open **Package Center** on your Synology DSM
2. Go to **Settings > General > Trust Level** and select **Any publisher**
3. Go to **Manual Install** and upload the `.spk` file
4. The install wizard will prompt you for:
   - **Setup Key** — from your NetBird dashboard (required)
   - **Management URL** — defaults to `https://api.netbird.io:443` (change for self-hosted)
5. The package will start automatically and connect using your setup key

> **Note:** This package runs as root, which is required for sideloaded packages that need network administration privileges (TUN device, routes, firewall). Packages distributed through the official Synology Package Center can use fine-grained capabilities instead, but sideloaded `.spk` files do not support this.

## Configuration

### Via DSM Web UI

Click the **NetBird** icon in the DSM desktop to open the status page. From there you can:
- View connection status, NetBird IP, and connected peers
- Enter a new **setup key** and **management URL** to connect
- **Disconnect** from the network

### Via SSH (CLI)

The CLI is available at `/usr/local/bin/netbird` (symlinked automatically).

```bash
# Connect using a setup key
netbird up --setup-key YOUR_SETUP_KEY

# Connect to a self-hosted management server
netbird up --setup-key YOUR_KEY --management-url https://your-server:443

# Check status
netbird status

# Disconnect
netbird down
```

### Upgrades

When upgrading the package, the wizard will optionally let you update your setup key and management URL. Leave the fields blank to keep your current configuration.

## Architecture

### How It Works

- NetBird runs as a daemon managed by DSM's Package Center (start/stop/status)
- Uses bundled **wireguard-go** for WireGuard tunnels (no kernel module needed)
- Attempts to load the **TUN kernel module** for best performance
- Falls back to **userspace routing** if TUN is unavailable
- Firewall rules are registered with DSM automatically (port 51820/udp)
- Log rotation is handled by DSM's syslog system

### DSM Integration

| Feature | Implementation |
|---------|---------------|
| Daemon lifecycle | `scripts/start-stop-status` (start/stop/status) |
| Firewall rules | `Netbird.sc` port config via `port-config` resource |
| CLI access | `/usr/local/bin/netbird` via `usr-local-linker` resource |
| Log rotation | `logrotate.conf` via `syslog-config` resource |
| Web UI | CGI status/settings page in DSM desktop |
| Install wizard | Setup key and management URL prompted on install |
| Privileges | Runs as root (required for sideloaded packages) |

## File Locations

| File | Path on DSM |
|------|-------------|
| Binary | `/var/packages/netbird/target/bin/netbird` |
| Config | `/var/packages/netbird/var/config.json` |
| Log | `/var/packages/netbird/var/netbird.log` |
| PID file | `/var/packages/netbird/var/netbird.pid` |
| CLI symlink | `/usr/local/bin/netbird` |

## Troubleshooting

### Package won't start

Check the log file:
```bash
cat /var/packages/netbird/var/netbird.log
```

### TUN device issues

NetBird needs a TUN device. The start script tries to load it automatically. If it fails, NetBird falls back to userspace routing (slightly slower but functional).

```bash
# Check if TUN module is loaded
lsmod | grep tun

# Manually load TUN
sudo modprobe tun
```

### "Requires root privileges" on install

This package must run as root for network administration (TUN device, routes). Go to **Package Center > Settings > General > Trust Level** and select **Any publisher**, then retry the install.

### Permission denied

The package runs as root to manage network interfaces. If you still see permission errors, try restarting the package from Package Center.

### Firewall blocking connections

Ensure port **51820/udp** is allowed in DSM's firewall. The package registers this port automatically, but manual firewall rules may override it.

## SPK Structure

```
netbird-x86_64-<version>.spk
├── INFO                    # Package metadata
├── PACKAGE_ICON.PNG        # 64x64 icon
├── PACKAGE_ICON_256.PNG    # 256x256 icon
├── Netbird.sc              # Firewall/port config
├── WIZARD_UIFILES/
│   ├── install_uifile      # Install wizard (setup key, management URL)
│   └── upgrade_uifile      # Upgrade wizard (optional reconfigure)
├── conf/
│   ├── privilege           # Run-as-root config for sideloading
│   └── resource            # Resource workers (linker, ports, logs)
├── scripts/
│   ├── start-stop-status   # Daemon lifecycle
│   ├── preinst             # Pre-install
│   ├── postinst            # Post-install
│   ├── preuninst           # Pre-uninstall (runs netbird down)
│   ├── postuninst          # Post-uninstall
│   ├── preupgrade          # Pre-upgrade (runs netbird down)
│   └── postupgrade         # Post-upgrade
└── package.tgz             # Inner tarball
    ├── bin/netbird         # NetBird binary
    ├── conf/
    │   ├── Netbird.sc      # Port config
    │   └── logrotate.conf  # Log rotation
    └── ui/
        ├── config          # DSM desktop app config
        ├── index.cgi       # CGI status page
        └── PACKAGE_ICON_256.PNG
```

## Development

Edit files in `spk/` and rebuild:
```bash
make clean
make download   # or: make build NETBIRD_SRC=/path/to/netbird
make package
```

To change the version, edit the `VERSION` file.

## License

This packaging is provided as-is for the NetBird community. NetBird itself is licensed under the [BSD 3-Clause License](https://github.com/netbirdio/netbird/blob/main/LICENSE).
