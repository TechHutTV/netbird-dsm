# PKG_DEPS

Similar to `install_dep_packages` in INFO, but additionally defines restrictions by OS version.

> Priority of `PKG_DEPS` is higher than `install_dep_packages` in `INFO`

## Configuration Keys

| Key | Availability | Description | Value |
|-----|--------------|-------------|-------|
| pkg_min_ver | DSM4.2 | Minimum version of dependent package | Package version |
| pkg_max_ver | DSM4.2 | Maximum version of dependent package | Package version |
| dsm_min_ver | DSM4.2 - DSM7.1 | Min DSM version (replaced by `os_min_ver` since DSM7.2) | X.Y-Z |
| dsm_max_ver | DSM4.2 - DSM7.1 | Max DSM version (replaced by `os_max_ver` since DSM7.2) | X.Y-Z |
| os_min_ver | DSM7.2-60112 | Minimum required OS version | X.Y-Z |
| os_max_ver | DSM7.2-60112 | Maximum required OS version | X.Y-Z |

## Examples

```ini
; Depends on Package A in any version
[Package A]

; Depends on Package B version 2 or newer
[Package B]
pkg_min_ver=2

; Depends on Package C version 2 or older
[Package C]
pkg_max_ver=2

; Depends on Package D v2+, ignored when OS < 7.2-60000
[Package D]
os_min_ver=7.2-60000
pkg_min_ver=2

; Depends on Package E v2+, ignored when OS > 7.2-60000
[Package E]
os_max_ver=7.2-60000
pkg_min_ver=2
```
