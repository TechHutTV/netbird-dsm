# Resource

## Overview

Packages can obtain system resources even in lower privilege identity if they apply this mechanism.

## Steps to Setup Resource Config

1. Find out the resources you want from Resource List
2. Check if the corresponding Timing of selected resource is satisfied
3. Create a file at `conf/resource` with preferred configuration

## Example Configuration

```json
{
    "data-share": {
        "shares": [
            {
                "name": "MyShareFolderName",
                "permission": {
                    "ro": ["MyUserName"]
                }
            }
        ]
    }
}
```

The instance handling the resource request is called a `worker`.

## Related Documentation

- Resource List (available workers)
- Resource Timing
- Resource Update
- Resource Monitoring
