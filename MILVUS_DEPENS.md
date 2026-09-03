# Dependency Tree for Milvus Conan Packages

## Scan Information

- **Scan date:** 2026-09-02
- **Scan method:** Parsed the `conanfile.py` of every Milvus-related C++ project checked out
  under `/home/myh/work/git-go/`, recording `requires` tuples, `requirements()` entries
  (including `force=True`/`override=True` pins), `build_requirements()`, and per-package
  options. Version/recipe revisions (`#<RREV>`) and channels are copied verbatim from the
  conanfiles; transitive resolutions come from the recipes in this repository.
- **Scanned conanfiles (local checkouts):**

  | Project | conanfile path | Git HEAD |
  |---------|----------------|----------|
  | milvus (internal/core) | `milvus/internal/core/conanfile.py` | `531ff43ffb95c8081c24a673f764ee10b0054a5a` |
  | milvus-common | `milvus-common/conanfile.py` | `7d67e14eae701d99227eed582e3af851fa51bee4` |
  | milvus-storage | `milvus-storage/cpp/conanfile.py` | `cb22dfaa01175c429edbd0fb6794251f1a58f400` |
  | knowhere | `knowhere/conanfile.py` | `2868882b02fd31fb658e276b20ad4309446e8173` |
  | cardinal | `cardinal/conanfile.py` | `a33638c3aa0e7deac5f8d1d5cc32b25d68b8daf0` |

  Notes:
  - `milvus` declares `milvus-common`, `libbson`, `azure-sdk-for-cpp` and `aws-sdk-cpp`
    explicitly so CMakeDeps emits standalone `find_package` configs.
  - `milvus-storage` pins `arrow/17.0.0@milvus/dev-2.6` while `milvus` pins
    `arrow/17.0.0@milvus/dev`.
  - `knowhere` is the only consumer forcing `fmt/12.1.0`; all others use `fmt/11.2.0`.
  - `knowhere` adds `fast_float`, `liburing` (Linux), `hdf5` (benchmark) and `catch2` (UT).
  - `milvus-common` version differs between consumers: `1.0.0-b589c5a` (milvus, knowhere,
    cardinal) vs `1.0.0-60a563c` (milvus-storage).

## Direct Dependencies

### milvus (`internal/core/conanfile.py`)

#### In `requires` tuple

| Package | Version | User/Channel | Revision |
|---------|---------|-------------|----------|
| rocksdb | 6.29.5 | @milvus/dev | 67b8ae76ad7be5f779082f67416f89bf |
| onetbb | 2021.9.0 | - | f9d7a3aa294ac4a594a93f9b4c7f272d |
| zstd | 1.5.5 | - | 70dc5eb8ea16708fc946fbac884c507e |
| arrow | 17.0.0 | @milvus/dev | 17b7257ae0de563ed6ab7b7843cedf86 |
| libevent | 2.1.12 | - | 95065aaefcd58d3956d6dfbfc5631d97 |
| googleapis | cci.20221108 | - | 4553d68a2429cc0fff7d2bab4e5b3ea9 |
| gtest | 1.13.0 | - | 2cf98fac7337eb73fc4ee839dbcd4468 |
| benchmark | 1.7.0 | - | 459f3bb1a64400a886ba43047576df3c |
| yaml-cpp | 0.7.0 | - | 355a88fb838abacfeb022dd52b91e248 |
| marisa | 0.2.6 | - | a1352b20c0c6c48fee4968584ffef631 |
| glog | 0.7.1 | - | a306e61d7b8311db8cb148ad62c48030 |
| gflags | 2.2.2 | - | 7671803f1dc19354cc90bd32874dcfda |
| double-conversion | 3.3.0 | - | 640e35791a4bac95b0545e2f54b7aceb |
| libsodium | 1.0.19 | - | (none) |
| xsimd | 9.0.1 | - | 51df19a2d512f70597105ee2a2d21916 |
| xz_utils | 5.4.5 | - | fc4e36861e0a47ecd4a40a00e6d29ac8 |
| prometheus-cpp | 1.2.4 | - | 0918d66c13f97acb7809759f9de49b3f |
| re2 | 20230301 | - | f8efaf45f98d0193cd0b2ea08b6b4060 |
| folly | 2026.04.20.00 | @milvus/dev | 06852bea5b6449f0c4eb0df002b5779c |
| milvus-common | 1.0.0-b589c5a | @milvus/dev | d431af735c8acb829feb7a94f05daf42 |
| google-cloud-cpp | 2.28.0 | @milvus/dev | 468918b43cec43624531a0340398cf43 |
| opentelemetry-cpp | 1.23.0 | @milvus/dev | 11bc565ec6e82910ae8f7471da756720 |
| librdkafka | 1.9.1 | - | ec1a00d5414f618555799be9566adfb7 |
| roaring | 3.0.0 | - | 25a703f80eda0764a31ef939229e202d |
| crc32c | 1.1.2 | - | (none) |
| simde | 0.8.2 | - | 5e1edfd5cba92f25d79bf6ef4616b972 |
| xxhash | 0.8.3 | - | caa6d0af1b951c247922e38fbcebdbe6 |
| unordered_dense | 4.4.0 | - | 6a855c992618cc4c63019109a2e47298 |
| geos | 3.12.0 | - | a923af6dc4c18f87a7dfa960118f3166 |
| icu | 74.2 | - | cd1937b9561b8950a2ae6311284c5813 |
| libavrocpp | 1.12.1.1 | @milvus/dev | b4854183542196740ec9a004fdfff7ec |

#### In `requirements()` method (force=True / override)

| Package | Version | User/Channel | Revision | Notes |
|---------|---------|-------------|----------|-------|
| boost | 1.83.0 | - | 4e8a94ac1b88312af95eded83cd81ca8 | force=True |
| openssl | 3.3.2 | - | 9f9f130d58e7c13e76bb8a559f0a6a8b | force=True |
| protobuf | 5.27.0 | @milvus/dev | 42f031a96d21c230a6e05bcac4bdd633 | force=True |
| grpc | 1.67.1 | @milvus/dev | efeaa484b59bffaa579004d5e82ec4fd | force=True |
| zlib | 1.3.1 | - | 8045430172a5f8d56ba001b14561b4ea | force=True |
| libcurl | 8.10.1 | - | a3113369c86086b0e84231844e7ed0a9 | force=True |
| nlohmann_json | 3.11.3 | - | ffb9e9236619f1c883e36662f944345d | force=True |
| abseil | 20250127.0 | - | 481edcc75deb0efb16500f511f0f0a1c | force=True |
| fmt | 11.2.0 | - | eb98daa559c7c59d591f4720dde4cd5c | force=True |
| libbson | 1.30.6 | @milvus/dev | 4fc4c269cbda1b46c3118fa396cdc690 | direct, CMakeDeps config |
| azure-sdk-for-cpp | 1.16.4 | @milvus/dev | 7c95e3df67cfea28b3cf6dbd60fbf137 | force=True |
| aws-sdk-cpp | 1.11.842 | @milvus/dev | 363556887f622db23a10168c108dd55d | force=True |
| snappy | 1.2.1 | - | b940695c64ccbff63c1aabd4b1eee3f3 | force=True |
| lz4 | 1.10.0 | - | 982d9b673900f665a1da109e09c17cab | force=True |
| rapidjson | cci.20230929 | - | 0a3982e5f4fa453a9b9cd0dd5b1dcb3a | force=True |
| openblas | 0.3.30 | - | (none) | Linux only |
| libunwind | 1.8.1 | - | 748a981ace010b80163a08867b732e71 | non-macOS |
| s2n | 1.6.0 | - | 4fa3b751b92e126a55e45dce723f0384 | Linux/FreeBSD, force=True |

### milvus-common (`conanfile.py`)

| Package | Version | User/Channel | Revision | Force/Override | Notes |
|---------|---------|-------------|----------|----------------|-------|
| glog | 0.7.1 | - | a306e61d7b8311db8cb148ad62c48030 | - | tuple |
| prometheus-cpp | 1.2.4 | - | 0918d66c13f97acb7809759f9de49b3f | - | tuple |
| gflags | 2.2.2 | - | 7671803f1dc19354cc90bd32874dcfda | - | tuple |
| opentelemetry-cpp | 1.23.0 | @milvus/dev | 11bc565ec6e82910ae8f7471da756720 | - | tuple |
| grpc | 1.67.1 | @milvus/dev | efeaa484b59bffaa579004d5e82ec4fd | - | tuple |
| abseil | 20250127.0 | - | 481edcc75deb0efb16500f511f0f0a1c | - | tuple |
| xz_utils | 5.4.5 | - | fc4e36861e0a47ecd4a40a00e6d29ac8 | - | tuple |
| zlib | 1.3.1 | - | 8045430172a5f8d56ba001b14561b4ea | - | tuple |
| libevent | 2.1.12 | - | 95065aaefcd58d3956d6dfbfc5631d97 | - | tuple |
| folly | 2026.04.20.00 | @milvus/dev | 06852bea5b6449f0c4eb0df002b5779c | - | tuple |
| boost | 1.83.0 | - | 4e8a94ac1b88312af95eded83cd81ca8 | - | tuple |
| protobuf | 5.27.0 | @milvus/dev | 42f031a96d21c230a6e05bcac4bdd633 | force, override | |
| lz4 | 1.9.4 | - | 7f0b5851453198536c14354ee30ca9ae | force, override | differs from milvus (1.10.0) |
| openssl | 3.3.2 | - | 9f9f130d58e7c13e76bb8a559f0a6a8b | force, override | |
| libcurl | 8.10.1 | - | a3113369c86086b0e84231844e7ed0a9 | force, override | |
| fmt | 11.2.0 | - | eb98daa559c7c59d591f4720dde4cd5c | force | |
| nlohmann_json | 3.11.3 | - | ffb9e9236619f1c883e36662f944345d | force | |
| libunwind | 1.8.1 | - | 748a981ace010b80163a08867b732e71 | - | non-macOS |
| openblas | 0.3.30 | - | (none) | - | Linux only |
| gtest | 1.15.0 | - | - | test_requires | when with_ut=True |

### milvus-storage (`cpp/conanfile.py`)

| Package | Version | User/Channel | Revision | Force/Override | Notes |
|---------|---------|-------------|----------|----------------|-------|
| xz_utils | 5.4.5 | - | fc4e36861e0a47ecd4a40a00e6d29ac8 | - | |
| glog | 0.7.1 | - | a306e61d7b8311db8cb148ad62c48030 | - | |
| zstd | 1.5.5 | - | 70dc5eb8ea16708fc946fbac884c507e | - | |
| fmt | 11.2.0 | - | eb98daa559c7c59d591f4720dde4cd5c | force | |
| prometheus-cpp | 1.2.4 | - | 0918d66c13f97acb7809759f9de49b3f | - | |
| gflags | 2.2.2 | - | 7671803f1dc19354cc90bd32874dcfda | - | |
| boost | 1.83.0 | - | 4e8a94ac1b88312af95eded83cd81ca8 | force | |
| arrow | 17.0.0 | @milvus/dev-2.6 | c743ea7a6f2420ba5811b2be3df59892 | - | dev-2.6 channel |
| openssl | 3.3.2 | - | 9f9f130d58e7c13e76bb8a559f0a6a8b | force, override | |
| zlib | 1.3.1 | - | 8045430172a5f8d56ba001b14561b4ea | - | |
| libcurl | 8.10.1 | - | a3113369c86086b0e84231844e7ed0a9 | force, override | |
| folly | 2026.04.20.00 | @milvus/dev | 06852bea5b6449f0c4eb0df002b5779c | - | |
| libavrocpp | 1.12.1.1 | @milvus/dev | cde7bb587a29f6f233bae7e18b71815d | - | rev differs from milvus |
| google-cloud-cpp | 2.28.0 | @milvus/dev | 468918b43cec43624531a0340398cf43 | - | |
| opentelemetry-cpp | 1.23.0 | @milvus/dev | 11bc565ec6e82910ae8f7471da756720 | - | |
| milvus-common | 1.0.0-60a563c | @milvus/dev | a7448f82ed17d10934eacb6d1b152fd8 | - | version 60a563c |
| azure-sdk-for-cpp | 1.16.4 | @milvus/dev | 7c95e3df67cfea28b3cf6dbd60fbf137 | force | |
| aws-sdk-cpp | 1.11.842 | @milvus/dev | 363556887f622db23a10168c108dd55d | force | |
| protobuf | 5.27.0 | @milvus/dev | 42f031a96d21c230a6e05bcac4bdd633 | force | |
| grpc | 1.67.1 | @milvus/dev | efeaa484b59bffaa579004d5e82ec4fd | force, override | |
| abseil | 20250127.0 | - | 481edcc75deb0efb16500f511f0f0a1c | force, override | |
| nlohmann_json | 3.11.3 | - | ffb9e9236619f1c883e36662f944345d | force | |
| snappy | 1.2.1 | - | b940695c64ccbff63c1aabd4b1eee3f3 | force, override | |
| lz4 | 1.9.4 | - | 7f0b5851453198536c14354ee30ca9ae | force, override | differs from milvus (1.10.0) |
| benchmark | 1.8.3 | - | - | - | with_benchmark=True |
| gtest | 1.15.0 | - | - | - | with_ut=True |
| libunwind | 1.8.1 | - | 748a981ace010b80163a08867b732e71 | - | non-macOS |

### knowhere (`conanfile.py`)

| Package | Version | User/Channel | Revision | Force/Override | Notes |
|---------|---------|-------------|----------|----------------|-------|
| abseil | 20250127.0 | - | 481edcc75deb0efb16500f511f0f0a1c | - | |
| boost | 1.83.0 | - | 4e8a94ac1b88312af95eded83cd81ca8 | - | |
| milvus-common | 1.0.0-b589c5a | @milvus/dev | d431af735c8acb829feb7a94f05daf42 | - | |
| gflags | 2.2.2 | - | 7671803f1dc19354cc90bd32874dcfda | - | |
| glog | 0.7.1 | - | a306e61d7b8311db8cb148ad62c48030 | - | |
| nlohmann_json | 3.11.3 | - | ffb9e9236619f1c883e36662f944345d | force | |
| openssl | 3.3.2 | - | 9f9f130d58e7c13e76bb8a559f0a6a8b | force, override | |
| prometheus-cpp | 1.2.4 | - | 0918d66c13f97acb7809759f9de49b3f | - | |
| zlib | 1.3.1 | - | 8045430172a5f8d56ba001b14561b4ea | - | |
| double-conversion | 3.3.0 | - | 640e35791a4bac95b0545e2f54b7aceb | - | |
| xz_utils | 5.4.5 | - | fc4e36861e0a47ecd4a40a00e6d29ac8 | - | |
| protobuf | 5.27.0 | @milvus/dev | 42f031a96d21c230a6e05bcac4bdd633 | force, override | |
| lz4 | 1.10.0 | - | 982d9b673900f665a1da109e09c17cab | force, override | matches milvus |
| liburing | 2.8 | - | - | force, override | Linux only |
| fmt | 12.1.0 | - | - | force, override | only consumer on fmt/12.1.0 |
| libevent | 2.1.12 | - | 95065aaefcd58d3956d6dfbfc5631d97 | - | |
| grpc | 1.67.1 | @milvus/dev | efeaa484b59bffaa579004d5e82ec4fd | - | |
| folly | 2026.04.20.00 | @milvus/dev | 06852bea5b6449f0c4eb0df002b5779c | - | |
| fast_float | 8.0.0 | @milvus/dev | c7802833c74c5a86ffed70e4af1a795e | - | |
| libcurl | 8.10.1 | - | a3113369c86086b0e84231844e7ed0a9 | force, override | |
| simde | 0.8.2 | - | 5e1edfd5cba92f25d79bf6ef4616b972 | - | |
| xxhash | 0.8.3 | - | caa6d0af1b951c247922e38fbcebdbe6 | - | |
| openblas | 0.3.30 | - | aca4131c143d4c109923372e052c643c | - | Linux only, pinned RREV |
| opentelemetry-cpp | 1.23.0 | @milvus/dev | 11bc565ec6e82910ae8f7471da756720 | - | skipped when with_light=True |
| libunwind | 1.8.1 | - | 748a981ace010b80163a08867b732e71 | - | non-macOS |
| catch2 | 3.7.1 | - | - | - | with_ut=True |
| gtest | 1.15.0 | - | - | - | with_benchmark / with_faiss_tests |
| hdf5 | 1.14.5 | - | - | - | with_benchmark=True |

### cardinal (`conanfile.py`)

| Package | Version | User/Channel | Revision | Force/Override | Notes |
|---------|---------|-------------|----------|----------------|-------|
| gflags | 2.2.2 | - | 7671803f1dc19354cc90bd32874dcfda | - | |
| boost | 1.83.0 | - | 4e8a94ac1b88312af95eded83cd81ca8 | - | |
| glog | 0.7.1 | - | a306e61d7b8311db8cb148ad62c48030 | - | |
| openssl | 3.3.2 | - | 9f9f130d58e7c13e76bb8a559f0a6a8b | force, override | |
| zlib | 1.3.1 | - | 8045430172a5f8d56ba001b14561b4ea | - | |
| xz_utils | 5.4.5 | - | fc4e36861e0a47ecd4a40a00e6d29ac8 | - | |
| nlohmann_json | 3.11.3 | - | ffb9e9236619f1c883e36662f944345d | force | |
| folly | 2026.04.20.00 | @milvus/dev | 06852bea5b6449f0c4eb0df002b5779c | - | |
| fmt | 11.2.0 | - | eb98daa559c7c59d591f4720dde4cd5c | force, override | |
| prometheus-cpp | 1.2.4 | - | 0918d66c13f97acb7809759f9de49b3f | - | |
| opentelemetry-cpp | 1.23.0 | @milvus/dev | 11bc565ec6e82910ae8f7471da756720 | - | |
| milvus-common | 1.0.0-b589c5a | @milvus/dev | d431af735c8acb829feb7a94f05daf42 | - | |
| libevent | 2.1.12 | - | 95065aaefcd58d3956d6dfbfc5631d97 | - | |
| libcurl | 8.10.1 | - | a3113369c86086b0e84231844e7ed0a9 | force, override | |
| openblas | 0.3.30 | - | (none) | - | Linux only |
| libunwind | 1.8.1 | - | 748a981ace010b80163a08867b732e71 | - | non-macOS |
| catch2 | 3.7.1 | - | - | - | with_ut=True |

## Full Resolved Package List

Union of direct requirements across all five conanfiles, plus their known transitive
dependencies. Versions and RREVs shown reflect the most common / strictest pin.

### Runtime/Library Packages

| # | Package | Version | User/Channel | Direct Dependencies |
|---|---------|---------|-------------|-------------------|
| 1 | abseil | 20250127.0 | - | (none) |
| 2 | arrow | 17.0.0 | @milvus/dev or @milvus/dev-2.6 | thrift, jemalloc, boost, rapidjson, **aws-sdk-cpp**, **azure-sdk-for-cpp**, xsimd, zstd, re2, openssl, snappy, lz4, bz2, protobuf, gflags, glog |
| 3 | aws-c-* | 0.12.5-based chain | - | (see AWS SDK chain below) |
| 4 | **aws-sdk-cpp** | **1.11.842** | **@milvus/dev** | aws-crt-cpp, aws-c-common, aws-c-event-stream, aws-checksums, aws-c-cal, aws-c-http, aws-c-io, aws-c-auth, aws-c-compression, aws-c-mqtt, aws-c-sdkutils, aws-c-s3 (s3-crt), libcurl, openssl |
| 5 | **azure-sdk-for-cpp** | **1.16.4** | **@milvus/dev** | libcurl, openssl, libxml2 |
| 6 | benchmark | 1.7.0 (milvus) / 1.8.3 (storage) | - | (none) |
| 7 | boost | 1.83.0 | - | zlib, bzip2, libbacktrace |
| 8 | bzip2 | 1.0.8 | - | (none) |
| 9 | c-ares | 1.19.1 | - | (none) |
| 10 | catch2 | 3.7.1 | - | (none, test only) |
| 11 | crc32c | 1.1.2 | - | (none) |
| 12 | cyrus-sasl | 2.1.27 | - | openssl, zlib |
| 13 | double-conversion | 3.3.0 | - | (none) |
| 14 | fast_float | 8.0.0 | @milvus/dev | (none, header_only) |
| 15 | fmt | 11.2.0 (milvus/common/storage/cardinal) / 12.1.0 (knowhere) | - | (none) |
| 16 | **folly** | **2026.04.20.00** | **@milvus/dev** | boost, bzip2, double-conversion, glog, gflags, libevent, openssl, lz4, snappy, zstd, libdwarf, libsodium, libiberty, libunwind, xz_utils, zlib, fmt |
| 17 | geos | 3.12.0 | - | (none) |
| 18 | gflags | 2.2.2 | - | (none) |
| 19 | glog | 0.7.1 | - | gflags, libunwind |
| 20 | google-cloud-cpp | 2.28.0 | @milvus/dev | abseil, nlohmann_json, crc32c, libcurl, openssl, zlib (storage-only) |
| 21 | googleapis | cci.20221108 | - | protobuf |
| 22 | **grpc** | **1.67.1** | **@milvus/dev** | abseil, **protobuf**, c-ares, openssl, re2, zlib |
| 23 | gtest | 1.13.0 (milvus) / 1.15.0 (others) | - | (none) |
| 24 | hdf5 | 1.14.5 | - | zlib (knowhere benchmark only) |
| 25 | hwloc | 2.9.3 | - | (none) |
| 26 | icu | 74.2 | - | (none) |
| 27 | jemalloc | 5.3.0 | - | (none) |
| 28 | **libavrocpp** | **1.12.1.1** | **@milvus/dev** | boost/[>=1.81 <=1.89], snappy/[>=1.1.9], fmt/[>=11 <13], zlib/[>=1.3.1] |
| 29 | libbacktrace | cci.20210118 | - | (none) |
| 30 | **libbson** | **1.30.6** | **@milvus/dev** | (none) |
| 31 | libcurl | 8.10.1 | - | openssl, zlib |
| 32 | libdwarf | 20191104 | - | libelf, zlib |
| 33 | libelf | 0.8.13 | - | (none) |
| 34 | libevent | 2.1.12 | - | openssl, zlib |
| 35 | libiberty | 9.1.0 | - | (none) |
| 36 | libiconv | 1.17 | - | (none) |
| 37 | librdkafka | 1.9.1 | - | lz4, zstd(opt), cyrus-sasl(opt), openssl(opt), zlib(opt) |
| 38 | libsodium | 1.0.19 | - | (none) |
| 39 | libunwind | 1.8.1 | - | xz_utils, zlib |
| 40 | liburing | 2.8 | - | (none, Linux only) |
| 41 | libxml2 | 2.15.1 | - | libiconv, zlib |
| 42 | lz4 | 1.10.0 (milvus/knowhere) / 1.9.4 (common/storage) | - | (none) |
| 43 | marisa | 0.2.6 | - | (none) |
| 44 | **milvus-common** | **1.0.0-b589c5a / 1.0.0-60a563c** | **@milvus/dev** | glog, prometheus-cpp, gflags, opentelemetry-cpp, grpc, abseil, xz_utils, zlib, libevent, folly, boost |
| 45 | nlohmann_json | 3.11.3 | - | (none, header_only) |
| 46 | onetbb | 2021.9.0 | - | hwloc |
| 47 | openblas | 0.3.30 | - | (none) |
| 48 | openssl | 3.3.2 | - | zlib |
| 49 | **opentelemetry-cpp** | **1.23.0** | **@milvus/dev** | opentelemetry-proto/1.7.0, **grpc/1.67.1@milvus/dev**, abseil, **protobuf/5.27.0@milvus/dev**, nlohmann_json/3.11.3, libcurl/8.10.1, openssl/3.3.2 |
| 50 | opentelemetry-proto | 1.7.0 | - | (none) |
| 51 | prometheus-cpp | 1.2.4 | - | zlib (with_pull=False: no civetweb) |
| 52 | **protobuf** | **5.27.0** | **@milvus/dev** | abseil, zlib |
| 53 | rapidjson | cci.20230929 | - | (none, header_only) |
| 54 | re2 | 20230301 | - | (none) |
| 55 | roaring | 3.0.0 | - | (none) |
| 56 | **rocksdb** | **6.29.5** | **@milvus/dev** | zstd (only dep; other with_* default False) |
| 57 | s2n | 1.6.0 | - | openssl (overrides s2n/1.4.1 from aws-c-io) |
| 58 | simde | 0.8.2 | - | (none, header_only) |
| 59 | snappy | 1.2.1 | - | (none) |
| 60 | thrift | 0.17.0 | - | boost, libevent, openssl, zlib |
| 61 | unordered_dense | 4.4.0 | - | (none, header_only) |
| 62 | xsimd | 9.0.1 | - | (none, header_only) |
| 63 | xxhash | 0.8.3 | - | (none) |
| 64 | xz_utils | 5.4.5 | - | (none) |
| 65 | yaml-cpp | 0.7.0 | - | (none) |
| 66 | zlib | 1.3.1 | - | (none) |
| 67 | zstd | 1.5.5 | - | (none) |

### Build Tool Packages

| # | Package | Version | Used By |
|---|---------|---------|---------|
| 1 | autoconf | 2.71 | libelf, jemalloc, libcurl, libtool |
| 2 | automake | 1.16.5 | jemalloc, libtool, libcurl |
| 3 | b2 | 5.4.2 | boost |
| 4 | bison | 3.8.2 | thrift |
| 5 | cmake | 3.31.11 | glog, folly, googleapis, libxml2, arrow |
| 6 | flex | 2.6.4 | thrift, bison |
| 7 | gnu-config | cci.20210814 | cyrus-sasl, libelf, libtool |
| 8 | libtool | 2.4.7 | libcurl |
| 9 | m4 | 1.4.19 | autoconf, flex, bison |
| 10 | meson | 1.10.1 | pkgconf, simde |
| 11 | ninja | 1.11.1 | meson |
| 12 | pkgconf | 1.9.3 / 2.0.3 / 2.1.0 | librdkafka, onetbb, simde, libcurl |

## Dependency Chains

### gRPC Chain
```
zlib/[>=1.2.11 <2]
abseil/[>=20240116.1 <=20250127.0]
protobuf/5.27.0@milvus/dev --> abseil, zlib
c-ares/[>=1.19.1 <2]
openssl/[>=1.1 <4]
re2/20230301
    |
    +-- grpc/1.67.1@milvus/dev --> abseil, protobuf, c-ares, openssl,
                                    re2, zlib
```

### Google Cloud Chain (storage-only, REST)
```
abseil/20250127.0
nlohmann_json/3.11.3
crc32c/1.1.2
libcurl/8.10.1
openssl/3.3.2
zlib/1.3.1
    |
    +-- google-cloud-cpp/2.28.0@milvus/dev --> abseil,
                                     nlohmann_json, crc32c,
                                     libcurl, openssl, zlib
```
Note: google-cloud-cpp/2.28.0@milvus/dev builds the storage component only (REST, no
grpc/protobuf). No relationship with aws-c-common or the AWS C SDK chain.

### OpenTelemetry Chain
```
opentelemetry-proto/1.7.0
grpc/1.67.1@milvus/dev
abseil/20250127.0
protobuf/5.27.0@milvus/dev
nlohmann_json/3.11.3 (forced)
libcurl/8.10.1        (forced)
openssl/3.3.2         (forced)
    |
    +-- opentelemetry-cpp/1.23.0@milvus/dev --> opentelemetry-proto, grpc,
                                                 abseil, protobuf, nlohmann_json,
                                                 libcurl, openssl
```
Note: otel 1.23.0 removed Jaeger support (no more thrift/boost deps).
with_prometheus=False by default — prometheus-cpp is a direct Milvus dep, not through otel.

### AWS SDK Chain (0.12.5-based, declared in aws-sdk-cpp recipe)

The aws-sdk-cpp/1.11.842 recipe pins specific aws-c-* versions (0.12.5-based chain),
resolved from CCI at build time.

```
aws-c-common/0.12.5
    |
    +-- aws-checksums/0.2.6
    +-- aws-c-compression/0.3.1
    +-- aws-c-sdkutils/0.2.4
    +-- aws-c-cal/0.9.8 -----> openssl
    |
    +-- aws-c-io/0.23.2 -----> aws-c-cal, s2n/1.6.0 (overridden by Milvus)
    |
    +-- aws-c-http/0.10.5 ---> aws-c-io, aws-c-compression
    |
    +-- aws-c-auth/0.9.1 ---> aws-c-http, aws-c-sdkutils
    +-- aws-c-mqtt/0.13.3 --> aws-c-http
    |
    +-- aws-c-event-stream/0.5.7 --> aws-c-io, aws-checksums
    +-- aws-c-s3/0.9.2 -----------> aws-c-auth, aws-c-http, aws-checksums
    |
    +-- aws-crt-cpp/0.35.2 --> aws-c-mqtt, aws-c-event-stream, aws-c-s3,
    |                           aws-c-auth, aws-c-sdkutils, aws-c-http,
    |                           aws-c-io, aws-c-cal, s2n, aws-checksums
    |
    +-- aws-sdk-cpp/1.11.842@milvus/dev --> all above + libcurl, openssl
```

### Folly Chain (recipe: recipes/folly/v2024/conanfile.py)
```
boost/1.83.0 ---------> zlib, bzip2, libbacktrace/cci.20210118
double-conversion/3.3.0
gflags/2.2.2
glog/0.7.1 -----------> gflags, libunwind/1.8.1
libevent/2.1.12 ------> openssl, zlib
lz4/1.10.0
snappy/1.2.1
zstd/1.5.5
libsodium/1.0.19
xz_utils/5.4.5
libunwind/1.8.1 ------> xz_utils, zlib
fmt/11.2.0
libdwarf/20191104 ----> libelf/0.8.13, zlib
libiberty/9.1.0 (Linux)
openssl/3.3.2
zlib/1.3.1
    |
    +-- folly/2026.04.20.00@milvus/dev --> boost, bzip2, double-conversion,
                                            glog, gflags, libevent, openssl,
                                            lz4, snappy, zstd, libdwarf,
                                            libsodium, libiberty, libunwind,
                                            xz_utils, zlib, fmt
```

### Arrow Chain (recipe: recipes/arrow/all/conanfile.py)

Arrow deps are conditional on options. Milvus/storage use with_thrift, with_boost,
with_openssl, with_s3, with_azure, with_re2, with_zstd, with_snappy, with_lz4,
filesystem_layer, parquet, compute, encryption:

```
thrift/0.17.0         (with_thrift)
jemalloc/5.3.0        (with_jemalloc, storage; milvus disables)
boost/1.83.0          (with_boost; forced)
rapidjson/cci.20230929 (encryption=True; forced)
aws-sdk-cpp/1.11.842@milvus/dev  (with_s3)
azure-sdk-for-cpp/1.16.4@milvus/dev  (with_azure) --> libcurl, openssl, libxml2
xsimd/9.0.1           (simd_level/runtime_simd_level)
zstd/1.5.5            (with_zstd)
re2/20230301          (with_re2)
snappy/1.2.1          (with_snappy)
lz4/1.10.0            (with_lz4)
openssl/3.3.2         (with_openssl)
    |
    +-- arrow/17.0.0@milvus/dev (or @milvus/dev-2.6 for storage)
                          --> thrift, jemalloc, boost, rapidjson,
                              aws-sdk-cpp, azure-sdk-for-cpp,
                              xsimd, zstd, re2, snappy, lz4, openssl
```

### RocksDB Chain (recipe: recipes/rocksdb/all/conanfile.py)

All with_* options default to False. Milvus only sets with_zstd=True.

```
zstd/1.5.5  (with_zstd=True)
    |
    +-- rocksdb/6.29.5@milvus/dev --> zstd
```

### libavrocpp Chain (recipe: recipes/libavrocpp/v2/conanfile.py)

```
boost/[>=1.81.0 <=1.89.0]
snappy/[>=1.1.9 <2]
fmt/[>=11 <13]
zlib/[>=1.3.1 <2]
    |
    +-- libavrocpp/1.12.1.1@milvus/dev --> boost, snappy, fmt, zlib
```

### librdkafka Chain (recipe: recipes/librdkafka/all/conanfile.py)

With Milvus options (zstd=True, ssl=True, sasl=True):

```
lz4/1.10.0            (always required)
zstd/1.5.5            (zstd=True)
cyrus-sasl/2.1.27 --- (sasl=True, Linux) --> openssl, zlib
openssl/3.3.2         (ssl=True)
zlib/1.3.1            (zlib=True, default)
    |
    +-- librdkafka/1.9.1 --> lz4, zstd, cyrus-sasl, openssl, zlib
```

## Custom Channel Packages (@milvus/*)

These packages have custom recipes in this repo:

| Package | Version | Channel | Why Custom |
|---------|---------|---------|------------|
| protobuf | 5.27.0 | @milvus/dev | Pinned version for grpc/1.67.1 compatibility |
| grpc | 1.67.1 | @milvus/dev | Uses protobuf/5.27.0@milvus/dev |
| opentelemetry-cpp | 1.23.0 | @milvus/dev | Uses grpc/1.67.1@milvus/dev, protobuf/5.27.0@milvus/dev |
| folly | 2026.04.20.00 | @milvus/dev | Milvus-compatible dep versions |
| google-cloud-cpp | 2.28.0 | @milvus/dev | Milvus-compatible dep versions (storage-only) |
| rocksdb | 6.29.5 | @milvus/dev | Custom build options for Milvus |
| libavrocpp | 1.12.1.1 | @milvus/dev | Custom recipe |
| aws-sdk-cpp | 1.11.842 | @milvus/dev | Custom build config |
| azure-sdk-for-cpp | 1.16.4 | @milvus/dev | Custom recipe |
| libbson | 1.30.6 | @milvus/dev | BSON C library only (not full mongo-c-driver) |
| fast_float | 8.0.0 | @milvus/dev | Custom recipe (knowhere) |
| arrow | 17.0.0 | @milvus/dev and @milvus/dev-2.6 | Custom build with S3, Azure, encryption |
| milvus-common | 1.0.0-b589c5a / 1.0.0-60a563c | @milvus/dev | Milvus C++ common library |

## Build Order (scripts/build-milvus-deps.sh)

### Phase 1: Foundation (no dependencies)
```
zlib/1.3.1
bzip2/1.0.8
lz4/1.10.0
snappy/1.2.1
zstd/1.5.5
gflags/2.2.2 (shared=True)
double-conversion/3.3.0 (shared=True)
crc32c/1.1.2
libbson/1.30.6@milvus/dev
nlohmann_json/3.11.3
rapidjson/cci.20230929
xsimd/9.0.1
fmt/11.2.0
yaml-cpp/0.7.0
marisa/0.2.6
geos/3.12.0
roaring/3.0.0 (from conancenter)
gtest/1.13.0
ninja/1.11.1, m4/1.4.19, cmake/3.31.11
opentelemetry-proto/1.7.0
```

### Phase 2: Basic Dependencies (Level 1)
```
xz_utils/5.4.5 (shared=True)
openssl/3.3.2 (shared=False, no_apps=True) [from conancenter]
c-ares/1.19.1
abseil/20250127.0
protobuf/5.27.0@milvus/dev (shared=True)
libunwind/1.8.1
s2n/1.6.0
libevent/2.1.12 (shared=True)
libsodium/1.0.19
re2/20230301
glog/0.7.1 (shared=True)
benchmark/1.7.0
flex/2.6.4, autoconf/2.71
libiberty/9.1.0
```

### Phase 3: Intermediate (Level 2)
```
automake/1.16.5
meson/1.2.2
boost/1.83.0
onetbb/2021.9.0
jemalloc/5.3.0
googleapis/cci.20221108
prometheus-cpp/1.2.4 (with_pull=False) [from conancenter]
libdwarf/20191104
```

### Phase 4: Complex Libraries (Level 3)
```
libtool/2.4.7
bison/3.8.2
grpc/1.67.1@milvus/dev
librdkafka/1.9.1
libcurl/8.10.1 [from conancenter]
```

### Phase 5: High-Level Libraries (Level 4)
```
thrift/0.17.0
azure-sdk-for-cpp/1.16.4@milvus/dev
```

### Phase 6: AWS SDK (Level 5-7)
```
aws-sdk-cpp/1.11.842@milvus/dev  (uses CCI 0.12.5 chain)
```

### Phase 7: Application Libraries
```
opentelemetry-cpp/1.23.0@milvus/dev
folly/2026.04.20.00@milvus/dev
google-cloud-cpp/2.28.0@milvus/dev
rocksdb/6.29.5@milvus/dev
libavrocpp/1.12.1.1@milvus/dev
milvus-common/1.0.0-b589c5a@milvus/dev
```

### Phase 8: Final
```
arrow/17.0.0@milvus/dev
```

### Phase 9: Conancenter-only packages
```
simde/0.8.2
xxhash/0.8.3
unordered_dense/4.4.0
icu/74.2
```

## Packages with Multiple Versions

- `fmt`: 11.2.0 (milvus, milvus-common, milvus-storage, cardinal) vs 12.1.0 (knowhere).
- `lz4`: 1.10.0 (milvus, knowhere) vs 1.9.4 (milvus-common, milvus-storage).
- `arrow`: 17.0.0@milvus/dev (milvus) vs 17.0.0@milvus/dev-2.6 (milvus-storage).
- `milvus-common`: 1.0.0-b589c5a (milvus, knowhere, cardinal) vs 1.0.0-60a563c
  (milvus-storage).
- `libavrocpp`: RREV `b4854183...` (milvus) vs `cde7bb58...` (milvus-storage).
- `gtest`: 1.13.0 (milvus) vs 1.15.0 (milvus-common/storage, knowhere, cardinal tests).
- `benchmark`: 1.7.0 (milvus) vs 1.8.3 (milvus-storage).

## ASCII Dependency Tree

Full dependency tree from Milvus's perspective. Each node shows `package/version[@user/channel]`.
Only runtime dependencies are shown (build tools in separate tree below).

Versions shown are from the scanned conanfiles. Where recipes declare version ranges,
the resolved version depends on the consumers' force=True overrides.

```
milvus/internal/core conanfile.py
|
|-- (requires tuple)
|-- rocksdb/6.29.5@milvus/dev .......................... zstd
|-- onetbb/2021.9.0 .................................... hwloc/2.9.3
|-- zstd/1.5.5 .......................................... (no deps)
|-- arrow/17.0.0@milvus/dev ............................. (see Arrow chain)
|-- libevent/2.1.12 .................................... openssl, zlib
|-- googleapis/cci.20221108 ............................ protobuf
|-- gtest/1.13.0 ........................................ (no deps)
|-- benchmark/1.7.0 ..................................... (no deps)
|-- yaml-cpp/0.7.0 ...................................... (no deps)
|-- marisa/0.2.6 ........................................ (no deps)
|-- glog/0.7.1 .......................................... gflags, libunwind(Linux)
|-- gflags/2.2.2 ........................................ (no deps)
|-- double-conversion/3.3.0 ............................. (no deps)
|-- libsodium/1.0.19 .................................... (no deps)
|-- xsimd/9.0.1 ......................................... (no deps)
|-- xz_utils/5.4.5 ...................................... (no deps)
|-- prometheus-cpp/1.2.4 ................................ zlib (with_pull=False)
|-- re2/20230301 ........................................ (no deps)
|-- folly/2026.04.20.00@milvus/dev ..................... (see Folly chain)
|-- milvus-common/1.0.0-b589c5a@milvus/dev ............. (see below)
|-- google-cloud-cpp/2.28.0@milvus/dev (storage-only) ... abseil, nlohmann_json,
|                                                      crc32c, libcurl, openssl, zlib
|-- opentelemetry-cpp/1.23.0@milvus/dev ................ (see OpenTelemetry chain)
|-- librdkafka/1.9.1 .................................... lz4, zstd, cyrus-sasl, openssl, zlib
|-- roaring/3.0.0 ....................................... (no deps)
|-- crc32c/1.1.2 ....................................... (no deps)
|-- simde/0.8.2 ......................................... (no deps)
|-- xxhash/0.8.3 ........................................ (no deps)
|-- unordered_dense/4.4.0 ............................... (no deps)
|-- geos/3.12.0 ......................................... (no deps)
|-- icu/74.2 ............................................ (no deps)
|-- libavrocpp/1.12.1.1@milvus/dev ..................... boost, snappy, fmt, zlib
|
|-- (requirements() - force=True overrides)
|-- boost/1.83.0 (force) ............................... zlib, bzip2, libbacktrace
|-- openssl/3.3.2 (force) .............................. zlib
|-- protobuf/5.27.0@milvus/dev (force) ................ abseil, zlib
|-- grpc/1.67.1@milvus/dev (force) .................... abseil, protobuf, c-ares,
|                                                       openssl, re2, zlib
|-- zlib/1.3.1 (force)
|-- libcurl/8.10.1 (force) ............................. openssl, zlib
|-- nlohmann_json/3.11.3 (force) ....................... (no deps)
|-- abseil/20250127.0 (force) .......................... (no deps)
|-- fmt/11.2.0 (force) ................................. (no deps)
|-- libbson/1.30.6@milvus/dev ......................... (no deps)
|-- azure-sdk-for-cpp/1.16.4@milvus/dev (force) ....... libcurl, openssl, libxml2
|-- aws-sdk-cpp/1.11.842@milvus/dev (force) ........... (see AWS SDK chain)
|-- snappy/1.2.1 (force) ............................... (no deps)
|-- lz4/1.10.0 (force) ................................. (no deps)
|-- rapidjson/cci.20230929 (force) ..................... (no deps)
|-- openblas/0.3.30 (Linux) ............................ (no deps)
|-- libunwind/1.8.1 (non-macOS) ........................ xz_utils, zlib
|-- s2n/1.6.0 (Linux/FreeBSD, force) .................. openssl (overrides 1.4.1)
|
+-- knowhere (consumer) --> milvus-common/1.0.0-b589c5a, fmt/12.1.0, fast_float,
    liburing/2.8 (Linux), catch2/3.7.1 (UT), hdf5/1.14.5 (benchmark)
+-- cardinal (consumer) --> milvus-common/1.0.0-b589c5a, catch2/3.7.1 (UT)
+-- milvus-storage (consumer) --> arrow/17.0.0@milvus/dev-2.6,
    milvus-common/1.0.0-60a563c, benchmark/1.8.3
```

## ASCII Build Tools Tree

Build-time dependencies used during compilation. These are `tool_requires` (not linked
into final binaries).

```
m4/1.4.19 .................................................... (no deps)
|
+-- flex/2.6.4
|   +-- m4/1.4.19
|
+-- autoconf/2.71
|   +-- m4/1.4.19
|
+-- automake/1.16.5
|   +-- autoconf/2.71
|   |   +-- m4/1.4.19
|   +-- m4/1.4.19
|
+-- libtool/2.4.7
|   +-- automake/1.16.5
|   |   +-- autoconf/2.71
|   |       +-- m4/1.4.19
|   +-- gnu-config/cci.20210814
|
+-- bison/3.8.2
    +-- m4/1.4.19
    +-- flex/2.6.4

ninja/1.11.1 ................................................. (no deps)
|
+-- meson/1.10.1
    +-- ninja/1.11.1
    |
    +-- pkgconf/1.9.3
    +-- pkgconf/2.0.3
    +-- pkgconf/2.1.0

cmake/3.31.11 ................................................ (no deps)

b2/5.4.2 ..................................................... (no deps)

gnu-config/cci.20210814 ...................................... (no deps)
```

### Which packages use which build tools

```
m4/1.4.19 ............. autoconf/2.71, flex/2.6.4, bison/3.8.2
autoconf/2.71 ......... libelf/0.8.13, jemalloc/5.3.0, libcurl/8.10.1, libtool/2.4.7
automake/1.16.5 ....... jemalloc/5.3.0, libtool/2.4.7, libcurl/8.10.1
libtool/2.4.7 ......... libcurl/8.10.1
flex/2.6.4 ............ thrift/0.17.0, bison/3.8.2
bison/3.8.2 ........... thrift/0.17.0
gnu-config/cci.20210814  cyrus-sasl/2.1.27, libelf/0.8.13, libtool/2.4.7
ninja/1.11.1 .......... meson/1.10.1
meson/1.10.1 .......... pkgconf/1.9.3, pkgconf/2.0.3, pkgconf/2.1.0, simde/0.8.2
pkgconf/1.9.3 ......... librdkafka/1.9.1
pkgconf/2.0.3 ......... simde/0.8.2
pkgconf/2.1.0 ......... onetbb/2021.9.0, libcurl/8.10.1
cmake/3.31.11 ......... glog/0.7.1, folly/2026.04.20.00, googleapis/cci.20221108, libxml2/2.15.1, arrow/17.0.0
b2/5.4.2 .............. boost/1.83.0
```
