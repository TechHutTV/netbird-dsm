# Monitor

## Overview

The DSM manages resources through slices or processes and requires information about process ownership. Packages must inform DSM which daemons belong to them.

## Configuration

To enable monitoring, set the `Slice` field in your systemd unit to `[package_name].slice`.

**Example for MyPackage:**

```ini
...
[Service]
Slice=MyPackage.slice
...
```

## Result

When properly configured, your package will appear in the resource monitor interface, as shown in the resource monitor screenshot example.

## Note

"If the field is properly set, you should be able to see your package shown on the resource monitor."
