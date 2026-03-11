# Privilege Config

The `conf/privilege` file is required and controls security behaviors.

## Basic Structure

```json
{
  "defaults": {
    "run-as": "package"
  },
  "username": "myusername",
  "groupname": "mygroupname",
  "tool": [{
    "relpath": "bin/mytool",
    "user": "package",
    "group": "package",
    "permission": "0700"
  }]
}
```

## defaults (required)

| run-as | File Behavior | Script Behavior |
|--------|---------------|-----------------|
| `package` | `chown -hR "${package}:${package}"` | Set resuid as [username] |
| `root` | `chown -hR "root:root"` | Set resuid as root |

## username / groupname (optional)

Custom user/group name. Default: package name. (Since 6.0-5940)

## ctrl-script (optional)

Controls identity for running scripts:

```json
"ctrl-script": [{
  "action": "start",
  "run-as": "package"
}]
```

Actions: `preinst`, `postinst`, `preuninst`, `postuninst`, `preupgrade`, `postupgrade`, `start`, `stop`, `status`, `prestart`, `prestop`

## executable (optional)

Identity to chown on installed files:

```json
"executable": [{
  "relpath": "bin/mybin",
  "run-as": "package"
}]
```

## tool (optional)

Identity to chown and chmod installed files:

```json
"tool": [{
  "relpath": "bin/mytool",
  "user": "package",
  "group": "package",
  "permission": "0700"
}]
```

### With capabilities (since 7.0-40656):

```json
"tool": [{
  "relpath": "bin/mytool",
  "user": "package",
  "group": "package",
  "capabilities": "cap_chown,cap_net_raw",
  "permission": "0700"
}]
```

## Package User/Group UI Visibility

- Application privilege permission viewer
- FTP chroot user selector
- File Station (Change owner, Shared Links Manager)
- Control Panel > Shared Folder > Edit > Permission (limited)
- ACL editor (limited)
