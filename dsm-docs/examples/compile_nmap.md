# Open Source Tool: nmap - Build Guide

## Overview

This documentation covers compiling the nmap open-source network scanning program for Synology DSM systems using the Package Toolkit, with avoton as the build platform.

## Project Preparation

### Download Commands
```bash
git clone https://github.com/SynologyOpenSource/ExamplePackages.git
cp -a ExamplePackages/libpcap /toolkit/source
cp -a ExamplePackages/nmap /toolkit/source
```

### Source Code URLs
```
wget https://nmap.org/dist/nmap-7.91.tar.bz2
wget http://www.tcpdump.org/release/libpcap-1.9.1.tar.gz
```

## Project Layout Structure

```
/toolkit/
├── build_env/
│   └── ds.${platform}-${version}/
│       └── /usr/syno/
│           ├── bin
│           ├── include
│           └── lib
├── pkgscripts-ng/
└── source/
    ├──nmap/
    │   ├── nmap related source code
    │   ├── SynoBuildConf/
    │   |   ├── build
    │   |   ├── depends
    │   |   └── install
    |   └── synology
    │       ├── PACKAGE_ICON.PNG
    │       ├── PACKAGE_ICON_256.PNG
    │       ├── INFO.sh
    │       ├── conf/
    │       |   ├── privilege
    │       |   └── resource
    │       └── scripts/
    └──libpcap/
        ├── libpcap related source code
        ├── Makefile
        └── SynoBuildConf/
            ├── build
            ├── depends
            ├── install-dev
            └── install
```

## SynoBuildConf/depends Files

### nmap depends
```
[BuildDependent]
libpcap

[default]
all="7.0"
```

### libpcap depends
```
[BuildDependent]

[default]
all="7.0"
```

## SynoBuildConf/build for nmap

```bash
#!/bin/sh
# Copyright (c) 2000-2022 Synology Inc. All rights reserved.

PKG_NAME=nmap
INST_DIR=/tmp/_${PKG_NAME}

case ${MakeClean} in
    [Yy][Ee][Ss])
        make distclean
        ;;
esac

LDFLAGS+=$(shell pkg-config --libs libnl libnl-genl)

env CC="${CC}" CXX="${CXX}" LD="${LD}" AR=${AR} STRIP=${STRIP} RANLIB=${RANLIB} NM=${NM} \
    CFLAGS="${CFLAGS}" CXXFLAGS="$CXXFLAGS $CFLAGS" \
    LDFLAGS="${LDFLAGS} -ldbus-1" \
    ./configure ${ConfigOpt} \
    --prefix=${INST_DIR} \
    --without-ndiff \
    --without-zenmap \
    --without-nping \
    --without-ncat \
    --without-nmap-update \
    --without-liblua \
    --with-libpcap=/usr/local

make ${MAKE_FLAGS}
```

### Environment Variables Required
- CC
- CXX
- LD
- AR
- STRIP
- RANLIB
- NM
- CFLAGS
- CXXFLAGS
- LDFLAGS

### Features Disabled
- ndiff
- zenmap
- nping
- ncat
- nmap-update
- liblua

## SynoBuildConf/build for libpcap

```bash
#!/bin/bash
# Copyright (c) 2000-2022 Synology Inc. All rights reserved.

case ${MakeClean} in
    [Yy][Ee][Ss])
        make distclean
        ;;
esac

case ${CleanOnly} in
    [Yy][Ee][Ss])
        return
        ;;
esac

# prefix with /usr/local, all files will be installed into /usr/local
env CC="${CC}" CXX="${CXX}" LD="${LD}" AR=${AR} STRIP=${STRIP} RANLIB=${RANLIB} NM=${NM} \
    CFLAGS="${CFLAGS} -Os" CXXFLAGS="${CXXFLAGS}" LDFLAGS="${LDFLAGS}" \
    ./configure ${ConfigOpt} \
    --with-pcap=linux --prefix=/usr/local

make ${MAKE_FLAGS}

make install
```

## SynoBuildConf/install

```bash
#!/bin/bash
# Copyright (c) 2000-2022 Synology Inc. All rights reserved.

PKG_NAME="nmap"
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

SetupPackageFiles() {
    make install
    synology/INFO.sh > INFO
    cp INFO "${PKG_DIR}"
    cp -r synology/conf/ "${PKG_DIR}"
    cp -r synology/scripts/ "${PKG_DIR}"
    cp synology/PACKAGE_ICON{,_256}.PNG "${PKG_DIR}"
}

MakePackage() {
    source /pkgscripts-ng/include/pkg_util.sh
    pkg_make_package $INST_DIR $PKG_DIR
    pkg_make_spk $PKG_DIR $PKG_DEST
}

main() {
    PrepareDirs
    SetupPackageFiles
    MakePackage
}

main "$@"
```

## Configuration Files

### conf/resource
```json
{
    "usr-local-linker": {
        "bin": ["bin/nmap"]
    }
}
```

### conf/privilege
```json
{
    "defaults": {
        "run-as": "package"
    }
}
```

## INFO.sh

```bash
#!/bin/sh
# Copyright (c) 2000-2022 Synology Inc. All rights reserved.

. /pkgscripts-ng/include/pkg_util.sh
package="nmap"
version="7.91-1001"
os_min_ver="7.0-40850"
displayname="nmap"
arch="$(pkg_get_platform) "
maintainer="Synology Inc."
description="This package will install nmap in your DSM system."
[ "$(caller)" != "0 NULL" ] && return 0
pkg_dump_info
```

## Build Command

```bash
/toolkit/pkgscripts-ng/PkgCreate.py -p avoton -x0 -c nmap
```

## Verification

After successful compilation, the SPK file appears in `/toolkit/result_spk`. Install via Package Center and test with: `nmap -v -A localhost`. Error logs are found at `/var/log/messages` if installation fails.

## Key Technical Details

**Cross-Compilation Steps:** The build process requires configure, make, and make install execution. The configure script checks machine details and dependencies. For cross-compilation, specify CC, LD, RANLIB, CFLAGS, LDFLAGS, host, target, and build parameters.

**Dependency Resolution:** nmap depends on libpcap; "BuildDependent" field ensures correct compilation order.

**libpcap Installation:** Cross-compiled libpcap installs to `/usr/local` in the chroot environment, allowing nmap to locate it during configuration.
