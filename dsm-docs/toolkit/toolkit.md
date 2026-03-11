# Synology Toolkit

## Overview

Creating a package manually can be very complex for most developers, so Synology recommends using the Package Toolkit to make the package creation process easier.

## Toolkit Directory Structure

```
/toolkit/
├── build_env/
│   └── ds.${platform}-${version}/
└── pkgscripts-ng/
    ├── EnvDeploy
    └── PkgCreate.py
```

## Package Creation Workflow

The toolkit employs a two-stage approach through `PkgCreate.py`:

1. **Build Stage**: Compiles the project and dependent projects in correct order
2. **Pack Stage**: Packages the project into an `.spk` file

## Required Configuration Files

Developers must provide configuration files in a folder named **SynoBuildConf** under their project:

- `SynoBuildConf/depends` - Defines project dependencies (Build Stage)
- `SynoBuildConf/build` - Specifies compilation instructions (Build Stage)
- `SynoBuildConf/install` - Specifies SPK packaging instructions (Pack Stage)
- `SynoBuildConf/install-dev` - Similar to install but uses chroot environment rather than general DSM system

## Manual Package Creation

Without the toolkit, developers must manually:
- Prepare a cross-compile tool chain
- Prepare a build environment
- Prepare metadata
- Compile source code
- Pack the package
