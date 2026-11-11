# NetBird for Synology DSM

Run [NetBird](https://netbird.io/) on your Synology NAS and reach DSM, SSH, SMB, and other NAS services through its NetBird IP. The package integrates with Package Center and includes a web interface for enrollment, connection status, peer details, and troubleshooting.

[Download a release](https://github.com/TechHutTV/netbird-dsm/releases/latest) · [Package source](https://techhuttv.github.io/netbird-dsm/) · [Report an issue](https://github.com/TechHutTV/netbird-dsm/issues)

> This is a community-maintained beta package, not an official NetBird distribution.

## Requirements

- Synology DSM 7.0 or newer.
- A supported 64-bit Intel/AMD (`x86_64`) or ARM (`aarch64`) NAS.
- Python 3 for web connection controls and diagnostics, and jq 1.5 or newer for the status summary.

The package runs as an unprivileged user. Docker and a kernel TUN device are not required for incoming connections to NAS services.

## Installation

### Package Center

Add the package source matching your NAS architecture to receive updates through Package Center:

| Architecture | Package source URL |
|---|---|
| Intel/AMD (`x86_64`) | `https://techhuttv.github.io/netbird-dsm/x86_64/index.json` |
| ARM64 (`aarch64`) | `https://techhuttv.github.io/netbird-dsm/aarch64/index.json` |

1. Open **Package Center → Settings → General** and select **Any publisher** under **Trust Level**.
2. Open **Package Sources**, select **Add**, and enter the URL for your architecture.
3. Find **NetBird** in the **Community** tab and select **Install**.

To identify your NAS architecture over SSH, run:

```sh
synogetkeyvalue /etc.defaults/synoinfo.conf unique
```

The result contains a chip-family name. Common Intel/AMD names include `apollolake`, `geminilake`, `v1000`, `r1000`, and `denverton`. ARM64 names include `armada37xx`, `rtd1296`, and `rtd1619b`. See [the full architecture lists](spk/INFO.sh) for other supported chips.

### Manual installation

1. Download the `.spk` for your architecture from [Releases](https://github.com/TechHutTV/netbird-dsm/releases/latest): `amd64` for Intel/AMD or `arm64` for ARM64.
2. Allow **Any publisher** in Package Center's trust settings.
3. Select **Manual Install** and upload the file.

If you already run NetBird outside Package Center, follow [Replacing a manual installation](#replacing-a-manual-installation) before installing.

## Connect your NAS

1. Sign in to DSM over **HTTPS** with an administrator account.
2. Open **NetBird** from DSM's main menu.
3. Choose **NetBird Cloud** or enter your self-hosted HTTPS management URL.
4. Enter a setup key from that server's dashboard and select **Enroll and connect**.

Use **Disconnect** and **Connect** to control the connection without removing enrollment. Disconnecting while accessing DSM through NetBird can close your session, so use a LAN connection when testing this.

Manage the daemon with **Start**, **Stop**, and **Restart** in Package Center. The web interface uses your existing DSM administrator session.

### Command line

SSH into the NAS to use the `netbird` CLI:

```sh
# Enroll and connect
sudo netbird up --setup-key YOUR_SETUP_KEY

# Connect to a self-hosted server
sudo netbird up --setup-key YOUR_SETUP_KEY --management-url https://netbird.example.com

# Check status and connection details
sudo netbird status
sudo netbird status --detail

# Disconnect while keeping enrollment
sudo netbird down
```

## Reaching NAS services

The default networking mode forwards permitted traffic from the NAS's NetBird IP to the same port on `127.0.0.1`. For example, `https://100.x.x.x:5001` reaches DSM HTTPS on `127.0.0.1:5001`.

To reach a service:

1. Allow the connecting peer to access the NAS and service port in your NetBird policies.
2. Enable the service on DSM and make sure it listens on loopback or all interfaces. A service listening only on the NAS's LAN IP cannot accept this forwarding.
3. Connect using the NAS's NetBird IP and the service's port. Common TCP ports are **5001** for DSM HTTPS, **22** for SSH, and **445** for SMB. Use your configured ports if they differ.

Forwarded connections appear local to the service. Restrict NetBird policies to the peers and ports you need, and require authentication on services that would otherwise trust localhost.

### Networking limits

- **Outbound traffic:** ordinary NAS applications do not automatically gain access to the NetBird network. Applications with SOCKS5 support can use NetBird's local proxy, normally `127.0.0.1:1080`. See [NetBird's rootless networking documentation](https://docs.netbird.io/get-started/install/docker#rootless-image).
- **DNS:** this mode does not configure DSM's host DNS. Other peers can still resolve the NAS through NetBird DNS.
- **Connection type:** both direct P2P and relayed connections are supported. `Interface type: Userspace` does not mean the connection is relayed; check `netbird status --detail`.

For transparent outbound access from NAS applications, see [kernel TUN mode](docs/advanced-setup.md#kernel-tun-mode).

## Updates and removal

Package Center checks the configured package source for updates. Updates preserve the package's configuration and enrollment.

Before upgrading an older build that did not forward traffic to local services, review the policies granting access to this NAS. Existing broad policies can make loopback-only services reachable after the upgrade.

To uninstall, **stop the package first**, then select **Action → Uninstall** in Package Center. Back up the package state before uninstalling if you need to retain enrollment.

## Troubleshooting

The web interface shows connection health, peer details, and recent logs. Under **Troubleshooting**, you can enable debug logging for 10 minutes or create a diagnostic bundle.

Choose **Download only** to keep a bundle local. Uploads go to NetBird's support service, including when using a self-hosted management server. Review bundles before sharing them and include the returned support code in your support request.

For startup errors, check the package log and system journal over SSH:

```sh
sudo tail -n 50 /var/packages/netbird/var/netbird.log
sudo journalctl -t netbird-pkg -n 50
```

If NetBird is connected but a service is unreachable, check its NetBird policy, listening address, and port. For DSM HTTPS, test the local listener with `curl -kI https://127.0.0.1:5001`; `-k` bypasses certificate verification for this local test. If port 22 opens a session as the package user, disable NetBird's built-in SSH server to reach DSM SSH instead.

The package registers UDP port **51820** with DSM. Check whether custom DSM firewall rules block it when diagnosing connectivity.

### Replacing a manual installation

Stop the old daemon and its startup service or task before installing this package. Back up its configuration if you want to retain the identity. Follow the [migration guide](docs/advanced-setup.md#replacing-a-manual-installation) to identify conflicting files and choose between fresh enrollment and migration.

### Returning to Package Center

If you started NetBird as root through Task Scheduler, disable that task and restore package-user ownership before returning to Package Center or upgrading. Follow the [recovery steps](docs/advanced-setup.md#returning-to-package-center) to preserve enrollment.

### Advanced: kernel TUN

Use [kernel TUN mode](docs/advanced-setup.md#kernel-tun-mode) when NAS applications need system-wide outbound access to peers. It requires a root Task Scheduler task and separate service management.

### Start fresh (clean reset)

A reset removes keys, configuration, and profiles and requires new enrollment. See [the reset procedure](docs/advanced-setup.md#start-fresh-clean-reset) if that is what you intend. Use the ownership recovery steps above for permission errors.

## Testing & Validation

The rootless package was tested on a DS1522+ running DSM 7.4.1 with NetBird 0.80.0, including DSM HTTPS, SSH, SMB, reboot recovery, and enrolled upgrades. ARM64 packages build, but runtime behavior still needs validation on ARM Synology hardware. These results do not establish compatibility for every model or newer release.

[Report an issue](https://github.com/TechHutTV/netbird-dsm/issues) with your NAS model, DSM version, package version, installation method, and relevant logs. Remove private keys, setup keys, and other credentials before sharing them.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local builds, tests, upstream version updates, and the release workflow.

## License

This packaging is provided as-is for the NetBird community. NetBird itself is licensed under the [BSD 3-Clause License](https://github.com/netbirdio/netbird/blob/main/LICENSE).
