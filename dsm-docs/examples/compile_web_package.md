# Web Package: WordPress

## Overview
This documentation provides a comprehensive guide for building a PHP-based WordPress web package that integrates with Synology DSM, specifically using WebStation, MariaDB, and Apache server.

## Key Requirements

**Dependencies needed before installation:**
- WebStation (>=3.0.0-0226)
- MariaDB10
- PHP7.3 (>=7.3.16-0150)
- Apache2.2 (>=2.2.34-0104)

## Project Structure

```
/toolkit/source/wordpress_sample
├── PACKAGE_ICON.PNG
├── PACKAGE_ICON_256.PNG
├── conf/
│   ├── privilege
│   └── resource
├── INFO.sh
├── Makefile
├── scripts/
│   ├── postinst
│   ├── postuninst
│   ├── postupgrade
│   ├── preinst
│   ├── preuninst
│   ├── preupgrade
│   ├── script_customized
│   └── start-stop-status
├── src/wordpress/
├── SynoBuildConf/
│   ├── build
│   ├── depends
│   └── install
└── ui/ (icon files)
```

## INFO.sh Configuration

```bash
#!/bin/bash
package="wordpress_sample"
. "/pkgscripts-ng/include/pkg_util.sh"
version="5.5.1-1001"
os_min_ver="7.0-40337"
startstop_restart_services="nginx.service"
instuninst_restart_services="nginx.service"
install_dep_packages="WebStation>=3.0.0-0226:MariaDB10:PHP7.3>=7.3.16-0150:Apache2.2>=2.2.34-0104"
install_provide_packages="WEBSTATION_SERVICE"
maintainer="WordPress"
thirdparty="yes"
silent_upgrade="yes"
arch="noarch"
adminprotocol="http"
adminport="80"
adminurl="wordpress"
dsmuidir="ui"

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
INST_DIR="/tmp/_WordPress"
PKG_DIR="/tmp/_WordPress_pkg"
PKG_DEST="/image/packages"

for dir in $INST_DIR $PKG_DIR; do
    rm -rf "$dir"
done
for dir in $INST_DIR $PKG_DIR $PKG_DEST; do
    mkdir -p "$dir"
done

make INSTALLDIR=$INST_DIR install
make PACKAGEDIR=$PKG_DIR package

. "/pkgscripts-ng/include/pkg_util.sh"
pkg_make_package $INST_DIR $PKG_DIR
pkg_make_spk $PKG_DIR $PKG_DEST
```

## Makefile

```makefile
WORDPRESSDIR=src
WORDPRESS_INSTALL_DIR=$(INSTALLDIR)/$(WORDPRESSDIR)

all clean:

.PHONY:

install:
	[ -d $(INSTALLDIR) ] || install -d $(INSTALLDIR)
	[ -d $(WORDPRESS_INSTALL_DIR) ] || install -d $(WORDPRESS_INSTALL_DIR)
	cp -a $(WORDPRESSDIR)/* $(WORDPRESS_INSTALL_DIR)
	[ -d $(INSTALLDIR)/ui ] || install -d $(INSTALLDIR)/ui
	cp -a ui/* $(INSTALLDIR)/ui
	chown -R http:http $(WORDPRESS_INSTALL_DIR)

INFO: INFO.sh
	env UISTRING_PATH=$(STRING_DIR) ./INFO.sh > INFO

package: INFO
	[ -d $(PACKAGEDIR) ] || install -d $(PACKAGEDIR)
	[ -d $(PACKAGEDIR)/scripts ] || install -d $(PACKAGEDIR)/scripts
	cp -a scripts/* $(PACKAGEDIR)/scripts
	chmod 755 $(PACKAGEDIR)/scripts/*
	cp -a PACKAGE_ICON.PNG $(PACKAGEDIR)
	cp -a PACKAGE_ICON_256.PNG $(PACKAGEDIR)
	cp -a conf $(PACKAGEDIR)
	install -c -m 644 INFO $(PACKAGEDIR)

clean:
```

## Scripts

### preinst
```bash
#!/bin/sh
exit 0
```

### postinst
```bash
#!/bin/sh
WEBSITE_ROOT="/var/services/web_packages/wordpress"
chown -R WordPress:http "$WEBSITE_ROOT/*"
exit 0
```

### preuninst
```bash
#!/bin/sh
exit 0
```

### postuninst
```bash
#!/bin/sh
exit 0
```

### preupgrade
```bash
#!/bin/sh
exit 0
```

### postupgrade
```bash
#!/bin/sh
exit 0
```

### start-stop-status
```bash
#!/bin/sh
case "$1" in
    start)
        exit 0
        ;;
    stop)
        exit 0
        ;;
    status)
        exit 0
        ;;
    *)
        exit 1
        ;;
esac
```

## Privilege Configuration

```json
{
    "defaults": {
        "run-as": "package"
    },
    "username": "WordPress",
    "join-groupname": "http"
}
```

## Resource Configuration (WebService Worker)

```json
{
    "webservice": {
        "services": [{
            "service": "wordpress",
            "display_name": "WordPress",
            "support_alias": true,
            "support_server": true,
            "type": "apache_php",
            "root": "wordpress",
            "backend": 1,
            "icon": "ui/Wordpress_{0}.png",
            "php": {
                "profile_name": "WordPress Profile",
                "profile_desc": "PHP Profile for WordPress",
                "backend": 7,
                "open_basedir": "/var/services/web_packages/wordpress:/tmp:/var/services/tmp",
                "extensions": [
                    "mysql",
                    "mysqli",
                    "pdo_mysql",
                    "curl",
                    "gd",
                    "iconv"
                ],
                "php_settings": {
                    "mysql.default_socket": "/run/mysqld/mysqld10.sock",
                    "mysqli.default_socket": "mysqli.default_socket",
                    "pdo_mysql.default_socket": "/run/mysqld/mysqld10.sock",
                    "display_errors": "1",
                    "error_reporting": "E_ALL",
                    "log_errors": "true"
                },
                "user": "WordPress",
                "group": "http"
            },
            "connect_timeout": 60,
            "read_timeout": 3600,
            "send_timeout": 60
        }],
        "portals": [{
            "service": "wordpress",
            "type": "alias",
            "name": "wordpress",
            "alias": "wordpress",
            "app": "SYNO.SDS.WordPress"
        }],
        "pkg_dir_prepare": [{
            "source": "/var/packages/WordPress/target/src/wordpress",
            "target": "wordpress",
            "mode": "0755",
            "user": "WordPress",
            "group": "http"
        }]
    }
}
```

## Build Command

```bash
/toolkit/pkgscripts-ng/PkgCreate.py -p avoton -c wordpress_sample
```

Results are placed in `/toolkit/result_spk`.

## Installation Notes

- Create database manually via phpMyAdmin or equivalent
- Database address: `localhost:/run/mysqld/mysqld10.sock` for root user
- To disable nginx error interception:
  1. Locate WordPress nginx configuration
  2. Change `proxy_intercept_errors` from "on" to "off"
  3. Execute `systemctl reload nginx`
