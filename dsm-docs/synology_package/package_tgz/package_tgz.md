# package.tgz

## Overview

The package.tgz file is a compressed archive (tgz or xz format) containing all necessary components for application deployment:

- Executable files
- Library files
- UI files
- Configuration files

## Creation

Use `pkg_make_package` function to create the package.tgz instead of packing it manually.

## Installation Location

Upon installation, package.tgz extracts to one of:
- `/volume?/@appstore/[your_pkg_name]/`
- `/usr/local/packages/@appstore/[your_pkg_name]/`

The location depends on the `install_type` field in the INFO file.

## Symbolic Linking

The system creates a soft link at:
```
/var/packages/[your_pkg_name]/target
```
pointing to the assigned installation folder.

## Additional Directories

Beyond the target directory, additional directories are automatically created for different data storage purposes (see FHS documentation).
