# NetBird Synology DSM Package

A Synology DSM 7.0+ package (.spk) for the [NetBird](https://netbird.io/) VPN client. Provides DSM integration for daemon lifecycle, firewall rules, CLI symlink, log rotation, and a read-only status page in DSM's AppPortal. **Configuration is CLI-only** — after installing, SSH into the NAS and use the `netbird` command to connect.

**Supported architectures:** `x86_64` (Intel/AMD — Plus series and above) and `aarch64` (64-bit ARM Synologies, e.g. DS220j-class and newer Realtek/Marvell ARM models).

> ### ⚠️ Testing / beta fork
>
> This repository is a **testing fork** used to validate the build, packaging, and update-delivery pipeline before any of it lands in an official NetBird-maintained channel. The Package Source URL below points at this fork's GitHub Pages deployment. See [Testing & Validation](#testing--validation) below for what's been verified, what hasn't, and how to report issues.

## Prerequisites

- A Synology NAS running **DSM 7.0** or later (x86_64 or aarch64)
- `curl`, `tar`, `make` (for building the package)
- Go 1.23+ (only if building from source)

## Quick Start (Pre-built Binary)

Substitute `<version>` with a NetBird release tag (without the leading `v`) — see [NetBird releases](https://github.com/netbirdio/netbird/releases).

```bash
# x86_64 (Intel/AMD — default)
make download package VERSION=<version>

# aarch64 (ARM64 Synology models)
make download package VERSION=<version> SYNOLOGY_ARCH=aarch64
```

This produces `netbird_<version>_synology_<amd64|arm64>.spk` in the repo root.

## Building from Source

```bash
git clone https://github.com/netbirdio/netbird.git /path/to/netbird

# x86_64
make build package VERSION=<version> NETBIRD_SRC=/path/to/netbird

# aarch64
make build package VERSION=<version> NETBIRD_SRC=/path/to/netbird SYNOLOGY_ARCH=aarch64
```

## Installing on Synology

### Option A — Package Source (recommended, gets automatic updates)

1. Open **Package Center** on your Synology DSM
2. Go to **Settings > General > Trust Level** and select **Any publisher**
3. Go to **Settings > Package Sources**, click **Add**, give it any name, and set Location to:
   ```
   https://techhuttv.github.io/netbird-dsm/index.json
   ```
4. Open the **Community** tab — NetBird will appear there. Click **Install**.
5. SSH into the NAS and connect via CLI (see below).

DSM will offer updates automatically when a new version is published.

### Option B — Manual install (single .spk file)

1. Open **Package Center** on your Synology DSM
2. Go to **Settings > General > Trust Level** and select **Any publisher**
3. Go to **Manual Install** and upload the `.spk` file
4. The package will install and start the daemon. It will not be connected yet.
5. SSH into the NAS and connect via CLI (see below).

> **Note:** This package runs as the unprivileged `netbird` user using NetBird's userspace networking (netstack mode), so no kernel TUN device or root access is required. The "Any publisher" trust level is needed because sideloaded `.spk` files aren't signed by Synology — it has nothing to do with privileges.

## Configuration (CLI only)

The DSM AppPortal page is read-only — there's no install wizard and no in-browser controls for connecting, disconnecting, or changing settings. SSH into the NAS and use the `netbird` CLI, which is symlinked to `/usr/local/bin/netbird`.

```bash
# Connect using a setup key
sudo netbird up --setup-key YOUR_SETUP_KEY

# Connect to a self-hosted management server
sudo netbird up --setup-key YOUR_KEY --management-url https://your-server:443

# Check status
sudo netbird status

# Disconnect
sudo netbird down
```

### Upgrades

Upgrading the package preserves your existing configuration — the daemon restarts and reconnects automatically using the keys it already has. No reconfiguration needed.

## Status Page (DSM AppPortal)

After install the package registers a NetBird entry in DSM's **Main Menu** that opens a read-only status page. By default it's restricted to DSM administrators — to grant access to other users go to **Control Panel → Application Privileges → NetBird** and add the desired users or groups.

The page shows:

- **Header line** — colored status dot + the connection state (`Connected` / `Not Configured` / `Disconnected`) and FQDN when enrolled
- **Information card** — Domain Name, NetBird IP, Peers Connected, Relays, Exit Node, Agent Version, Profile (sourced from `netbird status`)
- **Recent Activity** — collapsible tail of the daemon log with INFO/WARN/ERROR colorization
- **Open Docs** — links to the NetBird Synology install guide
- **Open Dashboard** — opens the management dashboard for this peer (uses `AdminURL` from `config.json`, so self-hosted deployments link to their own panel)

The page auto-refreshes every 10 seconds. It's strictly read-only — install/connect/disconnect still happens via the CLI.

## Architecture

### How It Works

- NetBird runs as a daemon managed by DSM's Package Center (start/stop/status)
- Uses bundled **wireguard-go** in **netstack mode** — fully userspace networking, no kernel WireGuard or TUN device required
- The start script still tries to load the TUN module so the route table can be reused if available; otherwise `NB_FORCE_USERSPACE_ROUTER=true` is set automatically
- Firewall rules are registered with DSM automatically (port 51820/udp)
- Log rotation is handled by DSM's syslog system
- Status page is served by DSM's web framework via the `dsmuidir` resource — DSM handles auth, sessions, and TLS

### DSM Integration

| Feature | Implementation |
|---------|---------------|
| Daemon lifecycle | `scripts/start-stop-status` (start/stop/status) |
| Firewall rules | `Netbird.sc` port config via `port-config` resource |
| CLI access | `/usr/local/bin/netbird` via `usr-local-linker` resource |
| Log rotation | `logrotate.conf` via `syslog-config` resource |
| Status page | `ui/index.cgi` via `dsmuidir` (DSM AppPortal, admin-only) |
| Privileges | Runs as unprivileged `netbird` package user (userspace networking, no root) |

## File Locations

| File | Path on DSM |
|------|-------------|
| Binary | `/var/packages/netbird/target/bin/netbird.bin` |
| CLI wrapper | `/var/packages/netbird/target/bin/netbird` (sets `NB_DAEMON_ADDR`, execs the binary) |
| CLI symlink | `/usr/local/bin/netbird` → wrapper |
| Status page CGI | `/var/packages/netbird/target/ui/index.cgi` |
| AppPortal URL | `https://<nas>:5001/webman/3rdparty/netbird/index.cgi` (behind DSM auth) |
| Config | `/var/packages/netbird/var/config.json` |
| Daemon socket | `/var/packages/netbird/var/netbird.sock` |
| Log | `/var/packages/netbird/var/netbird.log` |
| PID file | `/var/packages/netbird/var/netbird.pid` |

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

### Install blocked by trust level

Sideloaded packages aren't signed by Synology. Go to **Package Center > Settings > General > Trust Level** and select **Any publisher**, then retry the install.

### Permission denied

The package runs as the unprivileged `netbird` user, and all writable state lives under `/var/packages/netbird/var`. If you see permission errors, restart the package from Package Center.

### Firewall blocking connections

Ensure port **51820/udp** is allowed in DSM's firewall. The package registers this port automatically, but manual firewall rules may override it.

### Start fresh (clean reset)

To wipe all NetBird state (keys, peer config, profile data) and re-enroll the device, stop the package, clear the var directory, then start it again:

```bash
sudo synopkg stop netbird
sudo rm -rf /var/packages/netbird/var/*
sudo synopkg start netbird
sudo netbird up --setup-key YOUR_SETUP_KEY
```

All NetBird state lives under `/var/packages/netbird/var` — nothing escapes to `/etc` or other system locations, so this is a complete reset.

## SPK Structure

```
netbird_<version>_synology_<amd64|arm64>.spk
├── INFO                    # Package metadata
├── PACKAGE_ICON.PNG        # 64x64 icon
├── PACKAGE_ICON_256.PNG    # 256x256 icon
├── Netbird.sc              # Firewall/port config
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
    ├── bin/
    │   ├── netbird         # CLI wrapper (symlinked to /usr/local/bin/netbird)
    │   └── netbird.bin     # NetBird binary
    ├── conf/
    │   ├── Netbird.sc      # Port config
    │   └── logrotate.conf  # Log rotation
    └── ui/                 # DSM AppPortal status page (admin-only)
        ├── config          # AppPortal manifest (allUsers:false, grantPrivilege:local)
        ├── index.cgi       # Read-only status page (shell CGI)
        └── images/         # Multi-size launcher icons (16, 24, 32, 48, 64, 72, 96, 256 px)
```

## Development

Edit files in `spk/` and rebuild:
```bash
make clean
make download package VERSION=<version>                          # x86_64
make download package VERSION=<version> SYNOLOGY_ARCH=aarch64    # aarch64
```

Build variables:

| Variable        | Default          | Notes                                                       |
|-----------------|------------------|-------------------------------------------------------------|
| `VERSION`       | _required_       | NetBird upstream version (e.g. `0.70.5`)                    |
| `SYNOLOGY_ARCH` | `x86_64`         | Synology arch token written into INFO. Also accepts `aarch64`. |
| `NETBIRD_ARCH`  | auto from above  | NetBird release arch (`amd64`/`arm64`). Override only if needed. |
| `NETBIRD_SRC`   | `.`              | Path to NetBird source (only for `make build`)              |

## Testing & Validation

This is a **testing / beta fork**, not the official NetBird-maintained DSM channel. It exists to validate the build, packaging, and update-delivery pipeline before any of it ships through `netbirdio/*`.

### What's being validated

- **Build pipeline** — single GitHub Actions run produces both `x86_64` and `aarch64` SPKs via a matrix workflow, attaches both to a Release, and refreshes the package source catalog on GitHub Pages.
- **DSM Package Source flow** — confirming the static catalog at `https://techhuttv.github.io/netbird-dsm/index.json` is recognized by DSM and surfaces NetBird in **Package Center → Community** with working auto-update.
- **Multi-arch catalog behavior** — a single `index.json` lists one entry per arch with the `arch` field set, relying on DSM to pick the matching one client-side.

### Known untested areas

- **aarch64 on real ARM Synology hardware.** The aarch64 SPK is structurally correct (DSM accepts and installs it), but the bundled NetBird binary has not been runtime-tested on an actual ARM Synology model. If you run on one, please file an issue with results.
- **Multi-entry catalog filtering on DSM.** If DSM ends up showing duplicate NetBird entries instead of picking the matching arch, the fallback is to switch to per-arch URL paths (`/x86_64/index.json`, `/aarch64/index.json`).
- **Update-detection latency.** DSM polls package sources on its own cadence; "should have updated by now" thresholds are still being characterized.

### Reporting feedback

File issues at <https://github.com/TechHutTV/netbird-dsm/issues>. Useful context to include:

- DSM version (`Control Panel → Info Center`)
- NAS model and CPU arch
- Whether you installed via Package Source or Manual Install
- Relevant log excerpt: `cat /var/packages/netbird/var/netbird.log`

## License

This packaging is provided as-is for the NetBird community. NetBird itself is licensed under the [BSD 3-Clause License](https://github.com/netbirdio/netbird/blob/main/LICENSE).
