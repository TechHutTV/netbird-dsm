# Sign Package (DSM 5.1 - 6.X only)

> **Note:** Signing mechanism is deprecated after DSM7.0. You don't need this if developing for DSM7.0+.

## GPG Key Setup Options

### Option 1: Using Existing GPG Key

Place your private GPG key (generated with GPG 2.1, without passphrase) in:

```
/toolkit/build_env/ds.${platform}-6.2/root/.gnupg/
```

### Option 2: Installing GPG from Distribution

```bash
apt-get install gpg gpg-agent
```

### Option 3: Docker-Based GPG Setup

```bash
mkdir /tmp/gpgkey
docker run --rm -it -v /tmp/gpgkey:/root/.gnupg -e GPG_TTY=/dev/console vladgh/gpg:0.2.3 --gen-key
mv /tmp/gpgkey /path/to/build_env/ds.avoton-6.2/root/.gnupg
```

## Generating GPG Keys

```bash
gpg --gen-key
```

- Select key type: RSA and RSA (default)
- **Leave passphrase empty** (press Enter without typing) — otherwise the build process will FAIL

Copy generated keys to build environment:

```bash
cp ~/.gnupg/* /toolkit/build_env/ds.${platform}-6.2/root/.gnupg/
```

Verify:

```bash
cd /toolkit/build_env/ds.${platform}-6.2/
chroot .
gpg -K
```

## Signing Packages

### Automatic

```bash
PkgCreate.py -i ${project}
```

### Manual

```bash
chroot /toolkit/build_env/ds.${platform}-${version}
php /pkgscripts-ng/CodeSign.php [option] --sign=package-path
```

Options:
- `--keydir=keyrings directory` (default: `/root/.gnupg`)
- `--keyfpr=key's fingerprint` (default: first key in directory)

Examples:
```bash
php /pkgscripts-ng/CodeSign.php --sign=phpBB-3.0.12-0031.spk
php /pkgscripts-ng/CodeSign.php --keydir=/root/.gpg --keyfpr=C1BF63CD --sign=phpBB-3.0.12-0031.spk
```
