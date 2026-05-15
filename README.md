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

Pick the URL matching your NAS architecture:

| NAS architecture | Package Source URL |
|---|---|
| **x86_64** (Intel / AMD — DS918+, DS920+, DS923+, DS1522+, RS series, etc.) | `https://techhuttv.github.io/netbird-dsm/x86_64/index.json` |
| **aarch64** (64-bit ARM — DS220j, DS223j, DS124, DS418j, etc.) | `https://techhuttv.github.io/netbird-dsm/aarch64/index.json` |

> Not sure which? SSH into the NAS and run `synogetkeyvalue /etc.defaults/synoinfo.conf unique` — output is `synology_<arch>_<model>`. Tokens like `apollolake`, `geminilake`, `v1000`, `r1000`, `denverton`, `purley` → x86_64. Tokens like `armada37xx`, `rtd1296`, `rtd1619b` → aarch64.

1. Open **Package Center** on your Synology DSM
2. Go to **Settings > General > Trust Level** and select **Any publisher**
3. Go to **Settings > Package Sources**, click **Add**, give it any name, and paste the URL for your arch as the Location
4. Open the **Community** tab — NetBird will appear there. Click **Install**.
5. SSH into the NAS and connect via CLI (see below).

DSM will offer updates automatically when a new version is published.

### Option B — Manual install (single .spk file)

1. Open **Package Center** on your Synology DSM
2. Go to **Settings > General > Trust Level** and select **Any publisher**
3. Go to **Manual Install** and upload the `.spk` file
4. The package will install and start the daemon. It will not be connected yet.
5. SSH into the NAS and connect via CLI (see below).

> **Note:** This package runs as the unprivileged `netbird` package user with NetBird in **netstack mode** (userspace networking). DSM 7+ blocks third-party packages from running as root without a non-obvious user-flipped toggle, and `setcap` (which would let an unprivileged user create a kernel TUN) isn't available on most DSM builds — so a kernel TUN isn't reachable from this package. The "Any publisher" trust level is needed because sideloaded `.spk` files aren't signed by Synology; it has nothing to do with privileges.
>
> **Practical consequence:** the NAS is *not* directly reachable on its NetBird IP — `sshd`, DSM's web UI, and other host services bind to the kernel network stack, which doesn't see the netstack-only NetBird interface. See [Reaching the NAS over NetBird](#reaching-the-nas-over-netbird) below for workarounds.

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

### Reaching the NAS over NetBird

Because the daemon runs in **netstack mode** (see install Note above), DSM's host services — `sshd`, the web UI on `:5000`/`:5001`, SMB, etc. — are *not* directly reachable on the peer's NetBird IP from another peer. Outbound traffic from the NAS through the mesh works fine; what doesn't work out of the box is connecting *to* the NAS on `100.x.x.x` from elsewhere on the mesh.

Three workarounds, in order of how seamless they are:

- **Advertise the NAS's LAN as a network route, with the NAS itself as the routing peer.** This is the recommended option: the NAS sits in netstack mode, but it can still *forward* TCP and UDP from the mesh to anything on its LAN — including itself, at its LAN IP. In the NetBird dashboard mark this peer as a router for the NAS's subnet (e.g. `192.168.1.0/24`). Other mesh peers then reach DSM at `https://192.168.1.50:5001`, SSH at `ssh user@192.168.1.50`, SMB shares, etc. — all over the mesh. The NAS uses userspace sockets to relay traffic, so LAN hosts see connections coming from the NAS's LAN IP (effectively SNAT). Caveats: **ICMP doesn't work** (`ping 192.168.1.50` from a remote peer will time out — the daemon can't open raw sockets without `CAP_NET_RAW`), and non-TCP/UDP protocols (GRE, IPsec passthrough, mDNS/broadcast discovery) don't propagate. TCP/UDP-based services — which is everything you actually want from a NAS — work fine.
- **NetBird's built-in SSH server.** Enable it in the management dashboard for this peer (or with `netbird up --enable-ssh`) and connect with `netbird ssh <peer-name>` from another NetBird-enrolled device. This rides the netstack interface and doesn't depend on host `sshd` at all. Good complement to the routing-peer option above when you specifically want SSH without LAN exposure.
- **Outbound-tunnel / reverse-proxy fronting.** Out of scope for this package, but mentioned for completeness — anything that publishes DSM through a tunnel initiated *from the NAS* works fine.

If you specifically need the NAS to be reachable on its actual NetBird IP (`100.x.x.x`) rather than via LAN-route SNAT, see "Advanced: kernel TUN via Task Scheduler" below.

### Advanced: kernel TUN via Task Scheduler (lets you reach the NAS on its NetBird IP)

This package ships in netstack mode because DSM 7+ does not let unsigned third-party packages run as root (Synology's package signature, not a user-flippable toggle), and `setcap` isn't available on most DSM builds to grant an unprivileged daemon `CAP_NET_ADMIN`. The `start-stop-status` script auto-detects how it was invoked: when DSM's Package Center starts it under the unprivileged `netbird` user it stays in netstack mode, but when invoked **as root**, it brings up `/dev/net/tun` and the daemon uses a real kernel TUN — making the NetBird IP routable on the host (sshd, DSM web UI reachable on `100.x.x.x`).

The supported way to run the script as root is via DSM's **Task Scheduler**. Caveats up front:

- You're managing daemon lifecycle outside Package Center. The package's GUI Start/Stop button will still work (and will fall back to netstack), but the kernel-TUN daemon needs to be (re)started by the scheduled task.
- Once the daemon has run as root, files under `/var/packages/netbird/var/` (config, keys, logs) end up owned by `root` — Package Center's later attempts to start it under `netbird` may fail with permission errors. If you revert to netstack-only, run `sudo chown -R netbird:netbird /var/packages/netbird/var`.
- This isn't a Synology-supported configuration. Future DSM updates could change it.

Setup:

1. **Configure Package Center to not auto-start the daemon as the netbird user.** In Package Center → NetBird → **Stop** the package. Then either disable auto-start, or leave it stopped; either way the scheduled task will own start-up.
2. **Create a triggered Task Scheduler task that runs at boot, as root:**
   - Control Panel → Task Scheduler → Create → Triggered Task → User-defined script.
   - General tab: Task = `NetBird (root)`, User = `root`, Event = `Boot-up`, Enabled.
   - Task Settings tab → Run command:
     ```bash
     /var/packages/netbird/scripts/start-stop-status start
     ```
3. **Run the task once to start the daemon now** (right-click → Run, or reboot).
4. Verify with `sudo netbird status` — `Interface type:` should now read `Native` (real TUN) instead of `Userspace`, and `ip -br addr` should show `wt0` holding `100.x.x.x/16`.
5. From another peer, `ssh user@100.x.x.x` and `https://100.x.x.x:5001` should now work.

To revert to netstack-only: disable/delete the scheduled task, run `sudo chown -R netbird:netbird /var/packages/netbird/var`, and use Package Center to start the package normally.

### Upgrades

Upgrading the package preserves your existing configuration — the daemon restarts and reconnects automatically using the keys it already has. No reconfiguration needed.

### Uninstalling

Stop the package before uninstalling. DSM can leave the package in a stuck state if the daemon is still running (or has crashed) at the time of removal.

1. **Stop** the package first — in **Package Center → NetBird → Action → Stop**, or via SSH:
   ```bash
   sudo synopkg stop netbird
   ```
2. **Uninstall** — **Package Center → NetBird → Action → Uninstall**.

DSM removes `/var/packages/netbird` (binary, config, keys, logs) on uninstall — nothing escapes that path, so no manual cleanup is needed.

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

- NetBird runs as a daemon managed by DSM's Package Center (start/stop/status), as the unprivileged `netbird` package user (`privilege.conf: run-as: package`)
- The daemon runs in **netstack mode** by default (`NB_USE_NETSTACK_MODE=true`) — fully userspace networking via bundled wireguard-go and a gVisor TCP/IP stack. No kernel TUN, no `CAP_NET_ADMIN`, no root.
- This is a deliberate compromise: DSM 7+ doesn't let unsigned third-party packages run as root, and `setcap` (which would let an unprivileged daemon create a kernel TUN) isn't shipped on most DSM builds. Netstack works on every DSM 7 box out of the box.
- The cost is host-reachability: services bound on the kernel network stack (sshd, DSM UI) don't see the netstack interface. See "[Reaching the NAS over NetBird](#reaching-the-nas-over-netbird)" for workarounds.
- The `start-stop-status` script auto-detects how it was invoked: when run by Package Center under the `netbird` user → netstack; when run **as root** (via the optional DSM Task Scheduler setup in "[Advanced: kernel TUN](#advanced-kernel-tun-via-task-scheduler-lets-you-reach-the-nas-on-its-netbird-ip)") → bring up `/dev/net/tun` and use a real kernel TUN. Same SPK, two modes, user picks.
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
| Privileges | Daemon runs as unprivileged `netbird` user via `privilege.conf` (`run-as: package`); uses NetBird netstack mode (no kernel TUN, no root) |

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

### `Interface type: Userspace` in `netbird status`

That's expected — by default the daemon runs in netstack mode and reports a userspace interface. Host services aren't reachable on the NetBird IP in this mode; see "[Reaching the NAS over NetBird](#reaching-the-nas-over-netbird)" for what works (LAN-route forwarding, NetBird SSH) and the "[Advanced: kernel TUN](#advanced-kernel-tun-via-task-scheduler-lets-you-reach-the-nas-on-its-netbird-ip)" section if you want a real kernel TUN via Task Scheduler.

### Install blocked by trust level

Sideloaded packages aren't signed by Synology. Go to **Package Center > Settings > General > Trust Level** and select **Any publisher**, then retry the install.

### Permission denied

The package runs as the unprivileged `netbird` user, and all writable state lives under `/var/packages/netbird/var`. If you see permission errors, restart the package from Package Center. If the CLI errors with `permission denied` reading profile state, run it under `sudo netbird ...` — your shell user doesn't have read access to the daemon's config directory.

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
│   ├── privilege           # `run-as: package` (unprivileged netbird user)
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

### Path to root mode (requires Synology code-signing)

DSM 7+ blocks unsigned third-party packages from running as root, *and* refuses to honor file-capability declarations in `privilege.conf` for unsigned packages. The current code-only workaround is the Task Scheduler recipe documented in "[Advanced: kernel TUN](#advanced-kernel-tun-via-task-scheduler-lets-you-reach-the-nas-on-its-netbird-ip)"; the *clean* path — a NAS reachable on its NetBird IP straight out of Package Center, with no scheduled task and no caveats — requires getting the SPK signed by Synology through the Package Center inclusion process.

NetBird is pursuing this. When it lands, the code changes here are mechanical:

1. **`spk/conf/privilege`** — add a `tool` block requesting `cap_net_admin,cap_net_raw` (and possibly `cap_chown`) on `bin/netbird.bin`. DSM only honors this stanza for Synology-signed packages; with signing in place the daemon picks up the capabilities it needs at start time and never has to run as root.
2. **`spk/scripts/start-stop-status`** — drop the `id -u == 0` auto-detect block and the `NB_USE_NETSTACK_MODE` fallback. With caps granted at the binary level the daemon always has what it needs.
3. **`README.md`** — remove the netstack caveats from the install Note, drop the "Reaching the NAS over NetBird" workaround list, and delete the "Advanced: kernel TUN" section.

At build time this should produce a *second SPK variant* alongside the existing sideload one — same source tree, two `privilege.conf` files selected via a build flag, two distribution channels. The sideload SPK (this repo's current output) stays so users without Package Center access can still install; the signed SPK becomes the recommended path for end users.

The signing application goes through the [Synology Developer Center](https://developer.synology.com/). The capability ask is narrow and Synology has a well-established process for this kind of inclusion. Timeline has historically been weeks to a few months. Worth flagging that this is a vendor relationship investment, not a code task: acceptance depends on Synology's review priorities, not on what we do here.

## Testing & Validation

This is a **testing / beta fork**, not the official NetBird-maintained DSM channel. It exists to validate the build, packaging, and update-delivery pipeline before any of it ships through `netbirdio/*`.

### What's being validated

- **Build pipeline** — single GitHub Actions run produces both `x86_64` and `aarch64` SPKs via a matrix workflow, attaches both to a Release, and refreshes the per-arch package source catalogs on GitHub Pages.
- **DSM Package Source flow** — confirming the static catalogs at `/x86_64/index.json` and `/aarch64/index.json` are recognized by DSM and surface NetBird in **Package Center → Community** with working auto-update.
- **Per-arch URL routing** — separate URLs per arch with single-entry catalogs avoids ambiguity in DSM's multi-entry handling. (An earlier iteration used one URL with two entries; DSM rejected it with "not supported on the platform" because of how it matches the catalog `arch` field.)

### Known untested areas

- **aarch64 on real ARM Synology hardware.** The aarch64 SPK is structurally correct (DSM accepts and installs it), but the bundled NetBird binary has not been runtime-tested on an actual ARM Synology model. If you run on one, please file an issue with results.
- **Update-detection latency.** DSM polls package sources on its own cadence; "should have updated by now" thresholds are still being characterized.

### Reporting feedback

File issues at <https://github.com/TechHutTV/netbird-dsm/issues>. Useful context to include:

- DSM version (`Control Panel → Info Center`)
- NAS model and CPU arch
- Whether you installed via Package Source or Manual Install
- Relevant log excerpt: `cat /var/packages/netbird/var/netbird.log`

## License

This packaging is provided as-is for the NetBird community. NetBird itself is licensed under the [BSD 3-Clause License](https://github.com/netbirdio/netbird/blob/main/LICENSE).
