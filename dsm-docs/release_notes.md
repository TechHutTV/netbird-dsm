# Synology Package Framework Release Notes

## Synology Package Framework 7.2

### Notes

**Package Framework:**
- "Implementing a wizard using the Vue.js framework and compile by owner"

## Synology Package Framework 7.0

### Breaking Changes

The framework introduced substantial modifications detailed in the breaking changes documentation.

### Notes

#### Package Framework Changes
- Enforced lower privilege levels for packages
- Made certain INFO fields mandatory
- Eliminated package signing requirements
- Removed `run-as system` privilege option
- Shifted default home path from `target` to `home`
- Updated PACKAGE_ICON.PNG dimensions from 72x72 to 64x64
- Adjusted FHS directory ownership based on privilege configuration
- Moved package logging to `/var/log/packages/[package_name].log` and `/var/log/synopkg.log`
- Applied `prestart` script execution during system boot

#### Package Center Updates
- Removed keyring functionality
- Eliminated trust level verification

#### Command Modifications
- `synopkg start` now initiates packages with their dependents
- `synopkg install` validates installation feasibility

### New Features

#### SDK Plugin Additions
- `package_install` module
- `package_uninstall` module
- `package_start` module
- `package_stop` module

#### Package Framework Additions
- `var`, `tmp`, and `home` FHS directories
- `prereplace` and `postreplace` scripts
- INFO fields: `install_on_cold_storage`, `exclude_model`, `dsmapppage`, `use_deprecated_replace_mechanism`
- Multiple directory support for `dsmuidir`

#### Resource Worker Enhancements
- `strong-dependence` for data-share worker (auto-start after encrypted share mounting)
- `systemd-user-unit` worker support

### Enhancements

#### Package Framework
- Packages restart according to previous operational state post-repair
- Prevents installation if SPK checksum validation fails

#### Package Center
- Start packages with dependencies
- Stop packages with dependents
- Uninstall packages with dependents
- Repair failed packages via repair interface
- Community sources require matching names
