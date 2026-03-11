# Port Configuration for Synology Packages

## Overview

Packages that use specific ports for communication need a service configuration file. This enables the package to appear in firewall rules and port forwarding menus when users create rules through built-in applications.

## Service Configuration File

**Naming Convention:** `[package_name].sc`

The package name must match the "package" key in the INFO file. The `.sc` extension denotes a Service Configure file.

## Configuration Format

```
[service_name]
title="English title"
desc="English description"
port_forward="yes" or "no"
src.ports="ports/protocols"
dst.ports="ports/protocols"

[service_name2]
...
```

## Configuration Parameters

| Parameter | Required | Description | Values | Default | DSM Version |
|-----------|----------|-------------|--------|---------|-------------|
| service_name | Yes | Unique identifier; alphanumeric, hyphens, underscores, periods only | Valid string | N/A | 4.0-2206+ |
| title | Yes | Firewall protocol field display text | English text | N/A | 4.0-2206+ |
| desc | Yes | Firewall applications field display text | English text | N/A | 4.0-2206+ |
| port_forward | No | Enable port forwarding rule listing | "yes" or "no" | "no" | 4.0-2206+ |
| src.ports | No | Source ports with protocol specification | Format: `port,range/protocol` | tcp,udp | 4.0-2206+ |
| dst.ports | Yes | Destination ports with protocol specification | Format: `port,range/protocol` | tcp,udp | 4.0-2206+ |

**Port specification syntax:** Separate multiple ports with commas, use colons for ranges (e.g., `7000:8000`), and specify protocols (tcp, udp) after a forward slash.

## Example Configuration

```
[ss_findhostd_port]
title="Search Surveillance Station"
desc="Surveillance Station"
port_forward="yes"
src.ports="19997/udp"
dst.ports="19998/udp"
```

## Resource Specification Integration

Add to your resource specification file:

```json
"port-config": {
    "protocol-file": "port_conf/xxdns.sc"
}
```

Reference: [Port Config Documentation](../resource_acquisition/port_config.html)

## Checking Port Conflicts

Before modifying port numbers, verify they're not already in use.

### Example: DhcpServer.sc

```
[dhcp_udp]
title="DHCP Server"
title_key="DHCP Server"
desc="DHCP Server"
desc_key="DHCP Server"
port_forward="no"
dst.ports="67,68/udp"
```

### Command to Check Port Availability

```bash
servicetool --conf-port-conflict-check --tcp 667
```

### Expected Output

```
root@dev:~# servicetool --conf-port-conflict-check --tcp 667
IsConflict: false       Port: 667       Protocol: tcp   ServiceName: (null)
root@dev:~#
```

**Note:** "Parse the standard output to extract the IsConflict value. If false, the port is available for use."
