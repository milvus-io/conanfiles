# Publishing a Recipe to Milvus Conan 2.x Artifactory

This guide walks you through preparing and publishing a Conan 2.x recipe to Milvus's private Artifactory (`default-conan-local2`).

## Overview

The [milvus-io/conanfiles](https://github.com/milvus-io/conanfiles) repo holds custom Conan 2.x recipes for the third-party libraries that Milvus depends on. Recipes are published to:

- **Production:** `https://milvus01.jfrog.io/artifactory/api/conan/default-conan-local2`
- **Testing:** `https://milvus01.jfrog.io/artifactory/api/conan/testing2`

There are two ways to publish:

1. **GitHub Actions workflows** (requires write access to the conanfiles repo)
2. **Local scripts** (requires Artifactory credentials and a working build environment)

## Prerequisites

- Python 3.8 or later
- Conan 2.25.1

```bash
pip install --user conan==2.25.1 pyyaml
conan profile detect
```

## Step 1: Prepare the Recipe

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

## Step 2: Verify Locally

Before submitting or publishing, verify the recipe builds:

```bash
export CMAKE_POLICY_VERSION_MINIMUM=3.5    # only needed for CMake 4.x
./scripts/build-and-push.sh <package> <version> --no-upload
```

This runs the full build + test_package without uploading. If it succeeds locally, it will succeed on CI.

> **Note:** `CMAKE_POLICY_VERSION_MINIMUM=3.5` is only required for **CMake 4.x**, which removed compatibility with `cmake_minimum_required(VERSION < 3.5)`. Skip it if you're using CMake 3.x.

## Step 3: Submit a PR

Open a pull request against the `master` branch of the conanfiles repo with the new recipe. Once merged, maintainers can publish it.

## Step 4: Publish

### Option A: GitHub Actions Workflow (recommended)

Open the conanfiles Actions page: https://github.com/milvus-io/conanfiles/actions

1. Select the **build and push** workflow (left sidebar) → **Run workflow**
2. Select the branch (usually `master`)
3. Fill in the inputs:
   - `package` — e.g. `mylib`
   - `version` — e.g. `1.2.3`
   - `conanfile_path` — default `all/conanfile.py`
   - `repository` — `production` or `testing`
   - `user_channel` — e.g. `milvus/dev` for Milvus-customized recipes
   - `extra_options` — e.g. `-o mylib:shared=True`
4. Click **Run workflow**

Triggering workflows requires **write** access (or higher) to the conanfiles repo.

### Option B: Local Script

Requires Artifactory credentials:

```bash
export JFROG_USERNAME2=<your_username>
export JFROG_PASSWORD2=<your_password>
export CMAKE_POLICY_VERSION_MINIMUM=3.5    # only needed for CMake 4.x

./scripts/build-and-push.sh mylib 1.2.3                                    # upload to production
./scripts/build-and-push.sh mylib 1.2.3 --user-channel milvus/dev          # with user/channel
./scripts/build-and-push.sh mylib 1.2.3 --repository testing               # upload to testing
./scripts/build-and-push.sh mylib 1.2.3 --extra-options "-o mylib:shared=True"
```

The script uploads recipe-only (no pre-built binaries). Consumers build from source with their own profile.

## Step 5: Verify the Upload

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
./scripts/build-and-push.sh mylib 1.2.3 --user-channel milvus/dev
```

This produces `mylib/1.2.3@milvus/dev`, distinguishing it from any upstream `mylib/1.2.3` on ConanCenter.

## Troubleshooting

**Build fails with `absl::string_view` not found:**
C++ standard mismatch. The dependencies were resolved with a different `compiler.cppstd`. Add `-s compiler.cppstd=14` (or match the target) via `--extra-options`.

**CI fails with `'exports_sources' but sources not found`:**
Stale Conan cache on the CI agent. Add `conan remove <pkg>/<ver> -c || true` to the CI setup script before building.

**Pre-built binary not found, builds from source:**
Expected for recipe-only uploads. Consumers always build from source using their own profile.

**Permission denied when triggering workflow:**
You need **write** access to the conanfiles repo. Ask a maintainer.
