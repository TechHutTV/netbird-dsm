# Docker Project Worker Documentation

## Overview

The **Docker Project Worker** is provided by ContainerManager (version 1432+, since DSM7.2.1) and enables multi-container applications using docker-compose. It offers more flexibility than the standard Docker Worker.

## Core Functionality

The worker manages docker projects during package lifecycle events:
- **Installation/Uninstallation**: Creates, updates, and builds projects; deletes them on removal
- **Startup/Shutdown**: Starts projects on package startup; stops them on halt

## Configuration Syntax

```json
{
    "docker-project": {
        "preload-image": "image.tar.gz",
        "projects": [{
            "name": "django-project",
            "path": "django"
        }, {
            "name": "wordpress-project",
            "path": "wordpress-mysql"
        }]
    }
}
```

## Configuration Parameters

### Top-Level Keys

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| preload-image | String | false | Load image tar ball |
| projects | Array | true | List of docker projects |

### Projects Array

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| name | string | true | project name |
| path | string | true | directory of compose.yaml, relative path from target |
| build_params | object | false | build project parameters |

### Build Parameters

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| force_pull | boolean | false | force pull image |
| force_recreate | boolean | true | force recreate containers |
| build | boolean | true | force build Dockerfile |

## Example: Docker Compose File

```yaml
services:
  db:
    image: mariadb:10.6.4-focal
    command: '--default-authentication-plugin=mysql_native_password'
    volumes:
      - db_data:/var/lib/mysql
    restart: always
    environment:
      - MYSQL_ROOT_PASSWORD=somewordpress
      - MYSQL_DATABASE=wordpress
      - MYSQL_USER=wordpress
      - MYSQL_PASSWORD=wordpress
    expose:
      - 3306
      - 33060
  wordpress:
    image: wordpress:latest
    ports:
      - 9527:80
    restart: always
    environment:
      - WORDPRESS_DB_HOST=db
      - WORDPRESS_DB_USER=wordpress
      - WORDPRESS_DB_PASSWORD=wordpress
      - WORDPRESS_DB_NAME=wordpress
volumes:
  db_data:
```

## Example: Directory Structure

```
target
├── image.tar.gz
├── django
│   ├── app
│   │   ├── Dockerfile
│   │   ├── example
│   │   │   ├── __init__.py
│   │   │   ├── settings.py
│   │   │   ├── urls.py
│   │   │   └── wsgi.py
│   │   ├── manage.py
│   │   └── requirements.txt
│   ├── compose.yaml
│   └── README.md
└── wordpress-mysql
    └── compose.yml
```

## Resource Timing

**FROM_POSTINST_TO_PREUNINST**
- Acquire(): Creates/updates and builds projects
- Release(): Deletes projects

**FROM_STARTUP_TO_HALT**
- Acquire(): Starts projects
- Release(): Stops projects

## Technical Notes

- Environment variables: None specified
- Not updatable: This resource cannot be updated post-installation
- Requires ContainerManager>=1432 for DSM 7.2.1+
