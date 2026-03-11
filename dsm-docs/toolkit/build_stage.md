# Build Stage

## Overview

The Build Stage is where `PkgCreate.py` compiles projects and dependencies using two key build scripts in `SynoBuildConf/`: the `build` and `depends` files.

## Basic Command

```bash
PkgCreate.py -v ${version} -p ${platform} ${project}
```

## Directory Structure

```
/toolkit/
├── build_env/
│   └── ds.${platform}-${version}/
├── pkgscripts-ng/
│   ├── EnvDeploy
│   └── PkgCreate.py
└── source/
    └── ${project}/
        └── SynoBuildConf/
            ├── depends
            ├── build
            └── install
```

## Build Stage Workflow

1. `PkgCreate.py` locates the target DSM version from the `[default]` section of `SynoBuildConf/depends`
2. Projects and dependencies are resolved
3. Projects under `/toolkit/source` are hard-linked to `/toolkit/build_env/ds.${platform}/source`
4. `SynoBuildConf/build` scripts execute in dependency order
5. Optional: `SynoBuildConf/install-dev` script installs cross-compiled products into platform chroot

## SynoBuildConf/depends Configuration

Three required fields:

- **BuildDependent**: Lists dependent projects requiring compilation
- **ReferenceOnly**: Lists referenced projects not requiring build process
- **default**: Specifies toolkit environment — "all" applies version to all platforms

```ini
[default]
all="7.2.2"
```

## Dependency Verification

```bash
cd /toolkit/pkgscripts-ng
./ProjDepends.py -x0 ${project}
```

## SynoBuildConf/build Script

Shell script executed in `/source/${project}` within chroot environment. Cross-compiler sysroot is the default search path.

### Available Variables

| Variable | Purpose |
|----------|---------|
| CC | GCC cross compiler path |
| CXX | G++ cross compiler path |
| LD | Cross compiler linker |
| CFLAGS | Global C compiler flags |
| LDFLAGS | Global linker flags |
| AR | Cross compiler archiver |
| NM | Cross compiler symbol utility |
| STRIP | Cross compiler strip utility |
| RANLIB | Cross compiler ranlib |
| OBJDUMP | Cross compiler objdump |
| ARCH | Processor architecture |
| SYNO_PLATFORM | Synology platform identifier |
| DSM_SHLIB_MAJOR | DSM major version number |
| DSM_SHLIB_MINOR | DSM minor version number |
| DSM_SHLIB_NUM | DSM build number |
| ToolChainSysRoot | Cross compiler sysroot path |
| SysRootPrefix | Sysroot with /usr prefix |
| SysRootInclude | Sysroot with /usr/include |
| SysRootLib | Sysroot with /usr/lib |

## Build Script Example

```bash
# SynoBuildConf/build
case ${MakeClean} in
       [Yy][Ee][Ss])
               make distclean
               ;;
esac

make ${MAKE_FLAGS}
```

## Checking Chroot Dependencies

```bash
dpkg -l                          # List all packages
dpkg -L {project dev}            # List project files
dpkg -S {header/library pattern} # Search for specific files
```

## Example: Verifying zlib

```bash
chroot /toolkit/build_env/ds.avoton-7.0/
>> dpkg -l | grep zlib
ii  zlib-1.x-avoton-dev        7.0-7274       all

>> dpkg -L zlib-1.x-avoton-dev
/usr/local/x86_64-pc-linux-gnu/x86_64-pc-linux-gnu/sys-root/usr/lib/libz.so
/usr/local/x86_64-pc-linux-gnu/x86_64-pc-linux-gnu/sys-root/usr/lib/libz.a
/usr/local/x86_64-pc-linux-gnu/x86_64-pc-linux-gnu/sys-root/usr/lib/pkgconfig/zlib.pc
/usr/local/x86_64-pc-linux-gnu/x86_64-pc-linux-gnu/sys-root/usr/include/zconf.h
/usr/local/x86_64-pc-linux-gnu/x86_64-pc-linux-gnu/sys-root/usr/include/zlib.h
```

## Makefile Example

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
