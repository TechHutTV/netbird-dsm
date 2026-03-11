# Docker Worker Documentation

## Overview

The Docker worker (available since DSM 7.0) enables package developers to deploy containers without manual Docker commands. It utilizes docker-compose framework to generate configuration and manage containers.

## Lifecycle Operations

**Installation/Removal Phase (`FROM_POSTINST_TO_PREUNINST`):**
- `Acquire()`: Creates docker-compose.yaml, prepares host volumes, and launches containers
- `Release()`: Removes docker-compose.yaml, host volumes, containers, and images (note: host volumes persist during upgrades)

**Startup/Shutdown Phase (`FROM_STARTUP_TO_HALT`):**
- `Acquire()`: Starts containers
- `Release()`: Stops containers

## Configuration Syntax

```json
"docker":{
    "services": [{
        service setting 1
    },{
        service setting 2
    }...]
}
```

## Services Parameters

| Key | Since | Type | Required | Nullable | Description |
|-----|-------|------|----------|----------|-------------|
| `service` | 18.09.0-1018 | string | true | false | Service name |
| `image` | 18.09.0-1018 | string | true | false | Image name |
| `tag` | 18.09.0-1018 | string | true | false | Image tag |
| `build` | 18.09.0-1018 | string | true | false | Relative path to Dockerfile directory |
| `container_name` | 18.09.0-1018 | string | false | true | Container name |
| `shares` | 18.09.0-1018 | array | false | true | Persistent data volume specifications |
| `volumes` | 18.09.0-1018 | array | false | true | Config file mount specifications |
| `ports` | 18.09.0-1018 | array | false | true | Container port bindings |
| `environment` | 18.09.0-1018 | array | false | false | Environment variables |
| `depends` | 18.09.0-1018 | array | false | false | Dependent services |

## Build Configuration

Build paths are relative to `/var/packages/PKG_NAME/target/`.

**Syntax:**
```json
{
  "build": "[Dockerfile directory]"
}
```

**Transforms to docker-compose.yaml:**
```yaml
build: /var/packages/PKG_NAME/target/[Dockerfile directory]
```

**Example:**
```json
{
  "build": "odoo_docker"
}
```

Generates:
```yaml
build: /var/packages/Odoo/target/odoo_docker
```

## Volumes Configuration

### Shares (Persistent Data)

Used for container persistent data storage.

**Syntax:**
```json
{
  "shares": [{
      "host_dir": "[host directory]",
      "mount_point": "[mount point]"
  }]
}
```

**Transforms to docker-compose.yaml:**
```yaml
volumes:
  - /volumeX/docker/PKG_NAME/[host directory]:[mount point]
```

**Example:**
```json
{
  "shares": [{
      "host_dir": "odoo_data",
      "mount_point": "/var/lib/odoo"
  }]
}
```

Generates:
```yaml
volumes:
  - /volume1/docker/Odoo/odoo_data:/var/lib/odoo
```

### Volumes (Configuration Files)

Used for mounting configuration files or directories from package target path.

**Syntax:**
```json
{
  "volumes": [{
      "host_dir": "[host config or directory]",
      "mount_point": "[mount point]"
  }]
}
```

**Transforms to docker-compose.yaml:**
```yaml
volumes:
  - /var/packages/PKG_NAME/target/[host config or directory]:[mount point]
```

**Example:**
```json
{
  "volumes": [{
      "host_dir": "odoo_docker/config",
      "mount_point": "/etc/odoo"
  }]
}
```

Generates:
```yaml
volumes:
  - /var/packages/Odoo/target/odoo_docker:/etc/odoo
```

## Ports Configuration

Host ports must be between 1025-65535.

**Syntax:**
```json
{
  "ports": [{
      "host_port": "[port on host]",
      "container_port": "[port in container]",
      "protocol": "[tcp or udp]"
  }]
}
```

**Transforms to docker-compose.yaml:**
```yaml
ports:
  - "[port on host]:[port in container]/[tcp or udp]"
```

**Example:**
```json
{
  "ports": [{
      "host_port": "30076",
      "container_port": "80",
      "protocol": "tcp"
  }, {
      "host_port": "30078",
      "container_port": "443",
      "protocol": "tcp"
  }]
}
```

Generates:
```yaml
ports:
  - "30076:80/tcp"
  - "30078:443/tcp"
```

## Environment Variables Configuration

**Syntax:**
```json
{
  "environment": [{
      "env_var": "[variable name]",
      "env_value": "[value]"
  }]
}
```

**Transforms to docker-compose.yaml:**
```yaml
environment:
  - "[variable name]=[value]"
```

**Example:**
```json
{
  "environment": [{
      "env_var": "HOST",
      "env_value": "odoo_db"
  }, {
      "env_var": "USER",
      "env_value": "odoo"
  }, {
      "env_var": "PASSWORD",
      "env_value": "odoo"
  }]
}
```

Generates:
```yaml
environment:
  - HOST=odoo_db
  - USER=odoo
  - PASSWORD=odoo
```

## Dependencies Configuration

Specifies dependent services following docker-compose conventions.

**Syntax:**
```json
{
  "depends": [{
      "dep_service": "[service name]"
  }]
}
```

**Transforms to docker-compose.yaml:**
```yaml
depends_on:
  - [service name]
```

**Example:**
```json
{
  "depends": [{
      "dep_service": "odoo_db"
  }]
}
```

Generates:
```yaml
depends_on:
  - odoo_db
```

## Complete Example

**Input Configuration (conf/resource):**
```json
{
    "docker": {
        "services": [{
            "service": "odoo",
            "build": "odoo_docker",
            "image": "odoo",
            "container_name": "Odoo",
            "tag": "12.0",
            "environment": [{
                "env_var": "HOST",
                "env_value": "odoo_db"
            }, {
                "env_var": "USER",
                "env_value": "odoo"
            }, {
                "env_var": "PASSWORD",
                "env_value": "odoo"
            }],
            "shares": [{
                "host_dir": "odoo_data",
                "mount_point": "/var/lib/odoo"
            }],
            "ports": [{
                "host_port": "{{wizard_http_port}}",
                "container_port": "8069",
                "protocol": "tcp"
            }],
            "depends": [{
                "dep_service": "odoo_db"
            }]
        }, {
            "service": "odoo_db",
            "image": "postgres",
            "tag": "10",
            "container_name": "Odoo_db",
            "shares": [{
                "host_dir": "db",
                "mount_point": "/var/lib/postgresql/data/pgdata"
            }],
            "environment": [{
                "env_var": "POSTGRES_DB",
                "env_value": "postgres"
            }, {
                "env_var": "POSTGRES_PASSWORD",
                "env_value": "odoo"
            }, {
                "env_var": "POSTGRES_USER",
                "env_value": "odoo"
            }, {
                "env_var": "PGDATA",
                "env_value": "/var/lib/postgresql/data/pgdata"
            }]
        }]
    }
}
```

**Generated docker-compose.yaml:**
```yaml
version: '3'
services:
  odoo:
    build: /var/packages/Docker_Odoo_SynoCommunity/target/odoo_docker
    image: odoo:12.0
    container_name: Odoo
    environment:
      - HOST=odoo_db
      - USER=odoo
      - PASSWORD=odoo
    volumes:
      - /volume1/docker/Docker_Odoo_SynoCommunity//odoo_data:/var/lib/odoo
    ports:
      - "30076:8069/tcp"
    depends_on:
      - odoo_db
    networks:
      - Docker_Odoo_SynoCommunity
  odoo_db:
    image: postgres:10
    container_name: Odoo_db
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_USER=odoo
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - /volume1/docker/Docker_Odoo_SynoCommunity//db:/var/lib/postgresql/data/pgdata
    networks:
      - Docker_Odoo_SynoCommunity
networks:
  Docker_Odoo_SynoCommunity:
    driver: bridge
```

## Key Specifications

- **Provider:** Docker
- **Timing:** `FROM_POSTINST_TO_PREUNINST` and `FROM_STARTUP_TO_HALT`
- **Environment Variables:** None
- **Updatable:** No
