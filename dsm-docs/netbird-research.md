# NetBird Client Research for Synology DSM Package

## Build System

- **Language:** Go 1.23+
- **Client source:** `client/` directory in monorepo
- **Build command:**
  ```bash
  GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -ldflags "-s -w" -o netbird ./client/
  ```
- Produces a fully static binary with zero shared library dependencies
- Uses GoReleaser for releases (`.goreleaser.yml` in repo root)

## Runtime Dependencies

### WireGuard: Bundled (wireguard-go)
- NetBird bundles `wireguard-go` as a Go library (`golang.zx2c4.com/wireguard`)
- Creates WireGuard tunnels entirely in userspace
- **No WireGuard kernel module needed** - critical for Synology DSM

### TUN Device: Required
- Creates a `tun` interface (typically named `wt0`)
- Requires `/dev/net/tun` (character device, major 10, minor 200)
- Requires `tun` kernel module to be loaded

### No Other Dependencies
- `CGO_ENABLED=0` = fully static binary, no libc needed

## Linux Capabilities Needed

| Capability | Why |
|---|---|
| `CAP_NET_ADMIN` | TUN interfaces, routes, iptables/nftables |
| `CAP_NET_RAW` | Raw sockets for ICMP probes |
| `CAP_NET_BIND_SERVICE` | Port 53 if DNS features used |
| `CAP_SYS_ADMIN` | Some network namespace operations |
| `CAP_DAC_OVERRIDE` | Config files in protected directories |

**In practice: run as root.** The official systemd service runs as root.

## Config/Data File Locations

| File | Purpose | Default |
|---|---|---|
| `config.json` | Main client config (keys, management URL, peers) | `/etc/netbird/config.json` |
| `state.json` | Runtime state | `/etc/netbird/state.json` |

Config path is configurable via `--config` / `-c` flag.

### Recommended DSM layout:
```
/var/packages/netbird/etc/config.json       # Config (persistent)
/var/packages/netbird/var/state.json        # State (persistent)
/var/packages/netbird/target/bin/netbird    # Binary
/var/packages/netbird/var/netbird.log       # Log file
```

## Systemd Service (reference)

```ini
[Unit]
Description=Netbird Service
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/netbird service run
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

Key: daemon command is `netbird service run` (foreground mode).

## CLI Reference

### Daemon: `netbird service run`
| Flag | Description | Default |
|---|---|---|
| `--config`, `-c` | Config file path | `/etc/netbird/config.json` |
| `--log-file`, `-l` | Log file path | stdout/stderr |
| `--log-level` | Verbosity (panic/fatal/error/warn/info/debug/trace) | `info` |
| `--management-url`, `-m` | Management server URL | `https://api.netbird.io:443` |

### Setup: `netbird up`
| Flag | Description | Default |
|---|---|---|
| `--setup-key`, `-k` | Setup key for enrollment | |
| `--management-url`, `-m` | Management server URL | `https://api.netbird.io:443` |
| `--config`, `-c` | Config file path | `/etc/netbird/config.json` |
| `--hostname` | Override hostname | OS hostname |
| `--interface-name`, `-i` | WireGuard interface name | `wt0` |
| `--wireguard-port`, `-p` | WireGuard listen port | `51820` |
| `--disable-auto-connect` | No auto-connect on start | `false` |
| `--disable-dns` | Disable DNS management | `false` |
| `--disable-firewall` | Disable firewall management | `false` |

### Other commands
- `netbird status` - Connection status, peers, IP
- `netbird down` - Disconnect
- `netbird version` - Print version

## Ports Used

### Outbound (client connects to)
| Port | Protocol | Service |
|---|---|---|
| 443 | TCP (gRPC) | Management server (`api.netbird.io`) |
| 443 | TCP (WebSocket) | Signal server (`signal.netbird.io`) |
| 443 | TCP | Relay server (fallback when P2P fails) |
| 3478 | UDP | STUN (NAT traversal) |

### Local / P2P
| Port | Protocol | Purpose |
|---|---|---|
| 51820 | UDP | WireGuard tunnel (configurable) |
| 53 | UDP/TCP | DNS resolver (only if DNS enabled) |
| Random | UDP | ICE/STUN candidates |

### DSM firewall config (`netbird.sc`)
```
[netbird_wireguard]
title="NetBird VPN"
desc="NetBird VPN Service"
port_forward="no"
dst.ports="51820/udp"
```
