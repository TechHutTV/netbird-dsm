# Running WireGuard-based VPN Clients on Synology DSM

## WireGuard Kernel Module on DSM 7.x

**DSM does NOT ship with WireGuard kernel module.** DSM 7.x uses Linux 4.4.x kernel; WireGuard was merged in kernel 5.6.

Community projects exist to compile wireguard.ko for DSM:
- https://github.com/runfalk/synology-wireguard
- https://github.com/vegardit/synology-wireguard

But these break on every DSM kernel update. **We will NOT use kernel WireGuard - we use wireguard-go instead.**

## TUN/TAP Device on DSM 7

- `tun.ko` kernel module ships with DSM (needed for VPN Server/Docker)
- **Not loaded by default** unless VPN Server package is installed
- Must be loaded at package start:
  ```bash
  /sbin/modprobe tun 2>/dev/null || /sbin/insmod /lib/modules/tun.ko
  mkdir -p /dev/net
  [ ! -c /dev/net/tun ] && mknod /dev/net/tun c 10 200
  chmod 600 /dev/net/tun
  ```

## Existing NetBird on Synology

- **No official SPK package** exists
- GitHub issues requesting Synology support exist
- Users have manually run the Linux amd64 binary via SSH (doesn't survive reboots)
- Some run NetBird in Docker (`--cap-add=NET_ADMIN --device=/dev/net/tun`)

## Go Cross-Compilation for Synology

Standard Go cross-compilation works. No Synology-specific toolchain needed for Go.

```bash
# x86_64 (Plus series, most common)
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build ...

# ARM64 (rtd1296, rtd1619b models)
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build ...

# ARM32 (older models)
GOOS=linux GOARCH=arm GOARM=7 CGO_ENABLED=0 go build ...
```

Static linking (`CGO_ENABLED=0`) is critical - DSM has non-standard shared library layout.

## Kernel Module Loading on DSM 7

- DSM 7 packages run as non-root by default
- Loading kernel modules requires root privileges
- Package must declare `"run-as": "root"` in `conf/privilege` OR use specific capabilities
- Built-in modules like `tun.ko` are in `/lib/modules/` - just need `modprobe`
- Loaded modules don't persist across reboots - must reload in start script
- Users must enable "Any publisher" in Package Center for unsigned packages

## Recommended Architecture for NetBird DSM

| Aspect | Approach |
|--------|----------|
| WireGuard | wireguard-go (userspace, bundled in NetBird binary) |
| TUN device | Load `tun.ko` via modprobe in start script |
| Binary | Static Go binary (`CGO_ENABLED=0`) |
| Package format | Synology SPK (.spk) |
| Privilege | Run as root |
| Service management | start-stop-status script |
| Build framework ref | SynoCommunity spksrc (https://github.com/SynoCommunity/spksrc) |

## Key External References

- https://github.com/SynoCommunity/spksrc
- https://github.com/netbirdio/netbird
- https://sourceforge.net/projects/dsgpl/files/ (Synology GPL source/toolchains)
