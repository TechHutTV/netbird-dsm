# Docker Package Compilation Guide

## Overview

This documentation explains how to compile a Docker package using GitLab as an example. The guide covers project structure, configuration files, scripts, and build processes for Synology DSM packages.

## Project Layout

```
docker-gitlab
├── conf
│   ├── privilege
│   └── resource
├── INFO.sh
├── scripts
│   ├── postinst
│   ├── postuninst
│   ├── postupgrade
│   ├── preinst
│   ├── preuninst
│   ├── preupgrade
│   ├── script_customized
│   └── start-stop-status
├── SynoBuildConf
│   ├── build
│   ├── depends
│   └── install
└── ui
    ├── config.png
    ├── Gitlab_120.png
    ├── Gitlab_16.png
    ├── Gitlab_24.png
    ├── Gitlab_256.png
    ├── Gitlab_32.png
    ├── Gitlab_48.png
    ├── Gitlab_64.png
    └── Gitlab_72.png
```

## INFO.sh Configuration

```bash
#!/bin/bash
# Copyright (c) 2000-2022 Synology Inc. All rights reserved.

package="wordpress_sample"

. "/pkgscripts-ng/include/pkg_util.sh"
version="12.9.0-1"
os_min_ver="7.0-40337"
install_dep_packages="Docker>=18.09.0-1017"
maintainer="Gitlab"
thirdparty="yes"
arch="avoton"
adminurl="wordpress"
dsmuidir="ui"
displayname="Gitlab"
package_icon="`/pkgscripts-ng/include/base64.php ${ICON_PATH}`"

[ "$(caller)" != "0 NULL" ] && return 0
pkg_dump_info
```

## SynoBuildConf/depends

```
[default]
all="7.0"
```

## SynoBuildConf/build

```bash
#!/bin/bash
# Copyright (c) 2000-2022 Synology Inc. All rights reserved.

case ${MakeClean} in
    [Yy][Ee][Ss])
        make clean
        ;;
esac

case ${CleanOnly} in
    [Yy][Ee][Ss])
        return
        ;;
esac

make ${MAKE_FLAGS}
```

## SynoBuildConf/install

```bash
#!/bin/bash
# Copyright (c) 2000-2022 Synology Inc. All rights reserved.

# set include projects to install into this package
INST_DIR="/tmp/_Gitlab"      # temp folder for dsm files
PKG_DIR="/tmp/_Gitlab_pkg"   # temp folder for package files
PKG_DEST="/image/packages"

# prepare install and package dir
for dir in $INST_DIR $PKG_DIR; do
        rm -rf "$dir"
done
for dir in $INST_DIR $PKG_DIR $PKG_DEST; do
        mkdir -p "$dir" # use default mask
done

[ -d $INST_DIR/ui ] || install -d $INST_DIR/ui
cp -a ui/* $INST_DIR/ui

[ -d $PKG_DIR ] || install -d $PKG_DIR
[ -d $PKG_DIR/scripts ] || install -d $PKG_DIR/scripts
cp -a conf $PKG_DIR
cp -a scripts/* $PKG_DIR/scripts
chmod 755 $PKG_DIR/scripts/*

./INFO.sh > INFO

install -c -m 644 INFO $PKG_DIR

. "/pkgscripts-ng/include/pkg_util.sh"
pkg_make_package $INST_DIR $PKG_DIR
pkg_make_spk $PKG_DIR $PKG_DEST
```

## UI Configuration

Located in `ui` folder:

```json
{
    ".url": {
        "SYNO.SDS.GitLab": {
            "allUsers": true,
            "desc": "Docker-GitLab",
            "icon": "images/Docker_GitLab_SynoCommunity-{0}.png",
            "port": "@PORT@",
            "protocol": "http",
            "texts": "texts",
            "title": "GitLab",
            "type": "url",
            "url": "/"
        }
    }
}
```

## Scripts

### preinst

```sh
#!/bin/sh

exit 0
```

### postinst

```sh
#!/bin/sh
PKG_NAME="Gitlab"
PORT_CONFIG_FILE="/var/packages/$PKG_NAME/etc/port_config"

port=""
if [ ! -z "$wizard_http_port" ]; then
    # new install
    port="$wizard_http_port"
elif [ -f "$PORT_CONFIG_FILE" ]; then
    # upgrade
    port=$(get_key_value "$PORT_CONFIG_FILE" port)
fi

echo "port=$port" > $PORT_CONFIG_FILE

if [ -f "$SYNOPKG_PKGDEST/app/config" ]; then
    sed -i "s/@PORT@/$port/g" "$SYNOPKG_PKGDEST/ui/config"
fi

exit 0
```

### preuninst

```sh
#!/bin/sh

exit 0
```

### postuninst

```sh
#!/bin/sh
PKG_NAME="Gitlab"
PORT_CONFIG_FILE="/var/packages/$PKG_NAME/etc/port_config"

if [ "$SYNOPKG_PKG_STATUS" = "UNINSTALL" ]; then
    rm -f "$PORT_CONFIG_FILE"
fi

exit 0
```

### preupgrade

```sh
#!/bin/sh

exit 0
```

### postupgrade

```sh
#!/bin/sh

exit 0
```

### start-stop-status

```bash
#!/bin/bash
GITLAB_NAME="GitLab"
DOCKER_INSPECT="/usr/local/bin/docker_inspect"

case "$1" in
    start)
        ;;
    stop)
        ;;
    status)
        "$DOCKER_INSPECT" "$GITLAB_NAME" | grep -q "\"Status\": \"running\"," || exit 1
        ;;
    log)
        echo ""
        ;;
    *)
        echo "Usage: $0 {start|stop|status}" >&2
        exit 1
        ;;
esac
exit 0
```

## Privilege Configuration

Located in `conf/privilege`:

```json
{
    "defaults": {
        "run-as": "package"
    },
    "username": "Gitlab"
}
```

## Resource/Worker Configuration

Located in `conf/resource`:

```json
{
    "docker": {
        "services": [{
            "service": "gitlab",
            "image": "gitlab/gitlab-ce",
            "container_name": "GitLab",
            "tag": "12.9.0-ce.0",
            "restart": "always",
            "shares": [{
                "host_dir": "gitlab/data",
                "mount_point": "/var/opt/gitlab"
            }, {
                "host_dir": "gitlab/logs",
                "mount_point": "/var/log/gitlab"
            }, {
                "host_dir": "gitlab/config",
                "mount_point": "/etc/gitlab"
            }],
            "ports": [{
                "host_port": "{{wizard_http_port}}",
                "container_port": "80",
                "protocol": "tcp"
            }, {
                "host_port": "{{wizard_https_port}}",
                "container_port": "443",
                "protocol": "tcp"
            }, {
                "host_port": "{{wizard_ssh_port}}",
                "container_port": "22",
                "protocol": "tcp"
            }]
        }]
    }
}
```

## Build Command

```bash
/toolkit/pkgscripts-ng/PkgCreate.py -p avoton -c docker-gitlab
```

Output location: `/toolkit/result_spk`

## Key Points

- Docker packages pull or build images on the DSM system
- No code compilation needed during SPK packing
- Use port configuration files for dynamic port assignment
- Docker worker handles container setup automatically
- Install verification through Package Center manual installation
