# INFO File

## Overview

The INFO file describes the properties of a Synology package using key/value pair format.

## File Format

```
key=value
```

## Example Configuration

```
thirdparty="yes"
maintainer="mycompany"
description="mydescription"
distributor="mycompany"
package="mypackagename"
silent_install="yes"
silent_uninstall="yes"
silent_upgrade="yes"
os_min_ver="7.0-40000"
version="0.0.1-0001"
arch="noarch"
```

## Field Categories

- **Necessary Fields** - Required properties for package definition
- **Optional Fields** - Non-required properties that add functionality

Rather than manually creating an INFO file, developers can leverage helper functions within the Package Toolkit to generate fields programmatically via `INFO.sh` (see Pack Stage docs).
