# Advanced setup

The [standard installation](../README.md#installation) runs NetBird as the package user with local forwarding. Use this guide to migrate an existing installation, enable kernel TUN mode, recover package ownership, or reset enrollment.

## Replacing a manual installation

Stop an existing manual NetBird installation before installing the SPK. The installer checks for another daemon, an active or enabled manual `netbird.service`, and a conflicting `/usr/local/bin/netbird`. Root-owned processes may need an administrator to inspect them.

Use a LAN connection independent of NetBird throughout the migration.

1. **Identify and back up the old installation.** Inspect `ps -ef`, `systemctl status netbird.service`, and `readlink -f /usr/local/bin/netbird`. Save any configuration and enrollment you want to retain from `/etc/netbird` and `/var/lib/netbird` in a protected backup. These files can contain private keys.
2. **Stop the old daemon and disable its startup mechanism.** For a confirmed manual systemd installation, run:

   ```sh
   sudo systemctl disable --now netbird.service
   ```

   Disable any Task Scheduler task or custom startup script for that installation too. If a daemon remains, inspect its command line and `/proc/<PID>/exe` as root, then stop that specific process. An executable can keep running after its file has been deleted.
3. **Remove only confirmed manual program files.** Remove `/usr/local/bin/netbird` if it belongs to the manual installation. Keep it if it points to `/var/packages/netbird/target/bin/netbird`. Remove the confirmed manual `netbird.service` unit from its installed location, then run `sudo systemctl daemon-reload`. Keep the package's separate `pkgctl-netbird.service` unit.
4. **Choose fresh enrollment or migration.** The package initializes its own state. To retain the manual identity, an administrator must explicitly copy the desired default config into the stopped package's `/var/packages/netbird/var/` directory before its first start, with ownership `netbird:netbird` and mode `0600`. Keep an existing package identity unless you intend to replace it. Check that the saved management server is still the intended destination. Additional named profiles need separate migration. Otherwise, enroll the package normally.
5. **Optionally remove old state.** After stopping the old daemon and startup mechanisms, and after backing up or migrating anything needed, these commands discard the manual installation's state:

   ```sh
   sudo rm -rf /etc/netbird /var/lib/netbird
   sudo rm -f /var/run/netbird.sock
   ```

   Keep `/var/packages/netbird` and its resolved data directory. Confirm that the old daemon and any old host interface do not return at startup.

A leftover configuration file, stale socket, disabled service, or `wt0` interface alone does not prove that a daemon is running. The package recognizes its own daemon and CLI link during upgrades.

If package configuration is empty, inaccessible, or missing alongside existing profile data, startup stops to protect the identity. Restore the configuration or repair ownership. Use a [clean reset](#start-fresh-clean-reset) only when you want new enrollment.

## Kernel TUN mode

Use this mode when NAS applications need transparent outbound access to NetBird peers. Starting the service script as root attempts to prepare `/dev/net/tun` and use a host interface. If TUN is unavailable, it falls back to netstack with local forwarding. Check the startup log to confirm the selected mode.

This is an administrator-managed workaround, not a Synology-supported package configuration. Lifecycle operations run outside Package Center, and root starts can leave package state owned by root. Stop the root daemon before upgrades or uninstalling. Follow [Returning to Package Center](#returning-to-package-center) before switching back to normal package management.

1. Stop NetBird in Package Center. Keep it stopped while the scheduled task manages the daemon.
2. Open **Control Panel → Task Scheduler → Create → Triggered Task → User-defined script**.
3. Set the task name to `NetBird (root)`, the user to `root`, the event to **Boot-up**, and enable the task.
4. Under **Task Settings → Run command**, enter:

   ```sh
   /var/packages/netbird/scripts/start-stop-status start
   ```

5. Run the task once, or reboot.
6. Check the startup log for `kernel TUN`, then run `ip addr show wt0` to confirm the host interface has a NetBird IP. Test outbound access from a NAS application, subject to NetBird policies and DSM firewall rules.

`Interface type: Userspace` alone does not identify this mode. The package uses userspace WireGuard even with a real TUN device. Web connection controls require the daemon to run as the package user; use the CLI in root mode.

## Returning to Package Center

Disable or delete the root startup task in **Control Panel → Task Scheduler**. Then run the following over SSH as an administrator. It stops the daemon, checks DSM's package-state path, and restores access for the package user without deleting enrollment.

```sh
sudo sh <<'SH'
set -eu
/bin/sh /var/packages/netbird/scripts/start-stop-status stop

# Resolve DSM's var symlink and verify the destination before changing it.
state_dir=$(readlink -f /var/packages/netbird/var)
volume_number=${state_dir#/volume}
volume_number=${volume_number%%/*}
case "$volume_number" in
    ''|*[!0-9]*) printf 'Unexpected package state path: %s\n' "$state_dir" >&2; exit 1 ;;
esac
if [ "$state_dir" != "/volume${volume_number}/@appdata/netbird" ]; then
    printf 'Unexpected package state path: %s\n' "$state_dir" >&2
    exit 1
fi
test -d "$state_dir"
printf 'Restoring package-user access to %s\n' "$state_dir"
chown -hR netbird:netbird "$state_dir"
find "$state_dir" -type d -exec chmod u+rwx {} +
find "$state_dir" -type f -exec chmod u+rw {} +
SH
```

If stopping fails, the script exits and keeps the daemon's PID tracking. If the state path differs from the expected DSM 7 appdata path, inspect it before adjusting the check. The ownership repair does not follow directory symlinks inside the state directory.

Start NetBird from Package Center, or run:

```sh
sudo /usr/syno/bin/synopkg start netbird
```

If DSM reports error 275 (package locked), let the previous package operation finish before retrying. A restart or clean reset is not a substitute for repairing ownership.

## Start fresh (clean reset)

A reset removes the package's keys, configuration, and profiles. Back up anything you need before continuing, and use a connection independent of NetBird.

```sh
sudo synopkg stop netbird
sudo find /var/packages/netbird/var/ -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
sudo synopkg start netbird
sudo netbird up --setup-key YOUR_SETUP_KEY
```

The trailing slash follows DSM's `var` symlink, and `find` includes hidden state directories. This resets package state only. Manual-install state is handled separately in [Replacing a manual installation](#replacing-a-manual-installation).
