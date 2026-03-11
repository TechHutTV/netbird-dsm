# Scripts

Shell scripts controlling the lifecycle of a package.

## Required Scripts

| Script | Required | Purpose |
|--------|----------|---------|
| preinst | Yes | Validates conditions before installation; non-zero exit aborts |
| postinst | Yes | Prepares environment after installation; non-zero exit corrupts package |
| preuninst | Yes | Checks conditions before uninstallation; non-zero exit aborts |
| postuninst | Yes | Cleans up environment after uninstallation |
| preupgrade | Yes | Validates conditions before upgrade; non-zero exit aborts |
| postupgrade | Yes | Prepares environment after upgrade; non-zero exit corrupts package |
| prereplace | No | Handles data migration for package replacement |
| postreplace | No | Handles data migration for package replacement |
| start-stop-status | Yes | Controls package lifecycle and status detection |

## Minimal Script

```sh
#!/bin/sh
exit 0
```

## start-stop-status Script

```sh
#!/bin/sh
case "$1" in
    start)
        ;;
    stop)
        ;;
    status)
        ;;
esac
exit 0
```

### Status Exit Codes

- 0: package running
- 1: program dead, /var/run pid exists
- 2: program dead, /var/lock lock exists
- 3: package not running
- 4: unknown status
- 150: broken, requires reinstallation

### prestart / prestop

If `precheckstartstop` in INFO is "yes", checks if starting/stopping is permitted.

## Execution Order

### Installation
1. prereplace
2. preinst
3. postinst
4. postreplace
5. start-stop-status prestart (if user selects immediate start)
6. start-stop-status start (if user selects immediate start)

### Upgrade
1. start-stop-status prestop (old, if running)
2. start-stop-status stop (old, if running)
3. preupgrade (new)
4. preuninst (old)
5. postuninst (old)
6. prereplace (new)
7. preinst (new)
8. postinst (new)
9. postreplace (new)
10. postupgrade (new)
11. start-stop-status prestart (new, if previously started)
12. start-stop-status start (new, if previously started)

### Uninstallation
1. start-stop-status prestop (if running)
2. start-stop-status stop (if running)
3. preuninst
4. postuninst

### Start
1. start-stop-status prestart
2. start-stop-status start

### Stop
1. start-stop-status prestop
2. start-stop-status stop
