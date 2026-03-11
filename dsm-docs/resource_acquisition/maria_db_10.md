# Maria DB 10 Resource Documentation

## Overview

"This worker register on the following timings: PREINST/PREUNINST and POSTINST/POSTUNINST" to manage database operations during package lifecycle events.

## Operational Stages

### Installation & Upgrade (POSTINST)
- **migrate-db**: transitions databases from MariaDB 5 to MariaDB 10
- **create-db**: establishes new database
- **grant-user**: creates user accounts
- **drop-db-inst**: removes legacy databases during migration

### Uninstallation (POSTUNINST)
- **drop-db-uninst**: removes database
- **drop-user-uninst**: deletes user (use cautiously with shared users)

## Provider & Timing

**Provider**: MariaDB10 package
**Timing**: `FROM_PREINST_TO_PREUNINST` and `FROM_POSTINST_TO_POSTUNINST`

## Configuration Syntax

```json
"mariadb10-db": {
    "admin-account-m10": "<db account>",
    "admin-pw-m10": "<db password>",
    "admin-account-m5": "<m5 db account>",
    "admin-pw-m5": "<m5 db password>",
    "migrate-db": {
        "flag": true | false,
        "m5-db-name": "<db name>",
        "m10-db-name": "<db name>",
        "db-collision": "replace" | "error"
    },
    "create-db": {
        "flag": true | false,
        "db-name": "<db name>",
        "db-collision": "replace" | "skip" | "error"
    },
    "grant-user": {
        "flag": true | false,
        "db-name": "<db name>",
        "user-name": "<db username>",
        "host": "<db host>",
        "user-pw": "<db password>"
    },
    "drop-db-inst": {
        "flag": true | false,
        "ver": "m5" | "m10",
        "db-name": "<db name>"
    },
    "drop-db-uninst": true | false,
    "drop-user-uninst": true | false
}
```

## Configuration Parameters

| Parameter | Subfield | Version | Description |
|-----------|----------|---------|-------------|
| admin-account-m10 | - | 10.0.30-0005 | Root-level MariaDB10 account |
| admin-pw-m10 | - | 10.0.30-0005 | Root-level MariaDB10 password |
| admin-account-m5 | - | 10.0.30-0005 | Root-level MariaDB account |
| admin-pw-m5 | - | 10.0.30-0005 | Root-level MariaDB password |
| migrate-db | flag | 10.0.30-0005 | Enable migration stage |
| migrate-db | m5-db-name | 10.0.30-0005 | Source database name |
| migrate-db | m10-db-name | 10.0.30-0005 | Destination database name |
| migrate-db | db-collision | 10.0.30-0005 | Conflict resolution strategy |
| create-db | flag | 10.0.30-0005 | Enable creation stage |
| create-db | db-name | 10.0.30-0005 | Database name to create |
| create-db | db-collision | 10.0.30-0005 | Collision handling strategy |
| grant-user | flag | 10.0.30-0005 | Enable user grant stage |
| grant-user | db-name | 10.0.30-0005 | Target database |
| grant-user | user-name | 10.0.30-0005 | Username to create |
| grant-user | host | 10.0.30-0005 | User host (default: localhost) |
| grant-user | user-pw | 10.0.30-0005 | User password |
| drop-db-inst | flag | 10.0.30-0005 | Enable drop stage |
| drop-db-inst | ver | 10.0.30-0005 | Target version (m5/m10) |
| drop-db-inst | db-name | 10.0.30-0005 | Database to drop |
| drop-db-uninst | - | 10.0.30-0005 | Drop on uninstall |
| drop-user-uninst | - | 10.0.30-0005 | Drop user on uninstall |

## DB Collision Strategies

- **replace**: Removes existing database and substitutes with new version
- **error**: Reports error without action, potentially causing installation failure
- **skip**: Continues execution without modifications (unavailable for migration)

## Practical Example

```json
"mariadb10-db": {
    "admin-account-m10": "root",
    "admin-pw-m10": "password!@#123432",
    "admin-account-m5": "",
    "admin-pw-m5": "",
    "migrate-db": {
        "flag": false,
        "m5-db-name": "",
        "m10-db-name": "",
        "db-collision": ""
    },
    "create-db": {
        "flag": true,
        "db-name": "myservice",
        "db-collision": "error"
    },
    "grant-user": {
        "flag": true,
        "db-name": "myservice",
        "user-name": "myservice_dbuser",
        "host": "localhost",
        "user-pw": "password!@#123432asd123123"
    },
    "drop-db-inst": {
        "flag": false,
        "ver": "",
        "db-name": ""
    },
    "drop-db-uninst": true,
    "drop-user-uninst": false
}
```

## Key Notes

- Worker performs automatic rollback if any stage fails
- Environment Variables: None
- Not updatable during runtime
- Enabling specific stages requires corresponding credential fields
