#!/usr/bin/env python3
import os
import re
import subprocess
from pathlib import Path

import yaml

BASE_SHA = os.environ.get("BASE_SHA")
PR_NUMBER = os.environ.get("PR_NUMBER")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
GH_TOKEN = os.environ.get("GH_TOKEN")
TARGETS_FILE = Path(os.environ["TARGETS_FILE"])
HEAD_REF = "HEAD"

if not BASE_SHA and not PR_NUMBER:
    raise SystemExit("Either BASE_SHA or PR_NUMBER must be provided")

if PR_NUMBER and not GITHUB_REPOSITORY:
    raise SystemExit("GITHUB_REPOSITORY must be provided when PR_NUMBER is set")

if PR_NUMBER and not GH_TOKEN:
    raise SystemExit("GH_TOKEN must be provided when PR_NUMBER is set")

if PR_NUMBER and not BASE_SHA:
    raise SystemExit("BASE_SHA is still required when PR_NUMBER is set so old file contents can be compared")

if PR_NUMBER and not re.fullmatch(r"[0-9]+", PR_NUMBER):
    raise SystemExit(f"Invalid PR_NUMBER: {PR_NUMBER!r}")

if GITHUB_REPOSITORY and not re.fullmatch(r"[^/]+/[^/]+", GITHUB_REPOSITORY):
    raise SystemExit(f"Invalid GITHUB_REPOSITORY: {GITHUB_REPOSITORY!r}")


def git_stdout(args):
    return subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        capture_output=True,
    ).stdout


def git_lines(args):
    return git_stdout(args).splitlines()


def github_pr_files():
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{GITHUB_REPOSITORY}/pulls/{PR_NUMBER}/files",
            "--paginate",
            "--jq",
            ".[] | select(.status != \"removed\") | .filename",
        ],
        check=True,
        text=True,
        capture_output=True,
        env={**os.environ, "GH_TOKEN": GH_TOKEN},
    )
    return [line for line in result.stdout.splitlines() if line]


CHANGED_FILES = github_pr_files() if PR_NUMBER else None


def changed_files_matching(prefix):
    if CHANGED_FILES is None:
        return None
    return [path for path in CHANGED_FILES if path.startswith(prefix)]


def changed_config_files():
    if CHANGED_FILES is None:
        return None
    return [
        path for path in CHANGED_FILES
        if path.startswith("recipes/") and path.endswith("/config.yml")
    ]


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


def maybe_load_yaml_at_head(path):
    if CHANGED_FILES is None:
        return load_yaml(path)
    return load_yaml_at(HEAD_REF, path)


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


def pr_number_reason(path):
    if PR_NUMBER:
        return f"changed in PR #{PR_NUMBER}: {path}"
    return f"changed {path}"


def get_changed_configs():
    configs = changed_config_files()
    if configs is not None:
        return configs
    return git_lines(["diff", "--diff-filter=ACMR", "--name-only", BASE_SHA, HEAD_REF, "--", "recipes/*/config.yml"])


def get_changed_recipe_files():
    files = changed_files_matching("recipes/")
    if files is not None:
        return files
    return git_lines(["diff", "--diff-filter=ACMR", "--name-only", BASE_SHA, HEAD_REF, "--", "recipes"])


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
    new = maybe_load_yaml_at_head(path)
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

        if path.name == "config.yml":
            continue

        if path.name == "conandata.yml":
            for version in sorted(changed_conandata_versions(changed_path), key=version_sort_key):
                if version in versions_for(package):
                    add_target(package, version, pr_number_reason(changed_path))
            continue

        if folder_key not in seen_affected_folders:
            seen_affected_folders.add(folder_key)
            affected_folders.append((package, folder, changed_path))

    for package, folder, changed_path in affected_folders:
        if (package, folder) in covered_folders:
            continue
        version = pick_version_for_folder(package, folder)
        add_target(package, version, pr_number_reason(changed_path))


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
    changed_configs = get_changed_configs()
    changed_recipe_files = get_changed_recipe_files()
    print_source = f"PR #{PR_NUMBER}" if PR_NUMBER else f"git diff {BASE_SHA}..{HEAD_REF}"
    print(f"detection_source: {print_source}")
    print("changed_configs:", changed_configs)
    print("changed_recipe_files:", changed_recipe_files)

    detect_config_changes(changed_configs)
    detect_recipe_file_changes(changed_recipe_files)
    write_outputs()


if __name__ == "__main__":
    main()
