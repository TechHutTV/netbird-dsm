#!/usr/bin/env python3
"""Resolve upstream and DSM package versions for local builds and Actions."""

import argparse
import json
from pathlib import Path
import re
import subprocess


MAX_NUMBER = 2**31 - 1  # Synology INFO version component limit.
UPSTREAM = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def upstream_version(value):
    match = re.fullmatch(UPSTREAM, value)
    if not match or any(int(n) > MAX_NUMBER for n in match.groups()):
        raise ValueError("NetBird version must be numeric X.Y.Z without a leading v")
    return tuple(map(int, match.groups()))


def package_version(value):
    match = re.fullmatch(rf"({UPSTREAM})-(0|[1-9][0-9]*)", value)
    if not match:
        raise ValueError("DSM package version must be X.Y.Z-REVISION")
    upstream, revision = value.rsplit("-", 1)
    feature = upstream_version(upstream)
    if int(revision) > MAX_NUMBER:
        raise ValueError("DSM revision exceeds 2^31-1")
    return (*feature, int(revision))


def tagged_version(tag):
    if not tag.startswith("v"):
        raise ValueError("Release tags must start with v")
    return package_version(tag[1:])


def next_version(upstream, tags):
    feature = upstream_version(upstream)
    versions = []
    for tag in tags:
        try:
            versions.append(tagged_version(tag))
        except ValueError:
            # Legacy releases include bare upstream versions and malformed suffixes.
            # They cannot reserve a numeric revision, but still guard against rollback.
            try:
                versions.append((*upstream_version(tag.removeprefix("v").split("-", 1)[0]), 0))
            except ValueError:
                continue
    if versions and feature < max(v[:3] for v in versions):
        raise ValueError("Pinned upstream version is older than an existing release tag")
    # Keep revisions increasing across upstream updates too, as Synology recommends.
    revision = max((v[3] for v in versions), default=0) + 1
    result = f"{upstream}-{revision}"
    package_version(result)
    return result


def catalog_eligible(tag, releases):
    version = tagged_version(tag)
    stable = []
    for release in releases:
        if release["draft"] or release["prerelease"]:
            continue
        try:
            stable.append(tagged_version(release["tag_name"]))
        except ValueError:
            continue
    return bool(stable) and version == max(stable)


def previous_release_tag(releases):
    stable = []
    for release in releases:
        if release["draft"] or release["prerelease"]:
            continue
        tag = release["tag_name"]
        try:
            value = tagged_version(tag)
        except ValueError:
            try:
                value = (*upstream_version(tag.removeprefix("v").split("-", 1)[0]), 0)
            except ValueError:
                continue
        stable.append((value, release.get("published_at") or "", tag))
    return max(stable)[2] if stable else ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "next", "release", "pr", "catalog"))
    parser.add_argument("--upstream", default=Path("VERSION").read_text().strip())
    parser.add_argument("--package")
    parser.add_argument("--tag")
    parser.add_argument("--releases-file", type=Path)
    args = parser.parse_args()
    try:
        upstream_version(args.upstream)
        if args.command == "check":
            if args.package is not None:
                package_version(args.package)
                if args.package.rsplit("-", 1)[0] != args.upstream:
                    raise ValueError("Package version must use the selected NetBird version")
            return
        if args.command == "catalog":
            if not args.tag or not args.releases_file:
                raise ValueError("--tag and --releases-file are required")
            eligible = catalog_eligible(args.tag, json.loads(args.releases_file.read_text()))
            print(f"deploy_catalog={str(eligible).lower()}")
            return
        if args.command == "next":
            tags = subprocess.check_output(["git", "tag", "--list"], text=True).splitlines()
            package = next_version(args.upstream, tags)
            if args.releases_file:
                previous = previous_release_tag(json.loads(args.releases_file.read_text()))
                print(f"previous_tag={previous}")
        elif args.command == "release":
            if not args.tag:
                raise ValueError("--tag is required")
            version = tagged_version(args.tag)
            if version[3] == 0:
                raise ValueError("Revision 0 is reserved for local and PR builds")
            package = args.tag[1:]
            if package.rsplit("-", 1)[0] != args.upstream:
                raise ValueError("Release tag does not match VERSION at the tagged commit")
        else:
            package = f"{args.upstream}-0"
        print(f"upstream={args.upstream}")
        print(f"pkg={package}")
        print(f"tag=v{package}")
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
