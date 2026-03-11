# Apache 2.2 Config

## Description

Packages can carry sites-enabled/*.conf files for Apache HTTP Server 2.2. This worker installs/uninstalls these config files during package start/stop.

- **`Acquire()`**: Copy the conf files to `/usr/local/etc/httpd/sites-enabled/`. Then reload Apache 2.2.
  - The files should have .conf extension, otherwise it will be ignored
  - Files will be prefixed by `${package}`
  - Existing files will be `unlink()` first
  - Failure on any file copy results in this worker to abort and triggers rollback

- **`Release()`**: Delete previously created links
  - Ignore files that are not found
  - Ignore `unlink()` failure

## Provider

WebStation

## Timing

`FROM_ENABLE_TO_DISABLE`

## Environment Variables

None

## Updatable

No

## Syntax

```json
"apache22": {
    "sites-enabled": [{
        "relpath": "<conf-relpath>"
    }, ...]
}
```

## Members Table

| Member | Since | Description |
|--------|-------|-------------|
| `sites-enabled` | WebStation-1.0-0049 | Object array, list of conf files to install |
| `relpath` | WebStation-1.0-0049 | Target file's relative path under `/var/packages/${package}/target/` |

## Example

```json
{
    "apache22": {
        "sites-enabled": [{
            "relpath": "synology_added/test_1.conf"
        }, {
            "relpath": "synology_added/test_2.conf"
        }, {
            "relpath": "synology_added/test_3.conf"
        }]
    }
}
```
