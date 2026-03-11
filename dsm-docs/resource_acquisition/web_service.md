# Web Service Configuration Guide

## Overview

The Web Service worker manages web package services and portals during package installation, removal, and lifecycle transitions. It operates during two key timing phases:

- **`FROM_PREINST_TO_PREUNINST`**: Syncs configuration, handles migration, and sets up portals and services
- **`FROM_ENABLE_TO_DISABLE`**: Copies configuration files and manages service enablement

## Core Configuration Structure

```json
{
  "webservice": {
    "services": [
      {
        "service": "wordpress",
        "display_name": "WordPress",
        "type": "nginx_php",
        "root": "wordpress"
      }
    ],
    "portals": [
      {
        "service": "wordpress",
        "name": "wordpress",
        "type": "alias",
        "alias": "wordpress"
      }
    ],
    "migrate": {},
    "pkg_dir_prepare": []
  }
}
```

## Service Types

### Static Service
Serves static files via Nginx.

**Key fields:**
- `root`: Service working directory
- `index`: Index file array (default: `["index.html"]`)
- `custom_rule`: Custom routing rules

### Nginx PHP Service
Executes PHP via php-fpm with Nginx as the HTTP server.

**Key fields:**
- `root`: Service working directory
- `php`: PHP profile configuration
- `connect_timeout`: Connection timeout (seconds, default: 60)
- `read_timeout`: Response timeout (default: 60)
- `send_timeout`: Request timeout (default: 60)

### Apache PHP Service
Routes requests through Apache to php-fpm backend.

**Key fields:**
- `backend`: 1 (Apache 2.2) or 2 (Apache 2.4)
- `intercept_errors`: Error handling flag (default: true)
- `php`: PHP profile configuration

### Reverse Proxy Service
Proxies requests to target services supporting HTTP, HTTPS, and Unix sockets.

**Key fields:**
- `proxy_target`: Target URL or socket path
- `proxy_headers`: Custom header pairs
- `proxy_http_version`: HTTP version (0 for 1.0, 1 for 1.1)
- `proxy_intercept_errors`: Error interception (default: false)

## Common Service Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `service` | string | Yes | Service identifier |
| `display_name` | string | Yes | User-facing service name |
| `display_name_i18n` | string | No | Localized display names |
| `type` | string | Yes | Service type (static, nginx_php, apache_php, reverse_proxy) |
| `support_alias` | bool | No | Enable alias portal support (default: true) |
| `support_server` | bool | No | Enable server portal support (default: true) |
| `icon` | string | No | Icon path relative to package target; use `{0}` for resolution placeholder |

## PHP Profile Configuration

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `profile_name` | string | Yes | PHP profile identifier |
| `profile_desc` | string | Yes | Profile description |
| `backend` | int | Yes | PHP version (3=5.6, 4=7.0, 5=7.1, 6=7.2, 7=7.3) |
| `open_basedir` | string | No | PHP open_basedir setting |
| `extensions` | array | No | Enabled extensions users cannot disable |
| `php_settings` | object | No | Custom PHP ini settings |
| `user` | string | Yes | PHP-FPM user (must match pkg_dir_prepare user) |
| `group` | string | Yes | PHP-FPM group (must match pkg_dir_prepare group) |

## Portal Configuration

### Common Portal Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `service` | string | Yes | Linked service name |
| `name` | string | Yes | Portal identifier |
| `display_name` | string | No | UI portal title (defaults to name) |
| `app` | string | No | Package UI app identifier |
| `type` | string | Yes | Portal type: alias or server |

### Alias Portal
Accesses service by alias name.

```json
{
  "service": "wordpress",
  "name": "wordpress",
  "type": "alias",
  "alias": "wordpress"
}
```

### Server Portal
Direct server access with explicit ports.

```json
{
  "service": "wordpress",
  "name": "wordpress",
  "type": "server",
  "http_port": [9000],
  "https_port": [9001]
}
```

**Important:** "Default server portal cannot be registered as name-based portal due to potential FQDN lookup failures on client side."

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `http_port` | array | No | HTTP port (single port, server type) |
| `https_port` | array | No | HTTPS port (single port, server type) |

## Migration Configuration

### Root Migration
Migrates packages from older web share folder to DSM 7.0+ web_packages folder.

```json
{
  "root": [
    {
      "old": "wordpress",
      "new": "wordpress"
    }
  ]
}
```

### Virtual Host Migration
Converts legacy virtual hosts to service portals.

```json
{
  "vhost": [
    {
      "root": "wordpress",
      "service": "wordpress"
    }
  ]
}
```

## Package Directory Preparation

The `pkg_dir_prepare` mechanism creates website root directories with appropriate ownership and permissions.

```json
{
  "pkg_dir_prepare": [
    {
      "source": "/var/package/WordPress/target/src",
      "target": "wordpress",
      "mode": "0755",
      "group": "http",
      "user": "WordPress"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | No | Full path to source directory; webservice moves to target |
| `target` | string | Yes | Relative path under web_packages directory |
| `mode` | string | Yes | Directory access mode (e.g., "0755") |
| `group` | string | Yes | Target directory group ownership |
| `user` | string | Yes | Target directory user ownership |

**Note:** When `source` is unspecified, the worker creates the target directory and sets ownership without moving files.

## Custom Routing Rules

Packages can customize Nginx and Apache behavior via Mustache templates referenced in the `custom_rule` object.

```json
{
  "custom_rule": {
    "global_rule": "/var/packages/WordPress/target/misc/nginx_global.mustache",
    "fastcgi_rule": "/var/packages/WordPress/target/misc/nginx_fastcgi.mustache",
    "proxy_rule": "/var/packages/WordPress/target/misc/nginx_proxy.mustache",
    "apache_rule": "/var/packages/WordPress/target/misc/apache.mustache"
  }
}
```

| Rule | Affects | Service Types | Effect |
|------|---------|---------------|--------|
| `global_rule` | Nginx | All | Modifies service request behavior |
| `fastcgi_rule` | Nginx | nginx_php | Modifies php-fpm request handling |
| `proxy_rule` | Nginx | reverse_proxy | Modifies proxy target request handling |
| `apache_rule` | Apache 2.2/2.4 | apache_php | Modifies Apache behavior |

Template fields use `{{ @json key@ }}` syntax for dynamic content replacement.

## Proxy Headers

Configure custom headers for reverse proxy services to enable features like WebSocket support.

```json
{
  "proxy_headers": [
    {
      "name": "host",
      "value": "gitlab"
    },
    {
      "name": "Upgrade",
      "value": "$http_upgrade"
    },
    {
      "name": "Connection",
      "value": "$connection_upgrade"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | HTTP header name |
| `value` | string | Yes | Header value (supports Nginx variables) |

## Key Implementation Details

- **Privilege Model:** Web packages receive confined privileges during installation and runtime; `pkg_dir_prepare` assists with proper permission configuration
- **Directory Management:** Webservice removes the target directory between preuninst and postuninst stages; backup website data in preuninst scripts
- **User/Group Consistency:** PHP service `user` and `group` fields must match corresponding `pkg_dir_prepare` settings for proper file access
- **Icon Resolution:** Icon paths support `{0}` placeholder for automatic resolution substitution
- **Downgrade Protection:** Setting `support_alias` or `support_server` to false prevents downgrades to unsupported configurations
