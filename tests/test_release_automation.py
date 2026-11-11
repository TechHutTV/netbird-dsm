"""Check release ordering, upstream pin verification, and catalog/SPK agreement."""

from contextlib import redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import version


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalog = load_script("build-catalog")
updater = load_script("update-netbird")


class ReleaseVersionTests(unittest.TestCase):
    def test_revisions_increase_across_releases_and_upstream_updates(self):
        tags = ["v0.70.5-4", "v0.80.0", "v0.80.0-3", "v0.80.0--2", "v0.80.0-fix-1"]
        self.assertEqual(version.next_version("0.80.0", tags), "0.80.0-5")
        tags.append("v0.80.0-5")
        self.assertEqual(version.next_version("0.80.0", tags), "0.80.0-6")
        self.assertEqual(version.next_version("0.81.0", tags), "0.81.0-6")
        self.assertEqual(version.next_version("0.80.0", []), "0.80.0-1")

    def test_upstream_rollback_and_revision_overflow_fail(self):
        for tags in (["v0.81.0"], ["v0.81.0-fix-1"], ["v0.80.0-2147483647"]):
            with self.subTest(tags=tags), self.assertRaises(ValueError):
                version.next_version("0.80.0", tags)

    def test_invalid_versions_are_rejected(self):
        for value in ("v0.80.0", "0.80.0-1", "0.80", "00.80.0", "0.80.0\nother=1", "2147483648.0.0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                version.upstream_version(value)
        for value in ("0.80.0", "0.80.0--1", "0.80.0-fix-1", "0.80.0-01", "0.80.0-2147483648"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                version.package_version(value)

    def test_tag_must_match_the_pinned_binary_and_use_release_revision(self):
        for tag in ("v0.81.0-1", "v0.80.0-0", "v0.80.0--1"):
            result = subprocess.run([sys.executable, "-B", "scripts/version.py", "release", "--upstream", "0.80.0", "--tag", tag],
                                    cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
        result = subprocess.run([sys.executable, "-B", "scripts/version.py", "release", "--upstream", "0.80.0", "--tag", "v0.80.0-5"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pkg=0.80.0-5\n", result.stdout)

    def test_make_rejects_empty_versions_mismatched_upstream_and_architecture(self):
        commands = [
            ["make", "check-package-version", "PACKAGE_VERSION="],
            ["make", "check-package-version", "VERSION=0.80.0", "PACKAGE_VERSION=0.81.0-5"],
            ["make", "check-version", "SYNOLOGY_ARCH=aarch64", "NETBIRD_ARCH=amd64"],
        ]
        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)

    def test_old_retries_and_prereleases_cannot_replace_catalog(self):
        releases = [
            {"tag_name": "v0.80.0-5", "draft": False, "prerelease": False},
            {"tag_name": "v0.80.0-6", "draft": False, "prerelease": False},
            {"tag_name": "v0.80.0-7", "draft": True, "prerelease": False},
            {"tag_name": "v0.81.0-8", "draft": False, "prerelease": True},
            {"tag_name": "v0.80.0--2", "draft": False, "prerelease": False},
        ]
        self.assertTrue(version.catalog_eligible("v0.80.0-6", releases))
        for tag in ("v0.80.0-5", "v0.80.0-7", "v0.81.0-8"):
            self.assertFalse(version.catalog_eligible(tag, releases))

    def test_changelog_baseline_uses_package_order_instead_of_semver(self):
        releases = [
            {"tag_name": "v0.80.0", "draft": False, "prerelease": False},
            {"tag_name": "v0.80.0--1", "draft": False, "prerelease": False, "published_at": "2026-10-25"},
            {"tag_name": "v0.80.0-5", "draft": False, "prerelease": False},
            {"tag_name": "v0.80.0-6", "draft": True, "prerelease": False},
            {"tag_name": "v0.81.0-7", "draft": False, "prerelease": True},
        ]
        self.assertEqual(version.previous_release_tag(releases), "v0.80.0-5")
        self.assertEqual(version.previous_release_tag(releases[:2]), "v0.80.0--1")
        self.assertEqual(version.previous_release_tag([]), "")


class UpstreamPinTests(unittest.TestCase):
    def release(self):
        return {"tag_name": "v0.81.0", "draft": False, "prerelease": False, "assets": [
            {"name": f"netbird_0.81.0_linux_{arch}.tar.gz", "digest": "sha256:" + "a" * 64}
            for arch in ("amd64", "arm64")
        ]}

    def test_both_architectures_need_valid_digests_and_stable_release(self):
        release = self.release()
        pinned, checksums = updater.release_checksums(release)
        self.assertEqual(pinned, "0.81.0")
        self.assertEqual(len(checksums), 2)
        release["assets"].pop()
        with self.assertRaisesRegex(ValueError, "arm64"):
            updater.release_checksums(release)
        for field in ("draft", "prerelease"):
            release = self.release()
            release[field] = True
            with self.assertRaises(ValueError):
                updater.release_checksums(release)
        release = self.release()
        release["assets"][1]["digest"] = "sha256:bad"
        with self.assertRaises(ValueError):
            updater.release_checksums(release)

    def test_bad_download_preserves_both_existing_pins(self):
        release = self.release()
        # amd64 succeeds, then arm64 fails. Even the version file must stay untouched.
        release["assets"][0]["digest"] = "sha256:" + hashlib.sha256(b"fixture").hexdigest()
        def download(command, **kwargs):
            Path(command[-1]).write_bytes(b"fixture")
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            self.addCleanup(os.chdir, previous)
            os.chdir(directory)
            Path("VERSION").write_text("0.80.0\n")
            Path("SHA256SUMS").write_text("existing checksums\n")
            with patch.object(sys, "argv", ["update-netbird.py"]), \
                 patch.object(updater.subprocess, "check_output", return_value=json.dumps(release)), \
                 patch.object(updater.subprocess, "run", side_effect=download), \
                 redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                updater.main()
            self.assertEqual(Path("VERSION").read_text(), "0.80.0\n")
            self.assertEqual(Path("SHA256SUMS").read_text(), "existing checksums\n")

    def test_repository_manifest_matches_the_pinned_upstream(self):
        upstream = (ROOT / "VERSION").read_text().strip()
        expected = {f"netbird_{upstream}_linux_{arch}.tar.gz" for arch in ("amd64", "arm64")}
        entries = [line.split() for line in (ROOT / "SHA256SUMS").read_text().splitlines()]
        self.assertEqual({name for digest, name in entries}, expected)
        for digest, name in entries:
            self.assertRegex(digest, r"^[0-9a-f]{64}$")


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="netbird-release-")
        self.addCleanup(self.tmp.cleanup)
        self.artifacts = Path(self.tmp.name)
        self.output = self.artifacts / "site"
        for arch, (family, _) in catalog.ARCHES.items():
            self.write_spk(arch, family)

    def write_spk(self, arch, family, package="0.80.0-5"):
        info = subprocess.check_output(["sh", str(ROOT / "spk/INFO.sh"), package, "0", family])
        path = self.artifacts / f"netbird_0.80.0-5_synology_{arch}.spk"
        with tarfile.open(path, "w") as archive:
            member = tarfile.TarInfo("INFO")
            member.size = len(info)
            archive.addfile(member, io.BytesIO(info))

    def build(self):
        catalog.build_catalog("0.80.0-5", "TechHutTV/netbird-dsm", "https://example.com/dsm/",
                              self.artifacts, self.output)

    def test_catalog_versions_links_sizes_and_hashes_match_actual_spks(self):
        self.build()
        for arch, (family, _) in catalog.ARCHES.items():
            entry = json.loads((self.output / family / "index.json").read_text())["packages"][0]
            artifact = self.artifacts / f"netbird_0.80.0-5_synology_{arch}.spk"
            data = artifact.read_bytes()
            self.assertEqual(entry["version"], "0.80.0-5")
            self.assertEqual(entry["size"], len(data))
            self.assertEqual(entry["md5"], hashlib.md5(data).hexdigest())
            self.assertEqual(entry["sha256"], hashlib.sha256(data).hexdigest())
            self.assertTrue(entry["link"].endswith(f"/v0.80.0-5/{artifact.name}"))
            self.assertEqual(entry["thumbnail"], ["https://example.com/dsm/icon-256.png"])
        html = (self.output / "index.html").read_text()
        self.assertIn("https://example.com/dsm/aarch64/index.json", html)
        self.assertIn("v0.80.0-5", html)
        self.assertNotIn("$PKG_VERSION", html)

    def test_mismatched_info_and_missing_arch_fail_before_writing_catalogs(self):
        for family, package in (("aarch64", "0.80.0-4"), ("x86_64", "0.80.0-5")):
            self.write_spk("arm64", family, package)
            with self.assertRaises(ValueError):
                self.build()
            self.assertFalse(self.output.exists())
        (self.artifacts / "netbird_0.80.0-5_synology_arm64.spk").unlink()
        with self.assertRaises(FileNotFoundError):
            self.build()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
