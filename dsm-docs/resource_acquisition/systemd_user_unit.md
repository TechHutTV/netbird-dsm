# Systemd User Unit Documentation

## Overview

The systemd-user-unit worker handles user-level systemd units for Synology packages. The framework automatically manages file deployment and removal during package lifecycle events.

## Key Functionality

**File Management:** The package framework copies files located at `conf/systemd/pkguser-[customname]` to `home/.config/systemd/user/` during acquisition and removes them during release.

**Important Limitation:** "user unit cannot be related with normal systemd unit. If you need your package to be related with system service, please refer to [start_dep_services]"

## Service Control

Packages should use `synosystemctl start` and `synosystemctl stop` commands to manage user units within scripts.

## System-Level Units

For system-wide systemd units, place files in `conf/systemd/pkg-[customname]` instead. The framework will copy these to `/usr/local/lib/systemd/system` on acquisition and remove them on release.

## Technical Specifications

- **Provider:** DSM
- **Availability:** Since version 7.0-40761
- **Timing:** FROM_POSTINST_TO_POSTUNINST
- **Syntax:**
```json
"systemd-user-unit": {}
```
