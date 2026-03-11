# Port Config

## Overview

The Port Config resource enables installation and uninstallation of service port configuration files during package lifecycle events on Synology DSM systems.

## Description

"Install / uninstall service port config file during package install / uninstall." For comprehensive details on port configuration files, refer to the Ports Information documentation.

## Operations

- **Acquire()**: Copies the .sc file to `/usr/local/etc/service.d/` (skips if destination exists)
- **Release()**: Removes the .sc file and reloads firewall and port forwarding
- **Update()**: Updates the .sc file and reloads firewall and port forwarding

## Lifecycle Timing

`FROM_POSTINST_TO_POSTUNINST`

## Environment Variables

None

## Update Capability

Yes - refer to Config Update documentation for triggering updates.

## Configuration Syntax

```json
"port-config": {
    "protocol-file": "<protocol_file>"
}
```

## Parameters

| Member | Since | Description |
|--------|-------|-------------|
| `protocol_file` | 6.0-5936 | .sc file's relative path under `/var/package/{$package}/target/` |

## Example Configuration

```json
"port-config": {
    "protocol-file": "port_conf/xxdns.sc"
}
```
