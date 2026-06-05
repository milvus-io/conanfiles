#!/usr/bin/env python3
import hashlib
import os
import re
import sys
import urllib.request
from pathlib import Path

import yaml


RECIPE_SOURCES = {
    "zilliztech/milvus-common": {
        "package": "milvus-common",
        "folder": "all",
        "url": "https://github.com/{source_repo}/archive/refs/tags/{tag}.tar.gz",
        "cppstd": "20",
    },
    "milvus-io/milvus-sdk-cpp": {
        "package": "milvus-sdk-cpp",
        "folder": "all",
        "url": "https://github.com/{source_repo}/archive/refs/tags/{tag}.tar.gz",
        "cppstd": "14",
    },
    "zilliztech/knowhere": {
        "package": "knowhere",
        "folder": "all",
        "url": "https://github.com/{source_repo}/archive/refs/tags/{tag}.tar.gz",
        "cppstd": "20",
    },
    "zilliztech/cardinal": {
        "package": "cardinal",
        "folder": "all",
        "url": "https://github.com/{source_repo}/archive/refs/tags/{tag}.tar.gz",
        "cppstd": "20",
    },
    "milvus-io/milvus-storage": {
        "package": "milvus-storage",
        "folder": "all",
        "url": "https://github.com/{source_repo}/archive/refs/tags/{tag}.tar.gz",
        "cppstd": "20",
    },
}


TAG = os.environ["TAG"]
COMMIT = os.environ["COMMIT"]
SOURCE_REPO = os.environ["SOURCE_REPO"]


if SOURCE_REPO not in RECIPE_SOURCES:
    supported = ", ".join(sorted(RECIPE_SOURCES))
    raise SystemExit(f"unsupported source_repo {SOURCE_REPO!r}; supported: {supported}")

if not re.fullmatch(r"[0-9a-f]{40}", COMMIT):
    raise SystemExit(f"invalid commit sha: {COMMIT!r}")

if not re.fullmatch(r"v?[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z]+)?", TAG):
    raise SystemExit(f"unsupported tag format: {TAG!r}; expected vX.Y.Z, X.Y.Z, vX.Y.Z-suffix, or X.Y.Z-suffix")

recipe_version = TAG[1:] if TAG.startswith("v") and len(TAG) > 1 and TAG[1].isdigit() else TAG
recipe = RECIPE_SOURCES[SOURCE_REPO]
package = recipe["package"]
folder = recipe["folder"]
cppstd = recipe.get("cppstd", "20")
url = recipe["url"].format(source_repo=SOURCE_REPO, tag=TAG, commit=COMMIT)
config_path = Path("recipes", package, "config.yml")
conandata_path = Path("recipes", package, folder, "conandata.yml")
conanfile_path = Path("recipes", package, folder, "conanfile.py")


for path in (config_path, conandata_path, conanfile_path):
    if not path.is_file():
        raise SystemExit(f"required recipe file does not exist: {path}")


def download_sha256(source_url):
    request = urllib.request.Request(source_url, headers={"User-Agent": "conanfiles-recipe-updater"})
    sha256 = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=120) as response:
        while chunk := response.read(1024 * 1024):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_yaml(path):
    return yaml.safe_load(path.read_text()) or {}


def write_output(**values):
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a") as output:
        for key, value in values.items():
            print(f"{key}={value}", file=output)


def insert_version_block(path, section, version, lines):
    text = path.read_text()
    marker = f"{section}:\n"
    if marker not in text:
        raise SystemExit(f"{path} does not contain {marker.strip()!r}")
    block = "".join(lines)
    path.write_text(text.replace(marker, marker + block, 1))


sha256 = download_sha256(url)
config = load_yaml(config_path)
conandata = load_yaml(conandata_path)
versions = config.get("versions") or {}
sources = conandata.get("sources") or {}
changed = True

existing_version = versions.get(recipe_version)
existing_source = sources.get(recipe_version)
if existing_version is not None or existing_source is not None:
    expected_version = {"folder": folder}
    expected_source = {"url": url, "sha256": sha256}
    if existing_version == expected_version and existing_source == expected_source:
        changed = False
        print(f"{package}/{recipe_version} already exists with matching metadata")
    else:
        raise SystemExit(f"{package}/{recipe_version} already exists with different metadata")

if changed:
    insert_version_block(
        config_path,
        "versions",
        recipe_version,
        [
            f'  "{recipe_version}":\n',
            f"    folder: {folder}\n",
        ],
    )
    insert_version_block(
        conandata_path,
        "sources",
        recipe_version,
        [
            f'  "{recipe_version}":\n',
            f'    url: "{url}"\n',
            f'    sha256: "{sha256}"\n',
        ],
    )
    print(f"Added {package}/{recipe_version}")
    print(f"  source repo: {SOURCE_REPO}")
    print(f"  tag: {TAG}")
    print(f"  commit: {COMMIT}")
    print(f"  url: {url}")
    print(f"  sha256: {sha256}")
    print(f"  cppstd: {cppstd}")

write_output(
    package=package,
    recipe_version=recipe_version,
    recipe_config_path=str(config_path),
    conanfile_path=f"{folder}/conanfile.py",
    conandata_path=str(conandata_path),
    url=url,
    sha256=sha256,
    cppstd=cppstd,
    changed=str(changed).lower(),
)
