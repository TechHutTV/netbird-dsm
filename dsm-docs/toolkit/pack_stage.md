# Pack Stage

## Overview

The Pack Stage uses `PkgCreate.py` to assemble necessary files according to metadata and create a `.spk` file in `/toolkit/result_spk`. Running with the `-i` option skips the Build Stage:

```bash
cd /toolkit
pkgscripts-ng/PkgCreate.py -i ${project}
```

## Pack Stage Workflow

1. **Execute install script** - Runs `SynoBuildConf/install`
   - Creates `INFO` file via `INFO.sh`
   - Moves files to `/tmp/_install` and creates `package.tgz`
   - Moves metadata to `/tmp/_pkg` and creates `.spk` file

2. **Sign package** - Signs `.spk` with GPG key from `/root/` (deprecated after DSM7.0)

## SynoBuildConf/install Script

Must be written in bash. Current working directory is `/source/${project}` under chroot.

```bash
#!/bin/bash
PKG_DIR=/tmp/_test_spk
rm -rf $PKG_DIR
mkdir -p $PKG_DIR

source /pkgscripts-ng/include/pkg_util.sh

create_inner_tarball() {
    local inner_tarball_dir=/tmp/_inner_tarball
    rm -rf $inner_tarball_dir && mkdir -p $inner_tarball_dir
    make install DESTDIR="$inner_tarball_dir"
    pkg_make_package $inner_tarball_dir "${PKG_DIR}"
}

create_spk(){
    local scripts_dir=$PKG_DIR/scripts
    mkdir -p $scripts_dir
    cp -av scripts/* $scripts_dir
    cp -av PACKAGE_ICON*.PNG $PKG_DIR
    ./INFO.sh > INFO
    cp INFO $PKG_DIR/INFO
    mkdir -p /image/packages
    pkg_make_spk ${PKG_DIR} "/image/packages" $(pkg_get_spk_family_name)
}

create_inner_tarball
create_spk
```

## INFO.sh Script

```bash
#!/bin/bash
source /pkgscripts-ng/include/pkg_util.sh

package="ExamplePkg"
version="1.0.0000"
displayname="Example Package"
maintainer="Synology Inc."
arch="$(pkg_get_unified_platform)"
description="this is a Example package"
[ "$(caller)" != "0 NULL" ] && return 0
pkg_dump_info
```

## SPK Packing Functions

After importing `/pkgscripts-ng/include/pkg_util.sh`:

### Core Functions

- `pkg_make_package $1 $2` - Creates `package.tgz` of $2 from files in $1
- `pkg_make_spk $1 $2` - Creates `.spk` of $2 from files in $1

### Platform Functions

| Function | Values | Description |
|----------|--------|-------------|
| (No function) | noarch | Script-only packages; runs on all models |
| pkg_get_platform_family | x86_64, i686, armv7, armv5, ppc... | Unifies platforms with same kernel |
| pkg_get_spk_platform | bromolow, cedarview, qoriq, armadaxp... | Specific platform only |

### SPK Naming Functions

| Function | Platform Function | Example |
|----------|------------------|---------|
| pkg_get_spk_name | pkg_get_spk_platform | examplePkg-bromolow-1.0.0000.spk |
| pkg_get_spk_name | noarch | examplePkg-1.0.0000.spk |
| pkg_get_spk_family_name | pkg_get_platform_family | examplePkg-x86_64-1.0.0000.spk |

### SPK Creation

```bash
pkg_make_spk $source_path $dest_path $spk_name
```

Example:
```bash
pkg_make_spk /tmp/_test_spk "/image/packages" $(pkg_get_spk_family_name)
```
