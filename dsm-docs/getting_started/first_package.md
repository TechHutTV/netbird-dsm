# Your First Package

## Template Package

Download from [GitHub ExamplePackages repository](https://github.com/SynologyOpenSource/ExamplePackages) and place at `/toolkit/source/ExamplePackage`.

### Directory Structure

```
/toolkit/
├── build_env/
│   └── ds.${platform}-${version}/
├── pkgscripts-ng/
│   ├── EnvDeploy
│   └── PkgCreate.py
└── source/
    └── ExamplePackage/
        ├── examplePkg.c
        ├── INFO.sh
        ├── Makefile
        ├── PACKAGE_ICON.PNG
        ├── PACKAGE_ICON_256.PNG
        ├── scripts/
        │   ├── postinst
        │   ├── postuninst
        │   ├── postupgrade
        │   ├── postreplace
        │   ├── preinst
        │   ├── preuninst
        │   ├── preupgrade
        │   ├── prereplace
        │   └── start-stop-status
        └── SynoBuildConf/
            ├── depends
            ├── build
            └── install
```

## Build Configuration

Three files in `${project_path}/SynoBuildConf/`:

- **depends**: Project dependency configuration
- **build**: Build step configuration
- **install**: Package packing into `.spk` file configuration

## INFO.sh Configuration

```bash
#!/bin/bash
source /pkgscripts/include/pkg_util.sh
package="ExamplePackage"
version="1.0.0000"
os_min_ver="7.0-40000"
displayname="ExamplePackage Package"
description="this is an example package"
arch="$(pkg_get_unified_platform)"
maintainer="Synology Inc."
pkg_dump_info
```

## Package Lifecycle Scripts

Located at `${project_path}/scripts/`:

```bash
#!/bin/sh
# scripts/start-stop-status
case $1 in
    start)
        examplePkg "Start"
        echo "Hello World" > $SYNOPKG_TEMP_LOGFILE
        exit 0
    ;;
    stop)
        examplePkg "Stop"
        echo "Hello World" > $SYNOPKG_TEMP_LOGFILE
        exit 0
    ;;
    status)
        exit 0
    ;;
esac
```

## Example C Program

```c
#include <sys/sysinfo.h>
#include <syslog.h>
#include <stdio.h>
int main(int argc, char** argv) {
    struct sysinfo info;
    int ret;
    ret = sysinfo(&info);
    if (ret != 0) {
        syslog(LOG_SYSLOG, "Failed to get info\n");
        return -1;
    }
    syslog(LOG_SYSLOG, "[ExamplePkg] %s sample package ...", argv[1]);
    syslog(LOG_SYSLOG, "[ExamplePkg] Total RAM: %u\n", (unsigned int) info.totalram);
    syslog(LOG_SYSLOG, "[ExamplePkg] Free RAM: %u\n", (unsigned int) info.freeram);
    return 0;
}
```

## Makefile

```makefile
include /env.mak
EXEC= examplePkg
OBJS= examplePkg.o
all: $(EXEC)
$(EXEC): $(OBJS)
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)
install: $(EXEC)
	mkdir -p $(DESTDIR)/usr/bin/
	install $< $(DESTDIR)/usr/bin/
clean:
	rm -rf *.o $(EXEC)
```

## Install Build Script

```bash
# SynoBuildConf/install
create_package_tgz() {
    local firewere_version=
    local package_tgz_dir=/tmp/_package_tgz
    local binary_dir=$package_tgz_dir/usr/bin
    rm -rf $package_tgz_dir && mkdir -p $package_tgz_dir
    mkdir -p $binary_dir
    cp -av examplePkg $binary_dir
    make install DESTDIR="$package_tgz_dir"
    pkg_make_package $package_tgz_dir "${PKG_DIR}"
}
```

## Build and Pack Commands

```bash
cd /toolkit/pkgscripts-ng/
./PkgCreate.py -v 7.0 -p avoton -c ExamplePackage
```

Output structure:

```
/toolkit/
├── pkgscripts-ng/
├── build_env/
│   └── ds.${platform}-${version}
└── result_spk/
    └── ${package}-${version}/
        └── *.spk
```

## Installation and Testing

1. Navigate to **DSM > Package Center > Manual Install**
2. Select the generated `.spk` file
3. View package messages in UI and logs at `/var/log/messages`
