# /usr/local linker

## Description

The `/usr/local linker` is a resource worker that manages symbolic links for package executables and libraries. According to the documentation, this worker will "Create symbolic links under _/usr/local/{bin,lib,etc}/_ that points to files in _/var/packages/${package}/target/_" during the `Acquire()` operation when a package starts.

Key behaviors include:
- Files not found in the target directory are ignored
- Existing files in `/usr/local/{bin,lib,etc}/` are unlinked first if conflicts occur
- Any linking failure triggers a rollback of the entire operation
- During `Release()` on package stop, symbolic links are deleted while ignoring missing files and unlink failures

## Provider
DSM

## Timing
`FROM_ENABLE_TO_DISABLE`

## Environment Variables
None

## Updatable Status
No

## Configuration Syntax

```json
"usr-local-linker": {
  "bin": ["<relpath>", ...],
  "lib": ["<relpath>", ...],
  "etc": ["<relpath>", ...]
}
```

## Configuration Members

| Member | Since | Description |
|--------|-------|-------------|
| `bin` | 6.0-5941 | String array listing files to link under `/usr/local/bin/` |
| `lib` | 6.0-5941 | String array listing files to link under `/usr/local/lib/` |
| `etc` | 6.0-5941 | String array listing files to link under `/usr/local/etc/` |
| `relpath` | 6.0-5941 | String representing target file's relative path under `/var/packages/${package}/target/` |

## Example Configuration

```json
"usr-local-linker": {
  "bin": ["usr/bin/a2p", "usr/bin/perl"],
  "lib": ["lib/perl5"]
}
```

## Example Output

```
root@DS $ ls -l /usr/local/{bin,lib,etc}
/usr/local/bin/:
total 0
lrwxrwxrwx 1 root root   30 Aug 13 06:32 a2p -> /var/packages/Perl/target/usr/bin/a2p
lrwxrwxrwx 1 root root   31 Aug 13 06:32 perl -> /var/packages/Perl/target/usr/bin/perl

/usr/local/lib/:
total 0
lrwxrwxrwx 1 root root   28 Aug 13 06:32 perl5 -> /var/packages/Perl/target/lib/perl5

/usr/local/etc/:
total 0
```
