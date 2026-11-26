import hashlib
import io
import os
import runpy
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import sdk_grpc_zstd

COMMIT = "a" * 40
VERSION = "0.0.0-test"
REFERENCE = "grpc/1.65.0@milvus/zstd#" + "b" * 32


def sdk_archive(marker=None, commit=COMMIT):
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode="w:gz", pax_headers={"comment": commit}) as tar:
        root = tarfile.TarInfo("sdk-test")
        root.type = tarfile.DIRTYPE
        tar.addfile(root)
        if marker is not None:
            files = {sdk_grpc_zstd.MARKER: marker.encode()}
            for name in sdk_grpc_zstd.ASSETS:
                files[name] = b"raise AssertionError('dispatch must not execute tagged code')\n"
            for name, data in files.items():
                item = tarfile.TarInfo("sdk-test/" + name)
                item.size = len(data)
                tar.addfile(item, io.BytesIO(data))
    return result.getvalue()


class DispatchTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(tmp.name)
        self.root = Path("recipes/milvus-sdk-cpp")
        shutil.copytree(SCRIPTS.parent / self.root, self.root)

    def dispatch(self, data, repo="milvus-io/milvus-sdk-cpp"):
        env = {"SOURCE_REPO": repo, "TAG": "v" + VERSION, "COMMIT": COMMIT,
               "GITHUB_OUTPUT": "output"}
        Path("output").write_text("")
        with patch.dict(os.environ, env), patch("urllib.request.urlopen", return_value=io.BytesIO(data)):
            runpy.run_path(str(SCRIPTS / "update-recipe-from-dispatch.py"))
        return dict(line.split("=", 1) for line in Path("output").read_text().splitlines())

    def test_marked_release_is_scoped_and_repeatable(self):
        archive = sdk_archive(REFERENCE)
        old = {p: p.read_bytes() for p in (self.root / "all").rglob("*") if p.is_file()}
        result = self.dispatch(archive)
        directory = self.root / f"grpc-zstd-{VERSION}"
        self.assertEqual(result["conanfile_path"], f"{directory.name}/conanfile.py")
        data = yaml.safe_load((directory / "conandata.yml").read_text())
        self.assertEqual(data["grpc_zstd"][VERSION], REFERENCE)
        self.assertEqual(data["sources"][VERSION]["sha256"], hashlib.sha256(archive).hexdigest())
        self.assertTrue((directory / "bootstrap/scripts/export_grpc_zstd.py").is_file())
        self.assertEqual(self.dispatch(archive)["changed"], "false")
        self.assertEqual(old, {p: p.read_bytes() for p in old})

    def test_bootstrap_uses_public_fallback_and_verifies_exported_revision(self):
        self.dispatch(sdk_archive(REFERENCE))
        directory = self.root / f"grpc-zstd-{VERSION}"
        results = [subprocess.CompletedProcess([], code) for code in (1, 1, 0, 0)]
        with patch("subprocess.run", side_effect=results) as run, \
             patch("subprocess.check_output", side_effect=["/cache/export", "/cache/export"]):
            sdk_grpc_zstd.bootstrap(directory, VERSION, "mirror")
        self.assertEqual([c.args[0][-1] for c in run.call_args_list[1:3]], ["mirror", "conancenter"])
        with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)), \
             patch("subprocess.check_output", side_effect=["/cache/other", "/cache/pinned"]):
            with self.assertRaisesRegex(ValueError, "did not reproduce"):
                sdk_grpc_zstd.bootstrap(directory, VERSION, "mirror")

    def test_old_tag_keeps_ordinary_recipe(self):
        result = self.dispatch(sdk_archive())
        self.assertEqual(result["conanfile_path"], "all/conanfile.py")
        self.assertFalse((self.root / f"grpc-zstd-{VERSION}").exists())

    def test_different_commit_and_unpinned_recipe_are_rejected(self):
        for archive in [sdk_archive(REFERENCE, commit="c" * 40), sdk_archive("grpc/1.65.0@milvus/zstd")]:
            with self.assertRaises(ValueError):
                self.dispatch(archive)
        self.assertFalse((self.root / f"grpc-zstd-{VERSION}").exists())

    def test_unrelated_dispatch_only_hashes(self):
        shutil.copytree(SCRIPTS.parent / "recipes/milvus-common", "recipes/milvus-common")
        with patch("tempfile.TemporaryFile", side_effect=AssertionError("unexpected archive spool")):
            result = self.dispatch(b"unparsed upstream bytes", repo="zilliztech/milvus-common")
        self.assertEqual(result["sha256"], hashlib.sha256(b"unparsed upstream bytes").hexdigest())
        self.assertEqual(result["conanfile_path"], "all/conanfile.py")


if __name__ == "__main__":
    unittest.main()
