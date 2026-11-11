#!/usr/bin/env python3
"""Build the DSM catalogs from the exact SPKs uploaded to a release."""

import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import re
import shutil
from string import Template
import tarfile

from version import package_version


ARCHES = {"amd64": ("x86_64", "apollolake"), "arm64": ("aarch64", "armada37xx")}


def package_info(path, version, arch):
    with tarfile.open(path) as archive:
        with archive.extractfile("INFO") as stream:
            info = dict(re.findall(r'^([a-z_]+)="([^"\n]*)"$', stream.read().decode(), re.M))
    if info.get("package") != "netbird" or info.get("version") != version:
        raise ValueError(f"{path.name}: INFO does not match the release version")
    if ARCHES[arch][1] not in info.get("arch", "").split():
        raise ValueError(f"{path.name}: INFO does not match the expected architecture")
    for key in ("description", "maintainer", "maintainer_url"):
        if not info.get(key):
            raise ValueError(f"{path.name}: missing INFO field {key}")
    return info


def build_catalog(version, repo, base_url, artifacts, output):
    package_version(version)
    tag = f"v{version}"
    base_url = base_url.rstrip("/")
    packages = {}
    for arch, (family, _) in ARCHES.items():
        path = artifacts / f"netbird_{version}_synology_{arch}.spk"
        info = package_info(path, version, arch)
        data = path.read_bytes()
        packages[family] = {"packages": [{
            "package": "netbird", "version": info["version"], "dname": "NetBird",
            "desc": info["description"], "maintainer": info["maintainer"],
            "maintainer_url": info["maintainer_url"], "distributor": info["maintainer"],
            "distributor_url": info["maintainer_url"],
            "thumbnail": [f"{base_url}/icon-256.png"],
            "link": f"https://github.com/{repo}/releases/download/{tag}/{path.name}",
            "md5": hashlib.md5(data).hexdigest(), "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data), "qinst": True, "qstart": True, "qupgrade": True,
            "start": True, "thirdparty": True, "beta": False,
        }]}
    # Validate both SPKs before writing any catalog.
    for family, catalog in packages.items():
        directory = output / family
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.json").write_text(json.dumps(catalog, indent=2) + "\n")
    root = Path(__file__).resolve().parents[1]
    shutil.copyfile(root / "spk/PACKAGE_ICON_256.PNG", output / "icon-256.png")
    template = Template((root / "scripts/catalog-index.html").read_text())
    html = template.substitute({key: escape(value, quote=True) for key, value in {
        "REPO": repo, "PKG_VERSION": version, "UPSTREAM_VERSION": version.rsplit("-", 1)[0],
        "x86_url": f"{base_url}/x86_64/index.json", "arm_url": f"{base_url}/aarch64/index.json",
    }.items()})
    (output / "index.html").write_text(html)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--artifacts", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("_site"))
    args = parser.parse_args()
    try:
        build_catalog(args.version, args.repo, args.base_url, args.artifacts, args.output)
    except (ValueError, OSError, KeyError, tarfile.TarError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
