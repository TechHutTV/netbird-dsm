# Data Share Resource Configuration

## Overview

The Data Share worker creates shared folders and configures permissions during package startup. Per the documentation, "This worker creates shared folder and set its permission during package startup."

## Core Functionality

**Acquire()**: Creates shared folders and applies permissions. If a folder already exists, it skips creation but still applies permissions.

**Release()**: Takes no action.

## Key Details

- **Provider**: DSM
- **Timing**: FROM_ENABLE_TO_POSTUNINST
- **Updatable**: No
- **Environment Variables**: None

## Configuration Syntax

```json
"data-share": {
  "shares": [{
    "name": "<share-name>",
    "permission": {
      "ro": ["<user-name>", ...],
      "rw": ["<user-name>", ...]
    },
    "once": "<once>"
  }, ...]
}
```

## Configuration Parameters

| Member | Since | Description |
|--------|-------|-------------|
| `shares` | 6.0-5914 | Object array of shares to create |
| `name` | 6.0-5914 | String name of the share |
| `permission` | 6.0-5914 | JSON object defining share permissions (optional) |
| `ro` | 6.0-5914 | String array of users with read-only access |
| `rw` | 6.0-5914 | String array of users with read/write access |
| `once` | 6.0-5914 | Boolean; defaults to false |

## Example Configuration

```json
"data-share": {
  "shares": [{
    "name": "music",
    "permission": {
      "ro": ["AudioStation"]
    }
  }]
}
```

This creates a "music" share with AudioStation having read-only access. Since `once` defaults to false, permissions are reapplied at each startup.

## Important Notes

- Shared folders persist after package uninstallation to protect user data
- As of version 7.0-41201, package center creates symlinks under `/var/packages/[package_id]/shares/` pointing to share folder paths
