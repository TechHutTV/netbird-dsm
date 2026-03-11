# Open Source Tool: tmux - Build Guide

## Overview

This documentation explains how to build an open source project (tmux) for Synology DSM using the Package Toolkit. The process involves creating three configuration files before compilation.

## Standard Build Steps

Open source projects typically require:

1. `configure`
2. `make`
3. `make install`

The configure script examines system details and dependencies. Cross-compilation requires specifying: `CC`, `LD`, `RANLIB`, `CFLAGS`, `LDFLAGS`, `host`, `target`, and `build`.

## Project Structure

```
tmux/
    ├── tmux related source code
    ├── SynoBuildConf/
    |   ├── build
    |   ├── depends
    |   └── install
    └── synology
        ├── conf/
        ├── scripts/
        └── INFO.sh
```

## SynoBuildConf/depends

```
[default]
all="7.0"
```

## SynoBuildConf/build

```bash
#!/bin/sh
# Copyright (c) 2000-2022 Synology Inc. All rights reserved.

case ${MakeClean} in
    [Yy][Ee][Ss])
        make distclean
        ;;
esac

NCURSES_INCS="$(pkg-config ncurses --cflags)"
NCURSES_LIBS="$(pkg-config ncurses --libs)"

CFLAGS="${CFLAGS} ${NCURSES_INCS}"
LDFLAGS="${LDFLAGS} ${NCURSES_LIBS}"

autoreconf -if

env CC="${CC}" AR="${AR}" CFLAGS="${CFLAGS}" LDFLAGS="${LDFLAGS}" \
./configure ${ConfigOpt}

make ${MAKE_FLAGS}
```

**Key variables passed to configure:**
- `CC`
- `AR`
- `CFLAGS`
- `LDFLAGS`

The script uses `pkg-config` to resolve ncurses dependencies (headers and libraries).

## SynoBuildConf/install

```bash
#!/bin/bash
# Copyright (c) 2000-2022 Synology Inc. All rights reserved.

PKG_NAME="tmux"
INST_DIR="/tmp/_${PKG_NAME}"
PKG_DIR="/tmp/_${PKG_NAME}_pkg"
PKG_DEST="/image/packages"

PrepareDirs() {
    for dir in $INST_DIR $PKG_DIR; do
        rm -rf "$dir"
    done
    for dir in $INST_DIR $PKG_DIR $PKG_DEST; do
        mkdir -p "$dir"
    done
}

InstallTmux() {
    DESTDIR="${INST_DIR}" make install
}

GenerateINFO() {
    synology/INFO.sh > INFO
    cp INFO "${PKG_DIR}"
}

InstallSynologyConfig(){
    cp -r synology/scripts/ "${PKG_DIR}"
    cp -r synology/conf/ "${PKG_DIR}"
    cp synology/PACKAGE_ICON{,_256}.PNG "${PKG_DIR}"
}

MakePackage() {
    source /pkgscripts/include/pkg_util.sh
    pkg_make_package $INST_DIR $PKG_DIR
    pkg_make_spk $PKG_DIR $PKG_DEST
}

main() {
    PrepareDirs
    InstallTmux
    GenerateINFO
    InstallSynologyConfig
    MakePackage
}

main "$@"
```

Uses `DESTDIR` environment variable to specify installation location.

## INFO.sh

```bash
#!/bin/sh
# Copyright (c) 2000-2022 Synology Inc. All rights reserved.
. /pkgscripts/include/pkg_util.sh
package="tmux"
version="1.9.1-1001"
os_min_ver="7.0-40850"
displayname="tmux"
arch="$(pkg_get_platform) "
maintainer="Synology Inc."
description="Tmux package for Synology DSM."
support_url="https://github.com/tmux/tmux"
thirdparty="yes"
startable="no"
silent_install="yes"
silent_upgrade="yes"
silent_uninstall="yes"
[ "$(caller)" != "0 NULL" ] && return 0
pkg_dump_info
```

**Important:** Set executable permissions on INFO.sh.

## Build Commands

```bash
/toolkit/pkgscripts-ng/PkgCreate.py -p avoton -c tmux
```

Results appear in `/toolkit/result_spk`.

## Verification

- Check `/toolkit/result_spk` for the .spk file
- Install via Package Center
- Connect via SSH to test the `tmux` command
- Review `/var/log/messages` for error logs if installation fails
