# NetBird Synology DSM Package

A Synology DSM 7.0+ package (.spk) for the [NetBird](https://netbird.io/) VPN client. Runs unprivileged with userspace local forwarding so permitted peers can reach NAS services through its NetBird IP. Provides DSM integration for daemon lifecycle, firewall rules, CLI symlink, log rotation, and a read-only status page in DSM's AppPortal. **Configuration is CLI-only** — after installing, SSH into the NAS and use the `netbird` command to connect.

**Supported architectures:** `x86_64` (Intel/AMD — Plus series and above) and `aarch64` (64-bit ARM Synologies, e.g. DS220j-class and newer Realtek/Marvell ARM models).

> ### ⚠️ Testing / beta fork
>
> This repository is a **testing fork** used to validate the build, packaging, and update-delivery pipeline before any of it lands in an official NetBird-maintained channel. The Package Source URL below points at this fork's GitHub Pages deployment. See [Testing & Validation](#testing--validation) below for what's been verified, what hasn't, and how to report issues.

## Prerequisites

- A Synology NAS running **DSM 7.0** or later (x86_64 or aarch64)
- `curl`, `tar`, `make` (for building the package)
- The Go toolchain required by the selected NetBird release's `go.mod` (only if building from source)

## Quick Start (Pre-built Binary)

Local builds and GitHub Actions default to **NetBird 0.80.0**, pinned in the [`VERSION`](VERSION) file. The native SPK uses the standard NetBird binary with the same networking settings as upstream's rootless image; Docker is not required.

```bash
# x86_64 (Intel/AMD — default)
make download package

# aarch64 (ARM64 Synology models)
make download package SYNOLOGY_ARCH=aarch64
```

This produces `netbird_<version>_synology_<amd64|arm64>.spk` in the repo root.

To explicitly select another [NetBird release](https://github.com/netbirdio/netbird/releases), pass `VERSION=<version>` without the leading `v`. The release workflow accepts an override too; leaving it blank uses the pinned version.

## Building from Source

```bash
git clone https://github.com/netbirdio/netbird.git /path/to/netbird
git -C /path/to/netbird checkout v0.80.0

# x86_64
make build package NETBIRD_SRC=/path/to/netbird

# aarch64
make build package NETBIRD_SRC=/path/to/netbird SYNOLOGY_ARCH=aarch64
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

> **Rootless networking:** This package runs as the unprivileged `netbird` user in **netstack mode with local forwarding**. It does not need a kernel TUN device, file capabilities, or a root task for inbound access. NetBird forwards permitted connections on its overlay IP to services listening on the NAS's loopback address. DSM 7 restricts root privileges for unsigned packages; changing the publisher trust level does not grant root access.
>
> DSM, SSH, and SMB access depend on service bindings and NetBird access policies. See [Reaching the NAS over NetBird](#reaching-the-nas-over-netbird) and the [hardware validation checklist](#rootless-networking-validation-on-dsm). Ordinary NAS applications do not gain automatic outbound access to the mesh in this mode.

### Replacing a manual installation

Stop a previous manual NetBird installation before installing this SPK. The
installer and launcher check for another daemon, an active or enabled manual
`netbird.service`, and a conflicting `/usr/local/bin/netbird`. The package's own
CLI link and daemon are recognized during upgrades. Process inspection depends
on DSM permissions; a root-only process may require an administrator to inspect
it. A leftover config, stale socket, disabled service, or `wt0` interface alone
does not prove that another daemon is running.

Use a LAN connection independent of NetBird while retiring the old installation:

1. **Identify and back up the manual installation.** As an administrator, inspect
   `ps -ef`, `systemctl status netbird.service`, and
   `readlink -f /usr/local/bin/netbird`. Save any enrollment/configuration you want
   to retain from `/etc/netbird` and `/var/lib/netbird` in a protected backup.
   Those files can contain private keys.
2. **Stop the manual daemon and disable automatic startup.** For an installation
   using the confirmed manual systemd unit, run:
   ```bash
   sudo systemctl disable --now netbird.service
   ```
   Disable any Task Scheduler task or custom startup script for that manual
   installation too. If a daemon remains, inspect its command line and
   `/proc/<PID>/exe` as root, then stop that specific process. A process can still
   run after its executable has been deleted. Do not stop unrelated NetBird
   processes by name indiscriminately.
3. **Remove only confirmed manual program files.** Remove the old executable or
   link at `/usr/local/bin/netbird` if it belongs to the manual installation.
   Keep it if it points to `/var/packages/netbird/target/bin/netbird`. Remove the
   confirmed manual `netbird.service` unit from its installed location (commonly
   `/etc/systemd/system`, `/usr/local/lib/systemd/system`, `/usr/lib/systemd/system`,
   or `/lib/systemd/system`), then run `sudo systemctl daemon-reload`.
   The package's `pkgctl-netbird.service` is a different unit and must be kept.
4. **Choose fresh enrollment or an explicit migration.** Fresh package state is
   initialized independently of the old system config. Existing package state
   is preserved on restart and upgrade. To retain the manual identity, an
   administrator must explicitly copy the desired default config into the
   stopped package's state directory with ownership `netbird:netbird` and mode
   `0600`, before its first start. Do not overwrite an existing package identity.
   Check that the old management server is still the intended destination;
   additional named profiles need separate migration. Otherwise, enroll the
   package normally using the CLI below.
5. **Optionally remove remaining manual state.** After the manual daemon and its
   startup mechanisms are stopped, and after backing up or migrating anything
   needed, these commands discard the old manual state:
   ```bash
   sudo rm -rf /etc/netbird /var/lib/netbird
   sudo rm -f /var/run/netbird.sock
   ```
   Do not remove `/var/packages/netbird` or its resolved data directory as part
   of manual-install cleanup. Verify that the manual daemon and its host
   interface do not return after startup tasks have been disabled.

An inaccessible or empty package config, or a missing config alongside existing
profile/state data, stops startup rather than silently generating a new identity.
Restore the config from backup or repair its permissions. Use the documented
[clean reset](#start-fresh-clean-reset) only when a new enrollment is intended.

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

The package enables `NB_USE_NETSTACK_MODE=true` and `NB_ENABLE_NETSTACK_LOCAL_FORWARDING=true`, matching [NetBird 0.80.0's rootless configuration](https://github.com/netbirdio/netbird/blob/v0.80.0/client/Dockerfile-rootless). Incoming connections to the NAS's NetBird IP are forwarded to the same port on `127.0.0.1`. For example, `100.x.x.x:5001` reaches `127.0.0.1:5001` on the NAS. The NAS does not need that NetBird address on a kernel interface.

1. Enroll the NAS using `sudo netbird up --setup-key YOUR_SETUP_KEY`.
2. In the NetBird dashboard, allow the connecting peers to reach the NAS on the required ports. Typical TCP ports are **5001** for DSM HTTPS, **22** for DSM's SSH service, and **445** for SMB. Use your configured ports if different.
3. Enable the corresponding services in DSM and make sure they listen on loopback or all interfaces. A service bound only to the NAS's LAN IP will not accept a connection forwarded to `127.0.0.1`.
4. From another enrolled peer, use `https://100.x.x.x:5001`, `ssh user@100.x.x.x`, or `smb://100.x.x.x/share`, substituting the NAS's NetBird IP. You do not need to advertise a LAN route just to reach the NAS this way.

Local forwarding also makes loopback-only services reachable when a NetBird policy permits their ports. Limit policies to the source peers and destination ports you intend to allow. Host services see the forwarded connection as local, so their logs and source-IP rules do not identify the original peer. Binding to loopback or trusting local source addresses is not sufficient isolation for an allowed port; use NetBird policies to control peer access and require authentication in the service itself.

The SSH example above uses DSM's existing SSH service and accounts. NetBird's optional built-in SSH server is separate; when enabled, it can handle port 22 itself and runs sessions as the unprivileged package user. Leave it disabled when you intend to forward port 22 to DSM SSH.

### Rootless limitations and direct P2P

- **Inbound access:** local forwarding supports TCP and UDP services that accept connections on loopback. Responses to those connections travel back through NetBird.
- **Outbound access:** ordinary NAS applications cannot initiate mesh connections transparently because the host has no NetBird interface or routes. Applications that support SOCKS5 can use NetBird's local proxy (normally `127.0.0.1:1080`). See [upstream rootless documentation](https://docs.netbird.io/get-started/install/docker#rootless-image).
- **DNS:** rootless networking does not install NetBird DNS settings into DSM. Other peers can still use NetBird DNS to find the NAS; use IP addresses when isolating connectivity problems.
- **LAN routing:** the NAS can act as a userspace routing peer for reachable LAN resources. Configure a NetBird resource/route and the required policies; local forwarding also permits access to the NAS's own LAN address. See [routing-peer self-access](https://docs.netbird.io/use-cases/remote-access/reach-services-on-the-routing-peer).
- **Protocols:** this does not provide full layer-3 networking for host applications. Broadcast discovery and protocols requiring independent outbound connections need separate consideration. Test the actual service rather than using ping as the sole success criterion.
- **Direct P2P:** netstack mode does not force relaying. NetBird still attempts direct connections; NAT and firewall conditions decide whether it needs a relay. Check `sudo netbird status --detail` to distinguish connection type from service reachability.

### Advanced: kernel TUN via Task Scheduler (system-wide outbound access)

Use this optional mode when NAS applications need transparent outbound mesh access or you need a host network interface instead of local forwarding. It is not required for the inbound access described above. When started **as root**, the service script attempts to prepare `/dev/net/tun` and use a real kernel TUN. It falls back to netstack with local forwarding if that device is unavailable. The log records the selected mode.

DSM's **Task Scheduler** can run the script as root, with these limitations:

- You're managing daemon lifecycle outside Package Center. Its unprivileged scripts may not be able to stop a root-owned daemon. Use the service script as root to stop it before upgrades, uninstalling, or switching modes.
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
4. Check the startup log for `kernel TUN` and use `ip addr show wt0` to verify a host interface with the NetBird IP. `Interface type: Userspace` alone does not distinguish netstack from userspace WireGuard using a real TUN; this package always disables kernel WireGuard.
5. Test outbound access from a NAS application to another peer, subject to NetBird policies and DSM firewall rules.

To return to the normal rootless package, disable/delete the scheduled task, then stop the root daemon **before** restoring ownership:

```bash
sudo /var/packages/netbird/scripts/start-stop-status stop
sudo chown -R netbird:netbird /var/packages/netbird/var
sudo synopkg start netbird
```

### Upgrades

Upgrading the package preserves your existing configuration — the daemon restarts and reconnects automatically using the keys it already has. No new enrollment is needed.

**Before upgrading from an earlier netstack build, review every NetBird policy that grants access to this NAS.** Local forwarding becomes active on the next daemon start under those existing policies, including broad grants to all peers or all ports. Narrow the grants to the intended source peers and required destination ports before upgrading: allowed ports can now reach host services, including previously unreachable loopback-only listeners. Those services see a local connection, so any service that trusts localhost without authentication needs its own access controls before its port is allowed.

If you used the root Task Scheduler workaround, follow the steps above to return daemon ownership to Package Center before upgrading.

### Uninstalling

Stop the package before uninstalling. DSM can leave the package in a stuck state if the daemon is still running (or has crashed) at the time of removal.

1. **Stop** the package first — in **Package Center → NetBird → Action → Stop**, or via SSH:
   ```bash
   sudo synopkg stop netbird
   ```
2. **Uninstall** — **Package Center → NetBird → Action → Uninstall**.

DSM removes `/var/packages/netbird` (binary, config, keys, logs) on uninstall — nothing escapes that path, so no manual cleanup is needed.

## Status Page (DSM AppPortal)

After install the package registers a NetBird entry in DSM's **Main Menu** that opens a read-only status page. Sign in to DSM with an account in the **administrators** group, using the same hostname or IP address as the status page. The page uses your existing DSM session; it does not need a separate NetBird login.

The CGI validates the DSM session and administrator membership before reading configuration, querying NetBird, or returning logs. Invalid or expired sessions receive a sign-in page (HTTP 401); authenticated non-administrators receive HTTP 403. Authentication or group-lookup failures deny access. **Application Privileges** controls the launcher, but granting launcher access does not grant non-administrators access to this page.

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
- **Local forwarding** (`NB_ENABLE_NETSTACK_LOCAL_FORWARDING=true`) delivers permitted inbound connections on the NetBird IP to host loopback services. Access policies are enforced by NetBird's userspace filter.
- The netstack startup environment also sets `NB_DISABLE_DNS=true` and `NB_ENABLE_CAPTURE=false`, following upstream's rootless image. Rootless mode does not configure DSM's host DNS or routes.
- The `start-stop-status` script selects netstack for unprivileged starts even if `/dev/net/tun` is writable. An explicit **root** start can use a real TUN for system-wide outbound access; see [Advanced: kernel TUN](#advanced-kernel-tun-via-task-scheduler-system-wide-outbound-access). Network setup runs only when starting a new daemon.
- Firewall rules are registered with DSM automatically (port 51820/udp)
- Log rotation is handled by DSM's syslog system
- Status page is served by DSM's web framework via the `dsmuidir` resource. The CGI calls DSM's `authenticate.cgi` and checks administrator membership before accessing package data; responses disable caching and referrer disclosure.

### DSM Integration

| Feature | Implementation |
|---------|---------------|
| Daemon lifecycle | `scripts/start-stop-status` (start/stop/status) |
| Firewall rules | `Netbird.sc` port config via `port-config` resource |
| CLI access | `/usr/local/bin/netbird` via `usr-local-linker` resource |
| Log rotation | `logrotate.conf` via `syslog-config` resource |
| Status page | `ui/index.cgi` via `dsmuidir` (DSM session and administrator checks enforced by the CGI) |
| Privileges | Unprivileged `netbird` user via `conf/privilege` (`run-as: package`); netstack with local forwarding |

## File Locations

| File | Path on DSM |
|------|-------------|
| Binary | `/var/packages/netbird/target/bin/netbird.bin` |
| CLI wrapper | `/var/packages/netbird/target/bin/netbird` (sets `NB_DAEMON_ADDR`, execs the binary) |
| CLI symlink | `/usr/local/bin/netbird` → wrapper |
| Status page CGI | `/var/packages/netbird/target/ui/index.cgi` |
| AppPortal URL | `https://<nas>:5001/webman/3rdparty/netbird/index.cgi` |
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

That's expected. Local forwarding can reach host services without a kernel interface, and `Userspace` does not mean the connection is relayed. Check the package startup log for `netstack with local forwarding`, then test a service as described in [Reaching the NAS over NetBird](#reaching-the-nas-over-netbird).

### Connected, but DSM / SSH / SMB is unreachable on the NetBird IP

1. Confirm that the startup log says `netstack with local forwarding`. After installing this version, restart the package to pick up the new daemon environment.
2. Check that the connecting peer's NetBird policy permits the NAS and service port.
3. On the NAS, check the listener, for example `sudo netstat -lntp`, and test DSM locally with `curl -kI https://127.0.0.1:5001`. Here `-k` is only for testing DSM's local certificate. Adjust the port to your DSM configuration. If the service listens only on the LAN IP, adjust its binding or use a LAN resource/route instead.
4. If SSH reaches the package user instead of DSM's SSH service, check whether NetBird's built-in SSH server is enabled. Disable it when you want local forwarding to DSM SSH.
5. Check `sudo netbird status --detail` and both DSM and NetBird logs. A relayed tunnel can still reach the service; failure to establish direct P2P is a separate connectivity issue.

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
sudo find /var/packages/netbird/var/ -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
sudo synopkg start netbird
sudo netbird up --setup-key YOUR_SETUP_KEY
```

The trailing slash traverses DSM's `var` symlink, and `find` includes hidden state
directories. This resets package state only. Legacy manual-install state is
handled separately under [Replacing a manual installation](#replacing-a-manual-installation).

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
    └── ui/                 # DSM AppPortal status page
        ├── config          # AppPortal manifest (allUsers:false, grantPrivilege:local)
        ├── index.cgi       # Read-only status page (shell CGI)
        └── images/         # Multi-size launcher icons (16, 24, 32, 48, 64, 72, 96, 256 px)
```

## Development

Edit files in `spk/` and rebuild:
```bash
make clean
make test                                      # Python 3; no NAS or network required
make download package                          # x86_64, pinned NetBird version
make download package SYNOLOGY_ARCH=aarch64     # aarch64
```

Build variables:

| Variable        | Default          | Notes                                                       |
|-----------------|------------------|-------------------------------------------------------------|
| `VERSION`       | `VERSION` file (`0.80.0`) | NetBird upstream version, or package revision when running `make package` separately. |
| `SYNOLOGY_ARCH` | `x86_64`         | Synology arch token written into INFO. Also accepts `aarch64`. |
| `NETBIRD_ARCH`  | auto from above  | NetBird release arch (`amd64`/`arm64`). Override only if needed. |
| `NETBIRD_SRC`   | `.`              | Path to NetBird source (only for `make build`)              |

### Rootless implementation and privileged variants

The standard upstream binary supports rootless networking; no alternate executable or container is needed. The daemon environment follows [upstream's versioned rootless Dockerfile](https://github.com/netbirdio/netbird/blob/v0.80.0/client/Dockerfile-rootless). The [upstream forwarder](https://github.com/netbirdio/netbird/blob/v0.80.0/client/firewall/uspfilter/forwarder/forwarder.go) maps the peer's NetBird destination address to host loopback. Keep these settings on the daemon launch, since exporting them only for a CLI command does not reconfigure a running daemon.

`VERSION` is the shared default for local, PR, and release builds. Update it deliberately when validating a new upstream release. PR and release workflows run `make test` before packaging. Source builds must use a matching upstream checkout.

A future package with host networking privileges would address transparent outbound access and other kernel networking needs. It is not a prerequisite for inbound service access. Synology documents its [root-package signing restriction](https://help.synology.com/developer-guide/getting_started/system_requirement.html) and [package privilege configuration](https://help.synology.com/developer-guide/privilege/privilege_config.html); any privileged variant needs separate DSM validation. The optional Task Scheduler path remains available for administrator-managed TUN operation.

## Testing & Validation

This is a **testing / beta fork**, not the official NetBird-maintained DSM channel. It exists to validate the build, packaging, and update-delivery pipeline before any of it ships through `netbirdio/*`.

### What's being validated

- **Build pipeline** — single GitHub Actions run produces both `x86_64` and `aarch64` SPKs via a matrix workflow, attaches both to a Release, and refreshes the per-arch package source catalogs on GitHub Pages.
- **DSM Package Source flow** — confirming the static catalogs at `/x86_64/index.json` and `/aarch64/index.json` are recognized by DSM and surface NetBird in **Package Center → Community** with working auto-update.
- **Per-arch URL routing** — separate URLs per arch with single-entry catalogs avoids ambiguity in DSM's multi-entry handling. (An earlier iteration used one URL with two entries; DSM rejected it with "not supported on the platform" because of how it matches the catalog `arch` field.)

### Verified on DS1522+ (October 5, 2026)

Tested **x86_64, DSM 7.4.1 build 90080**, using `netbird_0.80.0-90008_synology_amd64.spk` from commit [`8491b06`](https://github.com/TechHutTV/netbird-dsm/commit/8491b06bbf717c915e477b1949e26c2eda1d0b74) and [CI run 37349381551](https://github.com/TechHutTV/netbird-dsm/actions/runs/37349381551). Installation and package lifecycle operations used DSM's `synopkg` CLI.

| Check | Observed result |
|-------|-----------------|
| Rootless startup | NetBird 0.80.0 ran as the `netbird` user with `netstack with local forwarding` in the log; no root startup task. |
| Allowed service access | DSM HTTPS and API authentication, DSM SSH login, and content-verified SMB write/read/delete passed over the NAS's NetBird IP. SSH reported a loopback source address. |
| Policy enforcement | With the same client and a temporary policy disabled, TCP 22, 445, and 5001 all timed out. Port-specific policies allowed selected services while denying the others; restoring the policy restored access. Existing production policies were unchanged. |
| Stop/start and reboot | Services recovered automatically after package stop/start and a DSM reboot, with enrollment preserved and the daemon still owned by `netbird`. |
| Enrolled upgrade | A clean, enrolled 0.71.4 installation upgraded to 0.80.0-90008, preserving peer ID, name, and IP without another login or setup key. Forwarded services became reachable; allowed and denied port checks passed afterward. |
| Separate-network access | From a cellular hotspot, direct NAS LAN access failed while overlay DSM authentication, SSH login, and SMB write/read/delete passed. NetBird reported direct P2P on both LAN and cellular. |
| Status page | Displayed status matched the CLI, but this initial artifact exposed status and logs without authentication. The subsequent fix and its validation are described below. |

These results cover one NAS and the tested TCP services. DSM HTTPS tests bypassed certificate-name verification when connecting by IP; they do not validate the certificate configuration. Networking regression tests use a fake daemon and simulated privileges to check service-script behavior; they do not replace hardware traffic tests.

### Status-page authentication follow-up

The updated CGI was installed on the same DS1522+ and checked through DSM's web server. Anonymous requests, sessions without a token, forged tokens, and sessions after logout returned HTTP 401 without status or logs. A valid administrator session and token returned HTTP 200 with the status page. Retrieving the token through the existing DSM session also passed. Browser testing confirmed that a logged-in administrator could open the page and a private window showed only the sign-in message.

All 14 local tests passed, including CGI checks for non-administrators, authentication and group-lookup failures, spoofed identity headers, and requests originating from loopback. The authentication follow-up used LAN and NAS loopback access; a real non-administrator DSM session and access through an enrolled NetBird peer still need a hardware retest.

### Remaining validation gaps

- **Additional forwarding and recovery cases.** Forced relay, UDP forwarding, daemon crash recovery, revocation of established connections, and applications that listen only on loopback or trust local source addresses were not tested.
- **Interactive DSM flows.** Package Center installation and visual DSM login were not exercised in a browser; the hardware tests used the package-manager CLI and DSM HTTP API.
- **aarch64 on real ARM Synology hardware.** The 0.80.0 SPK builds with the upstream ARM64 binary, but installation and runtime behavior still need testing on an actual ARM Synology model. If you run on one, please file an issue with results.
- **Update-detection latency.** DSM polls package sources on its own cadence; "should have updated by now" thresholds are still being characterized.

### Rootless networking validation on DSM

1. Install the 0.80.0 SPK for the NAS architecture and start it from Package Center as the `netbird` user. If migrating from the root workaround, stop that daemon and restore package ownership first.
2. Enroll it, confirm the startup log says `netstack with local forwarding`, and verify the reported agent version is `0.80.0`.
3. From an allowed peer, open DSM over HTTPS, log in through DSM SSH, and read/write a test file over SMB using the NAS's NetBird IP. Confirm each service accepts loopback connections before diagnosing the tunnel.
4. Repeat from a peer with no applicable allow policy and confirm access is denied. Check for broad existing policies that would otherwise allow the test peer.
5. Inspect `netbird status --detail` while using a service and record direct versus relayed connectivity. Do not treat a working relay as a local-forwarding failure.
6. Stop/start the package, reboot DSM, and test a package upgrade. Confirm enrollment persists and service access returns without a root task.

### Reporting feedback

File issues at <https://github.com/TechHutTV/netbird-dsm/issues>. Useful context to include:

- DSM version (`Control Panel → Info Center`)
- NAS model and CPU arch
- Whether you installed via Package Source or Manual Install
- Relevant log excerpt: `cat /var/packages/netbird/var/netbird.log`

## License

This packaging is provided as-is for the NetBird community. NetBird itself is licensed under the [BSD 3-Clause License](https://github.com/netbirdio/netbird/blob/main/LICENSE).
