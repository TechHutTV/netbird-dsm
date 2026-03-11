# Privilege

## Overview

DSM 7.0+ packages are forced to lower the privilege by applying privilege mechanism explicitly. Packages should operate under non-root user accounts to minimize security vulnerabilities.

## Capabilities

With privilege configuration, developers can:

- Control default user/group identity for processes in scripts
- Manage file permissions within package.tgz
- Set file capabilities in package.tgz
- Regulate access to special system resources

## Implementation

Create a configuration file at `conf/privilege`:

```json
{
    "defaults": {
        "run-as": "package"
    }
}
```

## Resource Access

Normal users cannot perform privileged operations. The system provides a mechanism for packages to request system resources (see Resource section).
