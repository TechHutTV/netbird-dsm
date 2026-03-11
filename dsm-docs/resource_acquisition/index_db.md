# Index DB Documentation

## Overview

The Index DB resource enables packages to manage search indexing for help and application content within DSM.

## Core Functionality

**Two primary operations:**
- `Acquire()`: "Index package help and app content"
- `Release()`: "Un-index package help and app content"

For additional context, the documentation references integration details available in the help documentation section.

## Technical Specifications

| Attribute | Value |
|-----------|-------|
| Provider | DSM |
| Timing | `FROM_ENABLE_TO_DISABLE` |
| Environment Variables | None |
| Updatable | No |

## Configuration Structure

```json
"indexdb": {
    "app-index"  : {
        "conf-relpath": "<conf relpath>",
        "db-relpath": "<app db relpath>"
    },
    "help-index": {
        "conf-relpath": "<conf relpath>",
        "db-relpath": "<help db relpath>"
    }
}
```

## Configuration Parameters

| Member | Version | Description |
|--------|---------|-------------|
| `app-index` | 6.0-5924 | Object containing app index configuration |
| `help-index` | 6.0-5924 | Object containing help index configuration |
| `conf-relpath` | 6.0-5924 | Configuration file's relative path under `/var/packages/${package}/target/` |
| `db-relpath` | 6.0-5924 | Database folder's relative path under `/var/packages/${package}/target/` |

## Practical Example

```json
"indexdb": {
    "app-index"  : {
        "conf-relpath": "app/index.conf",
        "db-relpath": "indexdb/appindexdb"
    },
    "help-index": {
        "conf-relpath": "app/helptoc.conf",
        "db-relpath": "indexdb/helpindexdb"
    }
}
```
