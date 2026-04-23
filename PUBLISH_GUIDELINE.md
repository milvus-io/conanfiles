# Publishing a Recipe to Milvus Conan 2.x Artifactory

This guide walks you through preparing and publishing a Conan 2.x recipe to Milvus's private Artifactory.

## Overview

The [milvus-io/conanfiles](https://github.com/milvus-io/conanfiles) repo holds custom Conan 2.x recipes for the third-party libraries that Milvus depends on. Recipes are published to two repositories:

- **Production:** `https://milvus01.jfrog.io/artifactory/api/conan/default-conan-local2`
- **Testing:** `https://milvus01.jfrog.io/artifactory/api/conan/testing2` (for validating new recipes before they go to production)

## The Publish Workflow

The recommended end-to-end flow for adding a new recipe (or a new version of an existing recipe):

| Step | Action |
|---|---|
| 1 | Branch off `master` with a `conan2-add-*` branch name, add/update the recipe(s) in Conan 2.x format |
| 2 | Push the branch to the conanfiles repo |
| 3 | Trigger the `build-and-push` GitHub Actions workflow from the branch, targeting the **testing** repository |
| 4 | Verify the testing upload succeeded, then open a PR and merge the branch into `master` |
| 5 | Trigger the `build-and-push` workflow from `master`, targeting the **production** repository |
| 6 | Delete the temporary branch |

**Why this flow:**
- Testing validates the recipe works on a clean CI runner before it hits production.
- Production uploads only happen from `master`, keeping it as the single source of truth.
- The recipe revision hash is identical between testing and production (same files), so consumers can pin the same revision either way.

> **Production branch restriction:** The publish script enforces that only `master` and release branches matching `3.x` (e.g. `3.0`, `3.1`, `3.2`) can publish to **production**. Any other branch must use **testing**. This prevents accidental production uploads from feature branches.

> **Important:** If the new recipe A depends on another new recipe B with `@milvus/dev` (e.g. `folly/2026.04.20.00@milvus/dev` depending on `fast_float/8.0.0@milvus/dev`), you must publish **B first, then A** — as two separate workflow triggers in each of steps 3 and 5. The graph-based upload handles transitive **ConanCenter** deps automatically, but local `@milvus/dev` recipes need to be published explicitly in dependency order so Conan can resolve them during the next build.

## Prerequisites

- Python 3.8 or later
- Conan 2.25.1
- **Write** access (or higher) to the conanfiles repo (required to trigger workflows)

```bash
pip install --user conan==2.25.1 pyyaml
conan profile detect
```

## Step 1: Prepare the Recipe

On a new branch off `master`:

```bash
git checkout master
git pull
git checkout -b conan2-add-<package>-<version>
```

Each recipe lives under `recipes/<package>/` in the conanfiles repo:

```
recipes/<package>/
├── config.yml                # maps versions to recipe folders
└── all/                      # or version-specific folder (e.g. v2024/, 3.x.x/)
    ├── conanfile.py          # Conan 2.x recipe
    ├── conandata.yml         # source URLs and sha256 hashes
    └── test_package/         # small test consumer
        ├── conanfile.py
        ├── CMakeLists.txt
        └── test_package.cpp
```

### config.yml

Maps each version to its folder:

```yaml
versions:
  "1.2.3":
    folder: all
  "1.2.4":
    folder: all
```

### conandata.yml

Provides source download URLs per version:

```yaml
sources:
  "1.2.3":
    url: "https://github.com/example/example/archive/refs/tags/v1.2.3.tar.gz"
    sha256: "<sha256 of the tarball>"
```

To get the sha256:

```bash
curl -sL "<tarball_url>" | sha256sum
```

### conanfile.py

Must use the Conan 2.x API:

```python
from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import get
from conan.tools.build import check_min_cppstd


class MyLibConan(ConanFile):
    name = "mylib"
    license = "Apache-2.0"
    url = "https://github.com/example/example"
    description = "Example library"

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def validate(self):
        check_min_cppstd(self, 14)

    def requirements(self):
        self.requires("zlib/1.3.1")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["mylib"]
```

**Do not use Conan 1.x patterns:**

- ❌ `from conans import ConanFile`
- ❌ `def imports(self): ...`
- ❌ `self.info.options.xxx` outside `package_id()`

## Step 2: Push the Branch

Verify the recipe builds locally (optional but strongly recommended):

```bash
export CMAKE_POLICY_VERSION_MINIMUM=3.5    # only needed for CMake 4.x
./scripts/build-and-push.sh <package> <version> --no-upload
```

> **Note:** `CMAKE_POLICY_VERSION_MINIMUM=3.5` is only required for **CMake 4.x**, which removed compatibility with `cmake_minimum_required(VERSION < 3.5)`. Skip it if you're using CMake 3.x.

Then push:

```bash
git add recipes/<package>
git commit -m "Add <package>/<version>"
git push -u origin conan2-add-<package>-<version>
```

## Step 3: Publish to Testing

Open the conanfiles Actions page: https://github.com/milvus-io/conanfiles/actions

1. Select the **build and push** workflow → **Run workflow**
2. **Use workflow from:** select your branch (`conan2-add-<package>-<version>`)
3. Fill in the inputs:
   - `package` — e.g. `mylib`
   - `version` — e.g. `1.2.3`
   - `conanfile_path` — default `all/conanfile.py`
   - `repository` — **`testing`**
   - `user_channel` — e.g. `milvus/dev` if the recipe is Milvus-customized
   - `extra_options` — e.g. `-o mylib:shared=True`
4. Click **Run workflow**

**If your recipe depends on another new `@milvus/dev` recipe** (e.g. folly v2026 needs fast_float), trigger the workflow for the dependency first, then for the main recipe. Both go to `testing`:

```
1st trigger:  package=fast_float         version=8.0.0            user_channel=milvus/dev  repository=testing
2nd trigger:  package=folly              version=2026.04.20.00    user_channel=milvus/dev  repository=testing  conanfile_path=v2026/conanfile.py
```

Wait for each job to succeed before triggering the next.

## Step 4: Verify and Merge

Check the uploaded recipes on the JFrog web UI:

https://milvus01.jfrog.io/ui/repos/tree/Properties/testing2

Navigate to the recipe's `conanfile.py` and verify the **Properties** tab shows the expected `build.commit`, `build.branch`, etc.

Once the recipe works in testing, open a PR to merge the branch into `master`. Get it reviewed and merged.

## Step 5: Publish to Production

After the merge, trigger the workflow again — this time from `master`, targeting production:

1. Go to https://github.com/milvus-io/conanfiles/actions
2. Select **build and push** → **Run workflow**
3. **Use workflow from:** `master`
4. Same inputs as Step 3, but change `repository` to **`production`**
5. Click **Run workflow**

Same rule for dependencies: if A depends on a new `@milvus/dev` recipe B, publish B first, then A.

## Step 6: Clean Up

Delete the temporary branch:

```bash
git push origin --delete conan2-add-<package>-<version>
# or on GitHub: Branches page → trash icon
```

Locally:

```bash
git checkout master
git pull
git branch -d conan2-add-<package>-<version>
```

## Verifying the Upload

### Via the JFrog Web UI

- Production: https://milvus01.jfrog.io/ui/repos/tree/Properties/default-conan-local2
- Testing: https://milvus01.jfrog.io/ui/repos/tree/Properties/testing2

Navigate to `<user>/<name>/<version>/<channel>/<revision>/export/conanfile.py` and open the **Properties** tab. You should see build metadata:

- `build.branch` — git branch the upload came from
- `build.commit` — commit SHA
- `build.datetime` — upload timestamp
- `build.author` — git author of the latest commit

URL path pattern:

```
# With user/channel (e.g. @milvus/dev)
/<user>/<name>/<version>/<channel>/<revision>/export/conanfile.py

# Without user/channel
/_/<name>/<version>/_/<revision>/export/conanfile.py
```

### Via Conan CLI

```bash
conan remote add default-conan-local2 https://milvus01.jfrog.io/artifactory/api/conan/default-conan-local2
conan list 'mylib/*#*' -r default-conan-local2
```

## Special Cases

### Non-standard folder layouts

If multiple versions need different recipe files, use version-specific folders:

```
recipes/folly/
├── config.yml
├── all/              # older versions
│   └── conanfile.py
└── v2024/            # 2024.x versions with different logic
    └── conanfile.py
```

Then pass `--conanfile v2024/conanfile.py` to `build-and-push.sh` (or set the `conanfile_path` input in the workflow).

### Using unreleased commits

GitHub auto-generates tarballs for every commit, tag, and branch — not just releases:

```
https://github.com/{owner}/{repo}/archive/{commit_sha}.tar.gz
https://github.com/{owner}/{repo}/archive/refs/tags/{tag}.tar.gz
https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.tar.gz
```

You can pin any commit as the source of a special version in `conandata.yml`:

```yaml
sources:
  "1.2.3-a1b2c3d":
    url: "https://github.com/example/example/archive/a1b2c3d4e5f6....tar.gz"
    sha256: "<sha256>"
```

The version string is arbitrary — Conan treats it as an opaque identifier. Common conventions:

- `<base_version>-<short_sha>` — e.g. `2.6.2-a1b2c3d`
- `<base_version>.<date>` — e.g. `2.6.2.20260420`
- `<next_version>-dev` — e.g. `2.6.3-dev`

### Using a user/channel

Recipes that differ from upstream (custom patches, pinned deps) should use `@milvus/dev`:

```bash
# via workflow input
user_channel: milvus/dev

# or via local script
./scripts/build-and-push.sh mylib 1.2.3 --user-channel milvus/dev
```

This produces `mylib/1.2.3@milvus/dev`, distinguishing it from any upstream `mylib/1.2.3` on ConanCenter.

### Publishing via local scripts (instead of the workflow)

If you have Artifactory credentials and a working build environment, you can skip the GitHub Actions workflow and publish directly:

```bash
export JFROG_USERNAME2=<your_username>
export JFROG_PASSWORD2=<your_password>
export CMAKE_POLICY_VERSION_MINIMUM=3.5    # only needed for CMake 4.x

./scripts/build-and-push.sh mylib 1.2.3 --user-channel milvus/dev --repository testing
./scripts/build-and-push.sh mylib 1.2.3 --user-channel milvus/dev --repository production
```

The script uploads recipe-only (no pre-built binaries). Consumers build from source with their own profile.

## Troubleshooting

**Build fails with `absl::string_view` not found:**
C++ standard mismatch. The dependencies were resolved with a different `compiler.cppstd`. Add `-s compiler.cppstd=14` (or match the target) via `extra_options` / `--extra-options`.

**Build fails with `target "fmt::fmt" not found`:**
`fmt` was resolved as header-only (default). Folly and similar libraries need the full library target. Add `-o fmt/*:header_only=False` via `extra_options`, or set it in the recipe's `default_options`.

**CI fails with `'exports_sources' but sources not found`:**
Stale Conan cache on the CI agent. Add `conan remove <pkg>/<ver> -c || true` to the CI setup script before building.

**Pre-built binary not found, builds from source:**
Expected for recipe-only uploads. Consumers always build from source using their own profile.

**Permission denied when triggering workflow:**
You need **write** access to the conanfiles repo. Ask a maintainer.

**Recipe depends on an `@milvus/dev` package that isn't published yet:**
Publish the dependency first (to testing or production respectively), then the main recipe. The workflow needs each `@milvus/dev` recipe to already exist on the target remote so the next build can resolve it.

**Script errors out with "production uploads are only allowed from 'master' or release branches (3.x)":**
You're trying to publish to production from a feature branch. Either (a) use `--repository testing` / `repository: testing` instead, or (b) merge your branch into `master` first and then publish from `master`.
