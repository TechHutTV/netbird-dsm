# Breaking Changes in DSM 7.0

## Package Framework Changes

**1. Mandatory Lower Privilege Configuration**
Packages must now include `conf/privilege` with explicit `package` designation in `run-as`. Operations requiring elevated permissions should utilize resource workers.

**2. Required INFO Fields**
All packages must include: `package`, `version`, `os_min_ver`, `description`, `arch`, and `maintainer`. The `os_min_ver` value must be at least `7.0-40000` for proper installation.

**3. Package Signing Removal**
The signing mechanism during the packing stage has been eliminated.

**4. Elimination of `run-as system`**
Packages can no longer execute with system-level privileges in `conf/privilege`. All packages must run as `package`.

**5. Home Directory Path Change**
The default home directory shifted from `/var/packages/[package_name]/target` to `/var/packages/[package_name]/home` with 0700 permissions.

**6. Icon Specification Update**
Package icons (`PACKAGE_ICON.PNG`) must now be 64x64 pixels minimum.

**7. FHS Directory Ownership Adjustment**
FHS directory ownership aligns with `conf/privilege` settings.

**8. Package Logging Location Changes**
Control script logs moved to `/var/log/packages/[package_name].log`. Package operation logs remain at `/var/log/synopkg.log`. Developers should monitor `/var/log/messages`.

**9. `prestart` Script Bootup Consideration**
The `prestart` script now executes during bootup to verify package startup capability.

## Package Center Changes

Keyring management and trust level selections have been removed. Non-Synology packages receive installation alerts.

## Command Changes

- `synopkg start` initiates dependent packages
- `synopkg install` enforces UI installation constraints
