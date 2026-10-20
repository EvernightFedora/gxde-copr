import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sources = load("sources", "scripts/dtk5-sources.py")
split = load("split", "packages/gxde-dtk5/split-files.py")


class Tags(unittest.TestCase):
    def test_numeric_order_and_prereleases(self):
        refs = "a refs/tags/6.9.0\nb refs/tags/v6.10.0\nc refs/tags/7.0.0-rc1"
        self.assertEqual(sources.latest_tag(refs), ("v6.10.0", "b"))

    def test_annotated_tag_uses_commit(self):
        self.assertEqual(sources.latest_tag("a refs/tags/6.7.43\nb refs/tags/6.7.43^{}"), ("6.7.43", "b"))

    def test_gxde_suffix(self):
        self.assertGreater(sources.tag_key("5.6.34gxde2"), sources.tag_key("5.6.34gxde1"))
        self.assertGreater(sources.tag_key("5.6.34gxde1"), sources.tag_key("5.6.34"))

    def test_hyphenated_gxde_release(self):
        refs = "a refs/tags/6.7.43\nb refs/tags/6.7.44-gxde1\nc refs/tags/6.7.44-gxde1^{}\nd refs/tags/6.7.45-rc1"
        self.assertEqual(sources.latest_tag(refs), ("6.7.44-gxde1", "c"))
        self.assertGreater(sources.tag_key("6.7.44-gxde10"), sources.tag_key("6.7.44-gxde2"))

    def test_numeric_release_suffix(self):
        refs = "a refs/tags/0.0.5\nb refs/tags/0.0.6-1\nc refs/tags/0.0.6-10\nd refs/tags/0.0.7-rc1"
        self.assertEqual(sources.latest_tag(refs), ("0.0.6-10", "c"))
        self.assertEqual(sources.rpm_version("0.0.6-1"), "0.0.6.1")

    def test_rpm_version_has_no_hyphen(self):
        self.assertEqual(sources.rpm_version("v6.7.44-gxde1"), "6.7.44.gxde1")
        self.assertEqual(sources.rpm_version("6.7.43"), "6.7.43")

    def test_no_silent_head_fallback(self):
        with self.assertRaises(ValueError):
            sources.latest_tag("a refs/tags/nightly")

    def test_moved_tag_rejected(self):
        old = {"components": {"dtk5common": {"tag": "6.7.43", "commit": "old"}}}
        with patch.object(sources.subprocess, "check_output", return_value="new refs/tags/6.7.43"):
            with self.assertRaisesRegex(ValueError, "moved"):
                sources.resolve(old, Path("unused"))

    def test_rollback_rejected(self):
        old = {"components": {"dtk5common": {"tag": "6.7.43", "commit": "old"}}}
        with patch.object(sources.subprocess, "check_output", return_value="new refs/tags/5.6.0"):
            with self.assertRaisesRegex(ValueError, "rollback"):
                sources.resolve(old, Path("unused"))

    def test_non_core_update_increments_release(self):
        components = {name: {"tag": "6.7.43", "commit": "a", "url": f"https://codeload.github.com/GXDE-OS/{name}/tar.gz/a", "sha256": "digest"} for name in sources.MODULES}
        old = {"version": "6.7.43", "release": 3, "components": components}
        refs = ["b refs/tags/6.7.44"] + ["a refs/tags/6.7.43"] * 6
        with patch.object(sources.subprocess, "check_output", side_effect=refs), patch.object(sources, "download", return_value="digest"):
            self.assertEqual(sources.resolve(old, Path("unused"))["release"], 4)

    def test_unchanged_release_is_stable(self):
        old = json.loads((sources.PACKAGE / "upstream-lock.json").read_text())
        refs = [f'{old["components"][name]["commit"]} refs/tags/{old["components"][name]["tag"]}' for name in sources.MODULES]
        digests = [old["components"][name]["sha256"] for name in sources.MODULES]
        with patch.object(sources.subprocess, "check_output", side_effect=refs), patch.object(sources, "download", side_effect=digests):
            self.assertEqual(sources.resolve(old, Path("unused")), old)


class Checksums(unittest.TestCase):
    def test_checksum_mismatch_does_not_replace_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            origin = Path(tmp) / "origin"
            origin.write_bytes(b"bad data")
            target = Path(tmp) / "archive.tar.gz"
            target.write_bytes(b"original")
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                sources.download(origin.as_uri(), target, "0" * 64)
            self.assertEqual(target.read_bytes(), b"original")
            self.assertFalse(target.with_suffix(".gz.part").exists())

    def test_verified_cache_needs_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "archive.tar.gz"
            target.write_bytes(b"cached")
            checksum = hashlib.sha256(b"cached").hexdigest()
            with patch.object(sources.urllib.request, "urlopen", side_effect=AssertionError("network used")):
                self.assertEqual(sources.download("unused", target, checksum), checksum)


class Packages(unittest.TestCase):
    def test_widget_devel_is_separate_from_runtime(self):
        for path in ("/usr/include/dtk5/DWidget/DApplication", "/usr/lib64/libdtkwidget.so",
                     "/usr/lib64/cmake/DtkWidget/DtkWidgetConfig.cmake"):
            self.assertEqual(split.category(path, "/usr/lib64", "/usr/lib64/qt5"), "widget-devel")
        self.assertEqual(split.category("/usr/lib64/libdtkwidget.so.5", "/usr/lib64", "/usr/lib64/qt5"), "runtime")

    def test_plugins_are_runtime_not_devel(self):
        self.assertEqual(split.category("/usr/lib64/qt5/plugins/platforms/libdxcb.so", "/usr/lib64", "/usr/lib64/qt5"), "runtime")
        self.assertEqual(split.category("/usr/lib64/libdtkcore.so", "/usr/lib64", "/usr/lib64/qt5"), "devel")


if __name__ == "__main__":
    unittest.main()
