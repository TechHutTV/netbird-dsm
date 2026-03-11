# INFO Optional Fields

## Display and Branding

- **displayname** - Package name shown in Package Center (defaults to package key)
- **displayname_[lang]** - Localized names (enu, cht, chs, krn, ger, fre, ita, spn, jpn, dan, nor, sve, nld, rus, plk, ptb, ptg, hun, trk, csy)
- **description_[lang]** - Localized descriptions
- **maintainer_url** - Developer webpage link (DSM 4.2+)
- **distributor** - Publisher name (DSM 4.2+)
- **distributor_url** - Publisher webpage link (DSM 4.2+)

## Support and Help

- **support_url** - Technical support link
- **support_center** - "yes" to launch Synology Support Center (DSM 5.0+)
- **helpurl** - Help webpage hyperlink (DSM 3.2+)
- **report_url** - Beta version report webpage

## Installation Control

- **install_reboot** - Reboot after install/upgrade ("yes"/"no")
- **install_dep_packages** - Required packages (colon-separated, supports version operators: =, <, >, >=, <=)
- **install_conflict_packages** - Conflicting packages
- **install_break_packages** - Packages to stop and break (DSM 6.1+)
- **install_replace_packages** - Packages to remove (DSM 6.1+)
- **install_dep_services** - Required services: apache-web, mysql, ssh, pgsql, nginx.service, avahi.service, etc.
- **start_dep_services** - Services required before start
- **install_type** - "system" for root filesystem installation (DSM 5.0+)

## Port and UI Configuration

- **adminport** - Package listening port (0-65536, default: 80)
- **adminurl** - Package webpage path (combined: adminprotocol://ip:adminport/adminurl)
- **adminprotocol** - "http" or "https" (default: http)
- **checkport** - Verify port conflicts ("yes"/"no", default: "yes")
- **dsmuidir** - DSM UI folder in package.tgz; supports multiple key:value pairs (DSM 7.0+)
- **dsmappname** - DSM config property names (space-separated)
- **dsmapppage** - Application page for open button (DSM 7.0+)
- **dsmapplaunchname** - Desktop app launch name (DSM 7.0+)

## Package Control

- **startable** - Allow start/stop ("yes"/"no", deprecated after DSM 6.1)
- **ctl_stop** - Control stop capability ("yes"/"no", default: "yes", DSM 6.1+)
- **ctl_uninstall** - Allow uninstallation ("yes"/"no", default: "yes", DSM 6.1+)
- **precheckstartstop** - Run prestart/prestop ("yes"/"no", default: "yes", DSM 6.0+)
- **model** - Restrict to specific Synology models
- **exclude_arch** - Architectures where package cannot install
- **exclude_model** - Models where package cannot install (DSM 7.0+)

## Version and Release

- **beta** - Mark as beta ("yes"/"no")
- **checksum** - MD5 string for package.tgz verification
- **extractsize** - Minimum installation space (bytes DSM <=5.2; kilobytes DSM 6.0+)
- **os_max_ver** - Maximum DSM version (format: X.Y-Z, DSM 6.1+)
- **auto_upgrade_from** - Minimum version for auto upgrades (DSM 5.2+)

## Silent Operations

- **silent_install** - Background installation without wizard ("yes"/"no")
- **silent_upgrade** - Background upgrade without wizard ("yes"/"no")
- **silent_uninstall** - Background uninstallation without wizard ("yes"/"no")
- **offline_install** - Hidden from server list but manually installable (DSM 6.0+)

## Storage and Replacement

- **support_move** - Allow relocation to different volume ("yes"/"no", DSM 6.2+)
- **install_on_cold_storage** - Enable cold storage installation ("yes"/"no", DSM 7.0+)
- **use_deprecated_replace_mechanism** - Legacy replacement behavior (DSM 7.0+)
- **thirdparty** - Mark as third-party ("yes"/"no", DSM 4.0-4.3 only)
