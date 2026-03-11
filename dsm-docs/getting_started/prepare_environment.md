# Prepare Environment

## Install Toolkit

### Clone and Install

```bash
apt-get install git
mkdir -p /toolkit
cd /toolkit
git clone https://github.com/SynologyOpenSource/pkgscripts-ng
```

Install required dependencies:

```bash
apt-get install cifs-utils \
    python \
    python-pip \
    python3 \
    python3-pip
```

### Directory Structure

```
/toolkit
├── pkgscripts-ng/
│   ├── include/
│   ├── EnvDeploy    (deployment tool for chroot environment)
│   └── PkgCreate.py (build tool for package)
└── build_env/       (directory to store chroot environments)
```

## Deploy Chroot Environment For Different NAS Target

Pre-built environments containing binaries and libraries (zlib, libxml2, etc.) are available for different architectures.

### Deployment Command

Deploy environment for a specific architecture (example: avoton for DSM 7.2.2):

```bash
cd /toolkit/pkgscripts-ng/
git checkout DSM7.2
./EnvDeploy -v 7.2 -p avoton
```

### Manual Environment Download

Place tarballs in the toolkit_tarballs directory:

```
/toolkit
├── pkgscripts-ng/
└── toolkit_tarballs/
    ├── base_env-7.2.txz
    ├── ds.avoton-7.2.dev.txz
    └── ds.avoton-7.2.env.txz
```

Deploy without downloading:

```bash
cd /toolkit/pkgscripts-ng/
./EnvDeploy -v 7.2 -p avoton -D
```

### Cross Compiler Sysroot

The environment includes pre-built libraries and headers:

```
/toolkit
├── pkgscripts-ng/
└── build_env/
    ├── ds.avoton-7.2/
    └── ds.avoton-6.2/
        └── usr/local/x86_64-pc-linux-gnu/x86_64-pc-linux-gnu/sys-root/
```

## Available Platforms

List available platforms:

```bash
./EnvDeploy -v 7.2 --list
./EnvDeploy -v 7.2 --info platform
```

Platform families allow using any toolkit from the same family to create packages for compatible platforms (e.g., braswell toolkit for all x86_64 compatible platforms).

## Update Environment

```bash
./EnvDeploy -v 7.2 -p avoton
```

## Remove Environment

```bash
umount /toolkit/build_env/ds.avoton-7.2/proc
rm -rf /toolkit/build_env/ds.avoton-7.2
```
