# References

## PkgCreate.py Command Option List

| Option Name | Option Purpose |
|---|---|
| (default) | Run build stage only (link and compile source code). Same as -U option. |
| -p | Specify the platform for packing your project |
| -x | Build dependent project level using `SynoBuildConf/build` (e.g., -x0, -x1) |
| -c | Run both build stage and pack stage (link, compile, pack, sign) |
| -U | Run build stage only (link and compile source code) |
| -l | Run build stage only, but will only link your source code |
| -L | Run build stage only, but will compile your source code only |
| -I | Run pack stage only, which will pack and sign your spk |
| --no-sign | Tells PkgCreate.py not to sign your spk file |
| -z | Run all platforms concurrently |
| -J | Compile your project with -J make command options |
| -S | Disable silent make |

## Build and Pack Stage Options Matrix

| Stage | Action | default | -l | -L | -U | -I --no-sign | -I | -c |
|---|---|---|---|---|---|---|---|---|
| Build Stage | Link Source code | Yes | Yes | No | Yes | No | No | Yes |
| Build Stage | Compile Source code | Yes | No | Yes | Yes | No | No | Yes |
| Pack Stage | Pack Package | No | No | No | No | Yes | Yes | Yes |
| Pack Stage | Sign Package | No | No | No | No | No | Yes | Yes |

## Platform-Specific Dependency

Append `:${platform}` to `BuildDependent` and `ReferenceOnly` sections:

```ini
[BuildDependent]
libfoo-1.0

[BuildDependent:816x,armada370]
libfoo-1.0
libbar-1.0

[default]
all="7.0"
```

## Collect SPK Files with Custom Hook

By default, PkgCreate.py moves SPK files to `/toolkit/result_spk`. Add a custom hook via `SynoBuildConf/collect`.

Environment variables available:
- **SPK_SRC_DIR**: Source folder of target SPK file
- **SPK_DST_DIR**: Default destination folder for SPK file
- **SPK_VERSION**: Version of package from INFO file

Working directory: `/source/${project}` (under chroot environment)
