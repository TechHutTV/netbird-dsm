# FHS - Package Filesystem Hierarchy Standard

## Volume Partition Installation

```
/var/packages/[package_name]
├── etc     -> /volume[N]/@appconf/[package_name]
├── var     -> /volume[N]/@appdata/[package_name]
├── tmp     -> /volume[N]/@apptemp/[package_name]
├── home    -> /volume[N]/@apphome/[package_name]
└── target  -> /volume[N]/@appstore/[package_name]
```

## System Partition Installation

```
/var/packages/[package_name]
├── etc     -> /usr/syno/etc/packages/[package_name]
├── var     -> /usr/local/packages/@appdata/[package_name]
├── tmp     -> /usr/local/packages/@apptemp/[package_name]
├── home    -> /usr/local/packages/@apphome/[package_name]
└── target  -> /usr/local/packages/@appstore/[package_name]
```

## Directory Details

| Directory | Purpose | Mode | Created | Removed | Script Variable |
|-----------|---------|------|---------|---------|-----------------|
| etc | Permanent config storage | 0755 | installed/upgraded | never | none |
| var | Permanent data storage (7.0+) | 0755 | installed/upgraded | never | SYNOPKG_PKGVAR |
| tmp | Temporary data storage (7.0+) | 0755 | installed/upgraded | uninstalled/upgrading | SYNOPKG_PKGTMP |
| home | Private storage (7.0+) | 0700 | installed/upgraded | never | SYNOPKG_PKGHOME |
| target | Data from package.tgz | 0755 | installed/upgraded | uninstalled/upgrading | SYNOPKG_PKGDEST |

## Directory Owner Rules

- **run-as package**: FHS directories use `[packageuser]:[packagegroup]` ownership
- **run-as root**: FHS directories use `root:[packagegroup]` ownership

The `etc` directory was moved to volume since DSM 7.0-41330 (old path still works).
