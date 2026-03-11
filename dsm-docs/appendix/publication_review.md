# Appendix C: Publication Review & Verification

## Package Review Guidelines

Synology provides specific review criteria for packages submitted to their ecosystem. The review process evaluates multiple dimensions of package quality and security.

### Review Checklist

| Review Item | Review Guideline |
|---|---|
| INFO: required field | Ensure required fields in INFO file exist |
| INFO: deprecated field | Ensure deprecated fields do not exist (from DSM7.0) |
| Lower privilege | Package should run with non-privileged user (from DSM7.0) |
| Package installation | Package should install successfully |
| Package start | Package should start successfully |
| Package stop | Package should stop successfully |
| Package upgrade | Package should upgrade successfully |
| Package uninstall | Package should uninstall successfully |
| Offline installation | Package should support offline installation |
| Network activity during installation | No abnormal connections during installation |
| Security advisor scan | Package should not trigger security advisor issues |
| Antivirus essential scan | Package must pass virus scanning |
| Clean up/file leftover | All package files removed after uninstallation |
| Clean up/process leftover | All package processes stopped after uninstallation |
| Port-config | Service port numbers must be registered |
| Port conflict | Registered ports must not conflict with other services |
| Error log | No error logs left on system |
| Apparmor log | No deny logs from apparmor |
| Coredump file | No coredump files left on system |
| Ad-hoc test | Check for other abnormal behavior |

The guidelines emphasize security, proper cleanup, and system integration compliance for successful package approval.
