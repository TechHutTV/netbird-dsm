# PHP INI Resource Configuration

## Overview

The PHP INI worker enables packages to deploy custom `php.ini` and `fpm.conf` files. During package startup, files are installed to designated directories; during shutdown, they're removed.

## Functionality

**Acquire()** operation:
- Copies php.ini and fpm.conf files to `/usr/local/etc/php56/conf.d/` and `/usr/local/etc/php56/fpm.d/`
- Reloads php56-fpm service
- Files require `.ini` or `.conf` extensions (others ignored)
- Prefixes filenames with `${package}`
- Unlinks existing files before installation
- Aborts and triggers rollback on copy failures

**Release()** operation:
- Deletes previously created links
- Ignores missing files and unlink failures

## Specifications

| Aspect | Details |
|--------|---------|
| Provider | PHP5.6 |
| Timing | `FROM_ENABLE_TO_DISABLE` |
| Environment Variables | None |
| Updatable | No |

## Configuration Syntax

```json
"php": {
     "php-ini": [{
         "relpath": "<ini-relpath>"
     }, ...],
     "fpm-conf": [{
         "relpath": "<conf-relpath>"
     }, ...]
 }
```

## Field Reference

| Member | Since | Description |
|--------|-------|-------------|
| `php-ini` | PHP5.6-5.6.17-0020 | Object array of php.ini files to install |
| `fpm-conf` | PHP5.6-5.6.17-0020 | Object array of fpm.conf files to install |
| `relpath` | PHP5.6-5.6.17-0020 | Target file path relative to `/var/packages/${package}/target/` |

## Configuration Example

```json
{
    "php": {
        "php-ini": [{
            "relpath": "synology_added/etc/php/conf.d/test_1.ini"
        }, {
            "relpath": "synology_added/etc/php/conf.d/test_2.ini"
        }, {
            "relpath": "synology_added/etc/php/conf.d/test_3.ini"
        }],
        "fpm-conf": [{
            "relpath": "synology_added/etc/php/fpm.d/test_1.conf"
        }, {
            "relpath": "synology_added/etc/php/fpm.d/test_2.conf"
        }, {
            "relpath": "synology_added/etc/php/fpm.d/test_2.conf"
        }]
    }
}
```
