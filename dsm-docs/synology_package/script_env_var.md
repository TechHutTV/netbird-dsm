# Script Environment Variables

Environment variables exported by Package Center for use in scripts.

## Available Variables

| Variable | Description |
|----------|-------------|
| SYNOPKG_PKGNAME | Package identity defined in INFO |
| SYNOPKG_PKGVER | Package version (new version during upgrade) |
| SYNOPKG_PKGDEST | Target installation directory |
| SYNOPKG_PKGDEST_VOL | Target volume of installation |
| SYNOPKG_PKGPORT | adminport from INFO |
| SYNOPKG_PKGINST_TEMP_DIR | Temporary directory during install/upgrade |
| SYNOPKG_TEMP_LOGFILE | Temporary file path for logging messages |
| SYNOPKG_TEMP_UPGRADE_FOLDER | Temporary directory during upgrade (for migrating files) |
| SYNOPKG_DSM_LANGUAGE | End user's DSM language |
| SYNOPKG_DSM_VERSION_MAJOR | DSM major version |
| SYNOPKG_DSM_VERSION_MINOR | DSM minor version |
| SYNOPKG_DSM_VERSION_BUILD | DSM build number |
| SYNOPKG_DSM_ARCH | End user's CPU architecture |
| SYNOPKG_PKG_STATUS | Lifecycle status: INSTALL, UPGRADE, UNINSTALL, START, STOP, or empty (boot/shutdown) |
| SYNOPKG_OLD_PKGVER | Previous version during upgrades |
| SYNOPKG_TEMP_SPKFILE | Temporary SPK file location during install/upgrade |
| SYNOPKG_USERNAME | User initiating action; empty if system-triggered |
| SYNOPKG_PKG_PROGRESS_PATH | Temporary file path for showing install/upgrade progress |

## Progress Example

Values range from 0 to 1:

```bash
flock -x "$SYNOPKG_PKG_PROGRESS_PATH" -c echo 0.80 > "$SYNOPKG_PKG_PROGRESS_PATH"
```
