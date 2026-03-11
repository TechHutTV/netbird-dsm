# Compile Open Source Projects

## Overview

The typical compilation process for open source projects involves three main steps:

1. `configure`
2. `make`
3. `make install`

## Configure Script Purpose

The configure script basically consists of many lines which are used to check details about the machine on where the software is going to be installed. The script validates system dependencies and will terminate if critical requirements are missing.

## Cross-Compilation Requirements

When targeting specific machines via cross-compilation, you must specify several environment variables: `CC`, `LD`, `RANLIB`, `CFLAGS`, `LDFLAGS`, `host`, `target`, and `build`. These values are available in `/env32.mak` or `/env64.mak` within your chroot environment.

## Example: Intel X86 Platform (DSM 7.0)

```bash
env CC=/usr/local/x86_64-pc-linux-gnu/bin/x86_64-pc-linux-gnu-wrap-gcc \
LD=/usr/local/x86_64-pc-linux-gnu/bin/x86_64-pc-linux-gnu-ld \
RANLIB=/usr/local/x86_64-pc-linux-gnu/bin/x86_64-pc-linux-gnu-ranlib \
CFLAGS="-DSYNOPLAT_F_X86_64 -O2 -include /usr/syno/include/platformconfig.h -DSYNO_ENVIRONMENT -DBUILD_ARCH=64 -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -g -DSDK_VER_MIN_REQUIRED=600" \
./configure \
    --host=i686-pc-linux-gnu \
    --target=i686-pc-linux-gnu \
    --build=i686-pc-linux \
    --prefix=/usr/local
```
