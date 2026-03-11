# System Requirements

## Toolkit Requirements

- **64bit** generic Linux environment with root permission (Ubuntu 18.04 LTS recommended)
- bash (>= 4.1.5)
- python (>= 2.7.3)

> **Important:** DO NOT install toolkit on Synology NAS as your development environment. Instead, install Docker on your NAS and configure a standard Linux container for toolkit installation.

## Runtime Requirements

- DSM6 packages require a DSM6 NAS device
- DSM7 packages require a DSM7 NAS device
- Package for DSM6 is **not** compatible with DSM7

## Development Token Installation (Collaborative Partners)

For packages requiring root privilege, Synology provides a development token to bypass signing restrictions:

1. Open DSM web UI → Support Center > Support Services
2. Click "Generate Logs" button (produces `debug.dat` file)
3. Send `debug.dat` to Synology
4. Receive signed development token from Synology
5. Place token at `/var/packages/syno_dev_token` on the originating NAS

**Token Limitation:** The development token is only valid for the NAS generating the `debug.dat`.

### Error Message Reference

If installation fails without proper token configuration: "Failed to install. The package should run with a lower privilege level."
