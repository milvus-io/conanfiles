#!/usr/bin/env python3
"""Append compiler versions missing from the Conan 2 settings.yml.

Conan 2.25.1 ships a default settings.yml listing clang versions only up to 22,
which rejects `-s compiler=clang -s compiler.version=23` with an
"Invalid setting" error. This script adds the versions used by the
build-with-toolchain workflow (clang 23) to the active Conan home's
settings.yml so that gcc-16 / clang-23 builds pass settings validation.

Idempotent: versions already present are left untouched, and a settings.yml
that already contains the requested versions is not rewritten.

Usage:
    CONAN_HOME=... ./scripts/extend-conan-settings.py
"""
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is required to run this script")

CONAN_HOME = os.environ.get("CONAN_HOME", os.path.expanduser("~/.conan2"))
SETTINGS_PATH = os.path.join(CONAN_HOME, "settings.yml")

# compiler -> extra version strings to ensure are present
ADDITIONS = {
    "clang": ["23"],
}


def main() -> int:
    if not os.path.isfile(SETTINGS_PATH):
        sys.exit(f"settings.yml not found at {SETTINGS_PATH}")

    with open(SETTINGS_PATH) as f:
        data = yaml.safe_load(f)

    compiler_map = (data.get("compiler") or {})

    changed = False
    for compiler, versions in ADDITIONS.items():
        version_list = (compiler_map.get(compiler) or {}).get("version")
        if not isinstance(version_list, list):
            sys.exit(f"no version list for compiler '{compiler}' in {SETTINGS_PATH}")
        for version in versions:
            if version not in version_list:
                version_list.append(version)
                changed = True

    if changed:
        with open(SETTINGS_PATH, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False)
        print(f"Updated {SETTINGS_PATH}: added {ADDITIONS}")
    else:
        print(f"{SETTINGS_PATH} already contains required versions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
