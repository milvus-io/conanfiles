# Conanfiles Repository

Milvus custom Conan recipes, built and published to JFrog Artifactory via GitHub Actions.

## Repository Structure

```
<package-name>/
  config.yml          # version -> folder mapping
  all/                # recipe folder (default)
    conanfile.py
    conandata.yml
    patches/
    test_package/
  <version>/          # version-specific folder (when recipe differs significantly)
    conanfile.py
    conandata.yml
    ...
```

## How to Publish a Package

### 1. Create/modify the recipe

- Add or update files under `<package-name>/<folder>/`
- Update `config.yml` to register the version
- Test locally: `conan export <path>/conanfile.py <package>/<version>@`

### 2. Push to GitHub and create a PR

```bash
git checkout -b <branch-name>
git add <files>
git commit -m "description"
git push -u origin <branch-name>
gh pr create --title "..." --body "..."
```

### 3. Trigger the `build-and-push` workflow

Go to **Actions > build and push > Run workflow**, or use CLI:

```bash
gh workflow run build-and-push.yml \
  -f package=<package-name> \
  -f version=<version> \
  -f conanfile_path=<folder>/conanfile.py \
  -f repository=testing
```

Parameters:
- **package**: e.g. `google-cloud-cpp`
- **version**: e.g. `2.28.0`
- **conanfile_path**: relative path inside the package dir, default `all/conanfile.py`. Use `2.28.0/conanfile.py` for version-specific folders.
- **repository**: `testing` (default) or `production`
- **user_channel**: optional, e.g. `milvus/dev` (leave empty for no channel)
- **extra_options**: extra conan options, e.g. `-o google-cloud-cpp:components=storage`

### 4. Promote to production

After verifying in testing, re-run the workflow with `repository=production`.

### Sync from Conan Center

To mirror an unmodified CCI package to Artifactory:

```bash
gh workflow run sync-to-artifactory.yml \
  -f package=<package-name> \
  -f version=<version> \
  -f repository=testing
```

## Artifactory Remotes

- **production**: `https://milvus01.jfrog.io/artifactory/api/conan/default-conan-local`
- **testing**: `https://milvus01.jfrog.io/artifactory/api/conan/testing`
