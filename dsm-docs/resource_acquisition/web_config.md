# Web Config Documentation

## Overview

The Web Config worker manages Nginx static configurations, available since DSM 7.2. As stated in the documentation, it helps to "make the registered nginx static config take effect at its desired time."

## Key Functionality

### Lifecycle Operations

**Installation to Pre-uninstall Phase:**
- Copies configs from `/var/packages/${package}/target/` to nginx folders
- Creates disabled config links initially

**Startup to Halt Phase:**
- Removes disabled links and creates enabled ones during startup
- Reverses the process during shutdown

## Critical Implementation Notes

The system implements several safeguards: "When creating an enable link, it will first lock and test the nginx config to avoid race conditions and to ensure that it does not conflict with the enabled config."

Configuration files undergo automatic renaming using hash calculation to prevent collisions, following the pattern: `{prefix}.{package}-hash({path}).conf`

## Required Service Restarts

Package developers must declare nginx restart requirements in the INFO file:
- For enable timing: `instuninst_restart_services = nginx.service`
- For disable timing: both `instuninst_restart_services` and `startstop_restart_services`

## Configuration Structure

```json
{
  "web-config": {
    "nginx-static-config": {
      "enable": [],
      "disable": []
    }
  }
}
```

## Config Types Supported

| Type | Purpose |
|------|---------|
| dsm | DSM Server and custom domain blocks |
| www | Default server block (80/443) |
| http | HTTP context |
| server | Independent server block |
| x-accel | Acceleration settings |
| main | Stream/mail blocks (DSM 7.0.27+) |

## Resource Declaration

Configs can optionally declare port reservations and aliases:
- **port**: Numeric port number
- **protocol**: tcp/udp/both
- **schema**: http/https
- **alias**: Domain alias declarations
