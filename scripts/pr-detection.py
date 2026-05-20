#!/usr/bin/env python3
import os
import re
import subprocess
from pathlib import Path

import yaml


BASE_SHA = os.environ["BASE_SHA"]
TARGETS_FILE = Path(os.environ["TARGETS_FILE"])


def git_stdout(args):
    return subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        capture_output=True,
    ).stdout


def git_lines(args):
    return git_stdout(args).splitlines()


def load_yaml(path):
    path = Path(path)
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def load_yaml_at(ref, path):
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    return yaml.safe_load(result.stdout) or {}


def version_folder(info):
    return info.get("folder", "all") if isinstance(info, dict) else "all"


def version_sort_key(version):
    normalized = str(version).lower()
    if normalized.startswith("v"):
        normalized = normalized[1:]
    tokens = []
    for token in re.findall(r"\d+|[a-z]+|[^0-9a-z]+", normalized):
        if token.isdigit():
            tokens.append((2, int(token)))
        elif token.isalpha():
            tokens.append((1, token))
        else:
            tokens.append((0, token))
    return tuple(tokens), str(version)


config_cache = {}


def versions_for(package):
    if package not in config_cache:
        config_cache[package] = (load_yaml(Path("recipes", package, "config.yml")).get("versions") or {})
    return config_cache[package]


targets = []
target_keys = set()
covered_folders = set()


def add_target(package, version, reason):
    versions = versions_for(package)
    info = versions.get(version)
    if info is None:
        raise SystemExit(f"recipes/{package}/config.yml: version {version!r} is not present in the final config.yml")

    folder = version_folder(info)
    conanfile = f"{folder}/conanfile.py"
    if not Path("recipes", package, conanfile).is_file():
        raise SystemExit(f"recipes/{package}/{conanfile} does not exist")

    key = (package, version, conanfile)
    if key in target_keys:
        return

    target_keys.add(key)
    covered_folders.add((package, folder))
    targets.append(key)
    print(f"Selected {package}/{version} ({conanfile}): {reason}")


def pick_version_for_folder(package, folder):
    candidates = [
        version
        for version, info in versions_for(package).items()
        if version_folder(info) == folder
    ]
    if candidates:
        return max(candidates, key=version_sort_key)
    raise SystemExit(f"recipes/{package}/{folder} changed, but no version in recipes/{package}/config.yml uses that folder")


def changed_conandata_versions(path):
    old = load_yaml_at(BASE_SHA, path)
    new = load_yaml(path)
    changed = set()
    for section in ("sources", "patches"):
        old_values = old.get(section) or {}
        new_values = new.get(section) or {}
        if not isinstance(old_values, dict) or not isinstance(new_values, dict):
            continue
        for version, value in new_values.items():
            if old_values.get(version) != value:
                changed.add(version)
    return changed


def detect_config_changes(changed_configs):
    for config_path in changed_configs:
        path = Path(config_path)
        parts = path.parts
        if len(parts) != 3 or parts[0] != "recipes" or parts[2] != "config.yml":
            continue

        package = parts[1]
        old_versions = (load_yaml_at(BASE_SHA, config_path).get("versions") or {})
        new_versions = versions_for(package)

        for version in sorted(new_versions.keys() - old_versions.keys(), key=version_sort_key):
            add_target(package, version, "new version in config.yml")

        for version, info in sorted(new_versions.items(), key=lambda item: version_sort_key(item[0])):
            if version in old_versions and old_versions[version] != info:
                add_target(package, version, "changed version mapping in config.yml")


def detect_recipe_file_changes(changed_recipe_files):
    affected_folders = []
    seen_affected_folders = set()

    for changed_path in changed_recipe_files:
        path = Path(changed_path)
        parts = path.parts
        if len(parts) < 4 or parts[0] != "recipes":
            continue

        package = parts[1]
        folder = parts[2]
        folder_key = (package, folder)

        if path.name == "conandata.yml":
            for version in sorted(changed_conandata_versions(changed_path), key=version_sort_key):
                if version in versions_for(package):
                    add_target(package, version, f"changed {changed_path}")

        if folder_key not in seen_affected_folders:
            seen_affected_folders.add(folder_key)
            affected_folders.append((package, folder, changed_path))

    for package, folder, changed_path in affected_folders:
        if (package, folder) in covered_folders:
            continue
        version = pick_version_for_folder(package, folder)
        add_target(package, version, f"changed {changed_path}")


def write_outputs():
    with TARGETS_FILE.open("w") as out:
        for target in targets:
            out.write("\t".join(target) + "\n")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as out:
            print(f"count={len(targets)}", file=out)

    if targets:
        print("Detected recipe versions to build:")
        for package, version, conanfile in targets:
            print(f"  - {package}/{version} ({conanfile})")
    else:
        print("No recipe versions were selected for this PR.")


def main():
    changed_configs = git_lines(["diff", "--diff-filter=ACMR", "--name-only", BASE_SHA, "HEAD", "--", "recipes/*/config.yml"])
    changed_recipe_files = git_lines(["diff", "--diff-filter=ACMR", "--name-only", BASE_SHA, "HEAD", "--", "recipes"])
    print("changed_configs:", changed_configs)
    print("changed_recipe_files:", changed_recipe_files)

    detect_config_changes(changed_configs)
    detect_recipe_file_changes(changed_recipe_files)
    write_outputs()


if __name__ == "__main__":
    main()
