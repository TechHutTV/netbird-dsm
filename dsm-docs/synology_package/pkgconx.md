# PKG_CONX

Similar to `install_conflict_packages` in INFO, but additionally defines restrictions by OS version.

> Priority of `PKG_CONX` is higher than `install_conflict_packages` in `INFO`

## Configuration Keys

| Key | Availability | Description | Value |
|-----|--------------|-------------|-------|
| pkg_min_ver | DSM4.2 | Min version of conflicting package | Package Version |
| pkg_max_ver | DSM4.2 | Max version of conflicting package | Package Version |
| dsm_min_ver | DSM4.2 - DSM7.1 | Min DSM version (replaced by `os_min_ver` since DSM7.2) | X.Y-Z |
| dsm_max_ver | DSM4.2 - DSM7.1 | Max DSM version (replaced by `os_max_ver` since DSM7.2) | X.Y-Z |
| os_min_ver | DSM7.2-60112 | Minimum required OS version | X.Y-Z |
| os_max_ver | DSM7.2-60112 | Maximum required OS version | X.Y-Z |

## Examples

```ini
; Conflicts with Package A in any version
[Package A]

; Conflicts with Package B version 2 or newer
[Package B]
pkg_min_ver=2

; Conflicts with Package C version 2 or older
[Package C]
pkg_max_ver=2
```
