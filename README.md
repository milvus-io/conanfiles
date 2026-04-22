# Conanfiles

## Summary

Custom Conan 2.x recipes for Milvus C++ dependencies. This repo holds conanfile.py recipes, patches, and configurations for third-party libraries that Milvus's C++ core depends on.

All recipes are organized under the `recipes/` directory, with each subdirectory representing a single package (e.g. `recipes/zlib/`, `recipes/arrow/`).

Recipes can be built and uploaded to Milvus's private Conan Artifactory either by triggering the GitHub Actions workflows, or by running the local scripts directly (requires Artifactory credentials).

## Prepare

**Requirements:**

- Python 3.8 or later
- Conan 2.25.1

**Install Conan:**

```bash
pip install --user conan==2.25.1 pyyaml
```

**Initialize Conan:**

```bash
conan profile detect
```

This detects your default build profile (compiler, arch, OS). The profile is stored at `~/.conan2/profiles/default`.

## Submit Your Recipe

For a step-by-step walkthrough — including recipe structure, verification, and publishing — see [PUBLISH_GUIDELINE.md](PUBLISH_GUIDELINE.md).

To add a new recipe (or a new version of an existing recipe), submit a pull request to the `master` branch:

1. Create a new folder under `recipes/<package>/` with this layout:
   ```
   recipes/<package>/
   ├── config.yml                # maps versions to recipe folders
   └── all/                      # (or version-specific folder, e.g. v2024/, 3.x.x/)
       ├── conanfile.py          # Conan 2.x recipe (required_conan_version = ">=2.0")
       ├── conandata.yml         # source URLs and sha256 hashes
       └── test_package/         # small test consumer
           ├── conanfile.py
           └── CMakeLists.txt
   ```

2. The recipe must follow the Conan 2.x API (`from conan import ConanFile`, `CMakeToolchain`, `CMakeDeps`, etc.). Conan 1.x recipes (`from conans import ConanFile`) are not accepted.

3. Verify the recipe builds locally before submitting:
   ```bash
   ./scripts/build-and-push.sh <package> <version> --no-upload
   ```

4. Open a PR against `master`. Once merged, maintainers can trigger the `build-and-push.yml` workflow to publish it to Artifactory.

## Publish Workflows (GitHub Actions)

Triggering these workflows requires **write** access (or higher) to the conanfiles repo. All the workflows authenticate to Artifactory using the `JFROG_USERNAME2` and `JFROG_PASSWORD2` GitHub repository secrets (configured in **Settings → Secrets and variables → Actions**).

### sync-to-artifactory.yml

Downloads a package from ConanCenter (upstream) and re-uploads it (with all transitive deps) to JFrog Artifactory. Used when you want a vanilla upstream package mirrored into your private registry.

**Inputs:**

| Input | Required | Description |
|---|---|---|
| `package` | Yes | Package name (e.g. `zlib`) |
| `version` | Yes | Package version (e.g. `1.3.1`) |
| `repository` | No | Target Artifactory repository: `production` or `testing` (default: `production`) |

**Job: `sync-conan-package`**

| Step | Command | Description |
|---|---|---|
| Install Conan | `pip install --user conan==2.25.1` | Install Conan 2.25.1 and detect default profile |
| Sync to Artifactory | `./scripts/sync-to-artifactory.sh` | Delegates to `scripts/sync-to-artifactory.sh` with workflow inputs passed as arguments (see [scripts/sync-to-artifactory.sh](#scriptssync-to-artifactorysh) for details) |

---

### build-and-push.yml

Builds a package from a local recipe in this repo (custom/patched), then uploads it to Artifactory. Used for Milvus-specific recipes that differ from upstream.

When triggering the workflow from the GitHub Actions page (**Run workflow** button), you can configure the following:

- **Use workflow from** (branch/tag) — the built-in GitHub Actions selector for which branch or tag's workflow and recipes to use
- The input fields listed below

**Inputs:**

| Input | Required | Description |
|---|---|---|
| `package` | Yes | Package name (e.g. `folly`) |
| `version` | Yes | Package version (e.g. `2024.08.12.00`) |
| `conanfile_path` | Yes | Relative path to conanfile.py within the package dir (default: `all/conanfile.py`) |
| `repository` | No | Target Artifactory repository: `production` or `testing` (default: `production`) |
| `user_channel` | No | User/channel for the package (e.g. `milvus/dev`) |
| `extra_options` | No | Extra conan options (e.g. `-o pkg:opt=val -c conf=val`) |

**Job: `build-and-push`**

| Step | Command | Description |
|---|---|---|
| Install Conan and dependencies | `pip install --user conan==2.25.1 pyyaml` | Install Conan 2.25.1, pyyaml, and detect default profile |
| Build and push | `./scripts/build-and-push.sh` | Delegates to `scripts/build-and-push.sh` with workflow inputs passed as arguments (see [scripts/build-and-push.sh](#scriptsbuild-and-pushsh) for details) |

## Scripts for Manual Publish

### scripts/build-milvus-deps.sh

Builds all 56 Milvus C++ dependencies from this repo's recipes in the correct dependency order, using `conan create` with Milvus-specific settings and options. Packages are built in 8 phases, from foundational libraries (zlib, lz4) up to complex ones (arrow, folly). This was run once during the initial population of the `default-conan-local2` Artifactory.

See [MILVUS_DEPENS.md](MILVUS_DEPENS.md) for the full Milvus dependency graph (resolved from `milvus/internal/core/conanfile.py`), including version pins, custom `@milvus/dev` channel packages, and build order.

**Usage:**

```bash
./scripts/build-milvus-deps.sh                # build only
./scripts/build-milvus-deps.sh --upload       # build and upload recipes to Artifactory
```

**Build settings:**

- Compiler: gcc 11, libstdc++11, C++17, Release
- Parallel jobs: 6
- CMake compatibility: `CMAKE_POLICY_VERSION_MINIMUM=3.5` (for CMake 4.x)

**Upload:** When `--upload` is specified, built recipes are uploaded to the `default-conan-local2` Artifactory remote. Requires `JFROG_USERNAME2` and `JFROG_PASSWORD2` environment variables (or prompts interactively).

### scripts/build-and-push.sh

Builds a single Conan package from this repo's recipes and uploads the recipe and its dependencies (recipe-only) to JFrog Artifactory. Uses the `conan create --format=json` build graph to determine exactly which packages to upload, so it is safe to run locally without uploading unrelated packages from the cache. Supports both production and testing remotes. This script is also used by the `build-and-push.yml` GitHub Actions workflow.

**Usage:**

```bash
./scripts/build-and-push.sh <package> <version> [options]
```

**Options:**

| Option | Description |
|---|---|
| `--conanfile <path>` | Relative path to conanfile.py within the package dir (default: `all/conanfile.py`) |
| `--user-channel <u/c>` | User/channel for the package (e.g. `milvus/dev`) |
| `--extra-options <opts>` | Extra conan options (e.g. `-o pkg:opt=val`) |
| `--repository <repo>` | Target Artifactory repository: `production` or `testing` (default: `production`) |
| `--no-upload` | Build only, skip uploading to Artifactory |

**Examples:**

```bash
./scripts/build-and-push.sh zlib 1.3.1
./scripts/build-and-push.sh protobuf 5.27.0 --user-channel milvus/dev
./scripts/build-and-push.sh protobuf 5.27.0 --user-channel milvus/dev --repository testing
./scripts/build-and-push.sh folly 2024.08.12.00 --conanfile v2024/conanfile.py --user-channel milvus/dev --extra-options "-o folly/*:shared=True"
./scripts/build-and-push.sh zlib 1.3.1 --no-upload    # build only
```

**Authentication:** Uploading to Artifactory requires `JFROG_USERNAME2` and `JFROG_PASSWORD2` environment variables (or prompts interactively).

**Build metadata:** After a successful upload, the script automatically sets the following properties on the uploaded recipe in JFrog Artifactory:

| Property | Description |
|---|---|
| `build.branch` | Current git branch name |
| `build.commit` | HEAD commit SHA of this repo |
| `build.datetime` | UTC timestamp of the build |
| `build.author` | Git author of the latest commit |

### scripts/sync-to-artifactory.sh

Downloads a package from ConanCenter (upstream) and uploads it along with all transitive dependencies (recipes and binaries) to JFrog Artifactory. Uses the `conan install --format=json` install graph to determine exactly which packages to upload, so it is safe to run locally without uploading unrelated packages from the cache. Supports both production and testing remotes. This script is also used by the `sync-to-artifactory.yml` GitHub Actions workflow.

**Usage:**

```bash
./scripts/sync-to-artifactory.sh <package> <version> [options]
```

**Options:**

| Option | Description |
|---|---|
| `--repository <repo>` | Target Artifactory repository: `production` or `testing` (default: `production`) |
| `--no-upload` | Download only, skip uploading to Artifactory |

**Examples:**

```bash
./scripts/sync-to-artifactory.sh openssl 3.3.2
./scripts/sync-to-artifactory.sh libcurl 8.10.1 --repository testing
./scripts/sync-to-artifactory.sh prometheus-cpp 1.2.4 --no-upload    # download only
```

**Authentication:** Uploading to Artifactory requires `JFROG_USERNAME2` and `JFROG_PASSWORD2` environment variables (or prompts interactively).

## Browsing Uploaded Recipes

After a recipe is uploaded, you can browse it via the JFrog web UI:

- Production: https://milvus01.jfrog.io/ui/repos/tree/Properties/default-conan-local2
- Testing: https://milvus01.jfrog.io/ui/repos/tree/Properties/testing2

Navigate to a recipe's `conanfile.py` and open the **Properties** tab to see the build metadata (`build.author`, `build.branch`, `build.commit`, `build.datetime`).

**Example:** `folly/2024.08.12.00@milvus/dev` properties:

https://milvus01.jfrog.io/ui/repos/tree/Properties/default-conan-local2/milvus/folly/2024.08.12.00/dev/f9b2bdf162c0ec47cb4e5404097b340d/export/conanfile.py

