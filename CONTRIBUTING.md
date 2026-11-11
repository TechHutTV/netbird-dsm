# Contributing

This repository handles Synology packaging, daemon lifecycle, and the DSM web interface. Report packaging issues here. Changes to the NetBird client itself belong in [netbirdio/netbird](https://github.com/netbirdio/netbird).

## Build requirements

- Python 3, curl, GNU tar, make, and shasum.
- jq 1.5 or newer for the test suite.
- An authenticated GitHub CLI for the upstream update script.
- The Go toolchain required by the selected upstream release's `go.mod` for source builds.

Run the full test suite on Linux; service tests depend on `/proc` and Linux tools. On macOS, install GNU tar and pass `TAR=gtar` when packaging.

## Build a package

```sh
git clone https://github.com/TechHutTV/netbird-dsm.git
cd netbird-dsm

# Intel/AMD
make download package

# ARM64
make download package SYNOLOGY_ARCH=aarch64
```

The build uses the upstream version in [`VERSION`](VERSION) and verifies downloads against [`SHA256SUMS`](SHA256SUMS). Output files are named `netbird_<version>-0_synology_<amd64|arm64>.spk`.

Revision `0` identifies development builds so a published package can upgrade them. To install a development build over a release at the same upstream version, back up enrollment and uninstall the installed package first. Older PR builds with large revisions also need uninstalling before switching to a normal release at that upstream version.

Run `make test` before submitting changes to package scripts or the web interface. PRs affecting the build or package run the tests and build both architectures. Download their SPKs from the workflow's artifacts; they are retained for 14 days.

## Update the upstream client

With an authenticated GitHub CLI, run:

```sh
python3 -B scripts/update-netbird.py --version latest
```

Use a stable version such as `--version 0.82.1` to pin a specific release. The script downloads and verifies both Linux archives before updating `VERSION` and `SHA256SUMS` together. Review both files in the same PR.

For a temporary local override, pass `VERSION=<version>` and `CHECKSUMS_FILE=<matching-checksum-file>` to make. The version must not include a leading `v` or a package revision.

## Build the client from source

From this repository's root:

```sh
git clone https://github.com/netbirdio/netbird.git /path/to/netbird
git -C /path/to/netbird checkout "v$(cat VERSION)"

make build package NETBIRD_SRC=/path/to/netbird
make build package NETBIRD_SRC=/path/to/netbird SYNOLOGY_ARCH=aarch64
```

Use an upstream checkout matching `VERSION`. Packaging checks the recorded binary version and architecture, so rerun `make download` or `make build` when switching either.

### Build variables

| Variable | Default | Purpose |
|---|---|---|
| `VERSION` | Contents of `VERSION` | Upstream client version. |
| `PACKAGE_VERSION` | `<VERSION>-0` | DSM version. Its upstream portion must match `VERSION`. |
| `CHECKSUMS_FILE` | `SHA256SUMS` | Pinned archive checksums. |
| `SYNOLOGY_ARCH` | `x86_64` | Synology architecture family; also accepts `aarch64`. |
| `NETBIRD_ARCH` | Derived from `SYNOLOGY_ARCH` | `amd64` or `arm64`; must match the Synology architecture. |
| `NETBIRD_SRC` | `.` | Upstream checkout for source builds. |
| `TAR` | `tar` | GNU tar executable; use `gtar` on macOS. |

## Release a package

1. Merge reviewed changes into `main`. **Draft release** updates the release draft and groups changes by PR title or label.
2. Review the draft under **Releases**. Keep its generated tag and `main` target, then publish it.
3. **Build SPK Release** tests the tagged code, builds both architectures, attaches the SPKs, and updates the per-architecture GitHub Pages catalogs.

Release titles show the upstream version, such as **NetBird DSM 0.82.1**. Tags, SPKs, and catalogs include a global DSM build revision, such as `v0.82.1-6`. The next revision is one greater than the highest valid numeric revision in existing tags, including older upstream versions. Revision `0` is reserved for development. See [Synology's version requirements](https://help.synology.com/developer-guide/synology_package/INFO_necessary_fields.html).

Use conventional PR titles such as `feat:`, `fix:`, `chore:`, or `docs:` for categorized release notes. Titles without a prefix still appear in the changelog.

**Update NetBird** checks for a newer stable client daily at 07:00 UTC. It verifies both downloads, runs tests, builds both packages, and opens or updates `automation/netbird-bump`. It can also be run manually with `latest` or a stable version. Merging that PR updates the draft; publishing remains a maintainer action.

The workflows use GitHub's built-in `GITHUB_TOKEN`. The updater validates packages before opening its PR; additional PR workflow runs may require [manual approval](https://docs.github.com/en/actions/concepts/security/github_token).

### Retry a failed release

Rerun the failed workflow, or dispatch **Build SPK Release** with the published tag. Existing assets are reused without replacement. Only the newest stable package can update the catalogs, so older retries and prereleases cannot roll back the package source. Tags predating the release automation cannot use this workflow.

### Repository setup

- Set **Settings → Pages → Build and deployment → Source** to **GitHub Actions**. Allow release tags in the `github-pages` environment's deployment policy.
- Enable **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests** so the upstream updater can open PRs. Default token permissions can remain read-only; workflows request their required permissions.
- Run **Draft release** manually to create the initial draft if needed.
