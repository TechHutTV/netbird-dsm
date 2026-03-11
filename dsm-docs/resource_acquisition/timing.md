# Resource Timing

Every worker acquires resources at certain timings and holds it during an interval.

## Timing Definitions

| Timing | Description | On Failure |
|--------|-------------|-----------|
| WHEN_PREINST | Before preinst script | Abort installation, rollback, show alert |
| WHEN_POSTINST | Before postinst script | Finish installation, show alert |
| WHEN_ENABLE | Before WHEN_STARTUP; skip during bootup | Abort startup, rollback, show alert |
| WHEN_STARTUP | Before start script | Abort startup, rollback, show alert |
| WHEN_PREUNINST | After preuninst script | Finish uninstallation, show alert |
| WHEN_POSTUNINST | Before postuninst script | Finish uninstallation, show alert |
| WHEN_DISABLE | After WHEN_HALT; skip during shutdown | Ignore |
| WHEN_HALT | After stop script | Ignore |

> To let the package itself decide whether uninstallation should continue, `WHEN_PREUNINST` is processed after the `preuninst` script.
