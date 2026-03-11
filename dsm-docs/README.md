# Synology DSM Package Developer Guide

Reference documentation from https://help.synology.com/developer-guide/ for building a NetBird client package for Synology DiskStation.

## Quick Reference

- [Release Notes](release_notes.md) | [Breaking Changes (DSM 7.0)](breaking_changes.md)

## Getting Started
- [Overview](getting_started/gettingstarted.md) - What packages can do, development workflow
- [System Requirements](getting_started/system_requirement.md) - Toolkit requirements, dev tokens
- [Prepare Environment](getting_started/prepare_environment.md) - Toolkit install, chroot deployment
- [First Package](getting_started/first_package.md) - Template, build, test walkthrough

## Synology Toolkit
- [Overview](toolkit/toolkit.md) - Two-stage build workflow
- [Build Stage](toolkit/build_stage.md) - Compilation, depends, cross-compiler variables
- [Pack Stage](toolkit/pack_stage.md) - SPK creation, INFO.sh, platform functions
- [Sign Package](toolkit/sign_package.md) - GPG signing (DSM 6.x only, deprecated)
- [References](toolkit/references.md) - PkgCreate.py options, platform-specific deps

## Synology Package Structure
- [Introduction](synology_package/introduction.md) - SPK layout, component table
- [INFO File](synology_package/INFO.md) - Key/value format overview
- [INFO Necessary Fields](synology_package/INFO_necessary_fields.md) - package, version, os_min_ver, arch, etc.
- [INFO Optional Fields](synology_package/INFO_optional_fields.md) - Display, ports, UI, silent ops, etc.
- [package.tgz](synology_package/package_tgz/package_tgz.md) - Archive contents, install locations
- [UI Files / Launch App](synology_package/package_tgz/launch_app.md) - Vue.js app, webpack, config
- [Scripts](synology_package/scripts.md) - Lifecycle scripts, execution order
- [Script Environment Variables](synology_package/script_env_var.md) - SYNOPKG_* variables
- [Script Messages](synology_package/show_massage.md) - Logging, desktop notifications
- [conf Folder](synology_package/conf.md) - privilege, resource, PKG_DEPS, PKG_CONX
- [PKG_DEPS](synology_package/pkgdeps.md) - Package dependencies with OS restrictions
- [PKG_CONX](synology_package/pkgconx.md) - Package conflicts with OS restrictions
- [Wizard UI Files](synology_package/wizard/intro.md) | [WIZARD_UIFILES v2](synology_package/wizard/WIZARD_UIFILES_v2.md)
- [LICENSE](synology_package/license.md)

## DSM Integration
- [Overview](integrate_dsm/integration.md)
- [FHS (Filesystem Hierarchy)](integrate_dsm/fhs.md) - Directory structure, ownership rules
- [Desktop Application](integrate_dsm/desktopapp.md) - dsmuidir, dsmappname setup
- [Application Config](integrate_dsm/config.md) - JSON config for DSM menu apps
- [Application Help](integrate_dsm/dsm_help.md) - helptoc.conf, help documents
- [I18N](integrate_dsm/i18n.md) - Internationalization strings
- [Web Authentication](integrate_dsm/web_authentication.md) - authenticate.cgi usage
- [Port Configuration](integrate_dsm/ports.md) - .sc files, firewall integration
- [Resource Monitor](integrate_dsm/resource_monitor.md) - systemd slice config

## Privilege
- [Overview](privilege/preface.md) - Why lower privilege is required
- [Privilege Config](privilege/privilege_config.md) - run-as, tool, capabilities, ctrl-script

## Resource Acquisition
- [Overview](resource_acquisition/resources.md) - Setup steps, worker concept
- [Resource Specification](resource_acquisition/resource_specification.md) - JSON format
- [Timing](resource_acquisition/timing.md) - WHEN_PREINST through WHEN_HALT
- [Resource Update](resource_acquisition/config_update.md) - synopkghelper usage
- [Available Workers](resource_acquisition/available_workers.md) - Full list

### Workers
- [/usr/local Linker](resource_acquisition/usrlocal_linker.md)
- [Apache 2.2](resource_acquisition/apache22.md)
- [Data Share](resource_acquisition/data_share.md)
- [Docker](resource_acquisition/docker.md)
- [Docker Project](resource_acquisition/docker-project.md)
- [Index DB](resource_acquisition/index_db.md)
- [MariaDB 10](resource_acquisition/maria_db_10.md)
- [PHP INI](resource_acquisition/php_ini.md)
- [Port Config](resource_acquisition/port_config.md)
- [Systemd User Unit](resource_acquisition/systemd_user_unit.md)
- [System Notification](resource_acquisition/sysnotify.md)
- [Syslog Config](resource_acquisition/syslog_config.md)
- [Web Service](resource_acquisition/web_service.md)
- [Web Config](resource_acquisition/web_config.md)

## Examples
- [Overview](examples/examples.md)
- [Compile tmux](examples/compile_tmux.md)
- [Compile nmap](examples/compile_nmap.md)
- [Docker Package](examples/compile_docker_package.md)
- [Web Package](examples/compile_web_package.md)

## Publishing
- [Overview](publish_package/publish.md)
- [Getting Started](publish_package/get_start.md)
- [Submit for Approval](publish_package/summit_package_for_approval.md)
- [Respond to Issues](publish_package/repond_to_user_issue.md)

## Appendix
- [Platform Architectures](appendix/platarchs.md)
- [Publication Review](appendix/publication_review.md)
- [Manual Compilation](compile_applications/manual.md)
- [Download DSM Toolchain](compile_applications/download_dsm_tool_chain.md)
- [Compile Applications](compile_applications/compile.md)
- [Compile Open Source](compile_applications/compile_open_source_projects.md)

### UI Framework
- [Overview](appendix/ui_framework/ui_framework.md)
- [Application](appendix/ui_framework/application.md)
- [Button](appendix/ui_framework/button.md)
- [Checkbox](appendix/ui_framework/checkbox.md)
- [Form](appendix/ui_framework/form.md)
- [Input](appendix/ui_framework/input.md)
- [Radio](appendix/ui_framework/radio.md)
- [Rich Text](appendix/ui_framework/rich_text.md)
- [Select](appendix/ui_framework/select.md)

---

## Project Research

- [NetBird Client Research](netbird-research.md) - Build system, capabilities, config paths, CLI flags, ports
- [Synology VPN Research](synology-vpn-research.md) - WireGuard/TUN on DSM, Go cross-compilation, kernel modules

## Key Info for NetBird DSM Package

**Architecture decisions:**
- Use `wireguard-go` (bundled in NetBird) - no kernel WireGuard module needed
- Run as `package` user with capabilities (`cap_net_admin`, `cap_net_raw`)
- Consider userspace networking mode to avoid TUN device issues on DSM 7
- Static Go binary: `CGO_ENABLED=0 GOOS=linux GOARCH=amd64`
- Target DSM 7.0+ (`os_min_ver="7.0-40000"`)

**Most relevant DSM docs:**
- **Getting Started** + **First Package** - Basic workflow
- **INFO fields** - Package metadata (arch, os_min_ver, etc.)
- **Scripts** - start-stop-status for NetBird daemon lifecycle
- **FHS** - Where config/data files go (`etc/`, `var/`, `target/`)
- **Privilege Config** - Capabilities: `cap_net_admin,cap_net_raw`
- **Port Config** - WireGuard UDP 51820 firewall rules
- **Resource workers** - usr-local-linker, port-config, syslog-config
- **Desktop App / Config** - DSM UI integration via CGI
