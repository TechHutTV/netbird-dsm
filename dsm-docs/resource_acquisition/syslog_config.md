# Syslog Config Documentation

## Overview

This resource handler manages syslog-ng and logrotate configuration files during package lifecycle events.

## Core Functionality

**Acquire()**: "Copy patterndb / logrotate to _/usr/local/etc/syslog-ng/patterndb.d/_ / _/usr/local/etc/logrotate.d/_. Then reload syslog-ng." If files exist, they're unlinked first. Any copy failure triggers rollback.

**Release()**: Deletes configuration files and reloads syslog-ng, ignoring unlink failures.

## Key Specifications

| Property | Details |
|----------|---------|
| Provider | DSM |
| Timing | `FROM_STARTUP_TO_HALT` |
| Updatable | No |
| Environment Variables | None |

## Configuration Syntax

```json
"syslog-config": {
  "patterndb-relpath": "<relpath>",
  "patterninc": [
    {
        "target-dir": "not2msg",
        "conf-relpath": "<relpath>"
    },
    {
        "target-dir": "not2kern",
        "conf-relpath": "<relpath>"
    }
  ],
  "logrotate-relpath": "<relpath>"
}
```

## Configuration Members

| Member | Since | Description |
|--------|-------|-------------|
| `patterndb-relpath` | 6.0-7145 | Syslog-ng config file path relative to `/var/packages/${package}/target/` (optional) |
| `patterndb-inc` | 6.1-7610 | Object array defining extra syslog-ng configs for specified paths |
| `target-dir` | 6.1-7610 | Installation target under `/usr/local/etc/syslog-ng/patterndb.d/include/` |
| `conf-relpath` | 6.1-7610 | Source path relative to `/var/packages/${package}/target/` |
| `logrotate-relpath` | 6.0-5911 | Logrotate config file path (optional, for non-database logs) |

## Usage Example

```json
"syslog-config": {
  "patterndb-relpath": "etc/syslog-ng.conf",
  "patterninc": [
    {
        "target-dir": "not2msg",
        "conf-relpath": "etc/NotLog2Msg"
    },
    {
        "target-dir": "not2kern",
        "conf-relpath": "etc/NotLog2Kern"
    }
  ],
  "logrotate-relpath": "etc/logrotate.conf"
}
```

## Important Notes

- Reference [syslog-ng.org](https://syslog-ng.org/) for configuration file syntax
- Store package logs in `/var/packages/[package_id]/var/` directory
