#!/usr/bin/env python3
"""Verify both upstream archives, then update VERSION and SHA256SUMS together."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from version import upstream_version


def release_checksums(release):
    if release["draft"] or release["prerelease"]:
        raise ValueError("Only stable upstream releases can be pinned")
    tag = release["tag_name"]
    if not tag.startswith("v"):
        raise ValueError("Upstream release tag must start with v")
    version = tag[1:]
    upstream_version(version)
    assets = {asset["name"]: asset for asset in release["assets"]}
    checksums = {}
    for arch in ("amd64", "arm64"):
        name = f"netbird_{version}_linux_{arch}.tar.gz"
        asset = assets.get(name, {})
        digest = asset.get("digest") or ""
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise ValueError(f"Missing asset or SHA256 digest: {name}")
        checksums[name] = digest.removeprefix("sha256:")
    return version, checksums


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="latest")
    parser.add_argument("--output", type=Path, help="GitHub Actions output file")
    args = parser.parse_args()
    try:
        endpoint = "repos/netbirdio/netbird/releases/latest"
        if args.version != "latest":
            requested = args.version.removeprefix("v")
            upstream_version(requested)
            endpoint = f"repos/netbirdio/netbird/releases/tags/v{requested}"
        release = json.loads(subprocess.check_output(["gh", "api", endpoint], text=True))
        version, checksums = release_checksums(release)
        current = Path("VERSION").read_text().strip()
        if upstream_version(version) < upstream_version(current):
            raise ValueError(f"Refusing to downgrade NetBird from {current} to {version}")
        manifest = "".join(f"{digest}  {name}\n" for name, digest in checksums.items())
        changed = version != current or Path("SHA256SUMS").read_text() != manifest
        if changed:
            with tempfile.TemporaryDirectory(prefix="netbird-update-") as directory:
                for name, expected in checksums.items():
                    archive = Path(directory) / name
                    url = f"https://github.com/netbirdio/netbird/releases/download/v{version}/{name}"
                    subprocess.run(["curl", "-fSL", "--retry", "3", url, "-o", str(archive)], check=True)
                    digest = hashlib.sha256()
                    with archive.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(chunk)
                    if digest.hexdigest() != expected:
                        raise ValueError(f"SHA256 mismatch for {name}")
            # Neither pin changes unless both architectures have passed verification.
            Path("VERSION").write_text(version + "\n")
            Path("SHA256SUMS").write_text(manifest)
        output = f"version={version}\nchanged={str(changed).lower()}\n"
        if args.output:
            with args.output.open("a") as stream:
                stream.write(output)
        print(output, end="")
    except (ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
