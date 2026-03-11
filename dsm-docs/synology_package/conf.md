# conf

The conf folder contains configuration files for Synology packages.

## File Structure

| File/Folder | Required | Description | Type | DSM |
|---|---|---|---|---|
| PKG_DEPS | No | Define dependency between packages with OS version restrictions | File | 4.2-3160 |
| PKG_CONX | No | Define conflicts between packages with OS version restrictions | File | 4.2-3160 |
| privilege | Yes | Define file privilege and execution privilege to secure the package | File | 6.2-5891 |
| resource | No | Define system resources for package lifecycle | File | 6.2-5941 |

> **Since DSM 7.0, all packages are forced to lower the privilege explicitly. The `privilege` must be provided for package to work.**
