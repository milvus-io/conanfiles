# Dependency Tree for Milvus Conan Packages

This document shows the full dependency graph resolved from
- milvus/internal/core/conanfile.py
- milvus-common/conanfile.py
- milvus-storage/cpp/conanfile.py
- knowhere/conanfile.py


## Direct Dependencies

### In `requires` tuple

| Package | Version | User/Channel |
|---------|---------|-------------|
| rocksdb | 6.29.5 | @milvus/dev |
| onetbb | 2021.9.0 | - |
| zstd | 1.5.5 | - |
| lz4 | 1.9.4 | - |
| snappy | 1.2.1 | - |
| arrow | 17.0.0 | @milvus/dev-2.6 |
| libevent | 2.1.12 | - |
| googleapis | cci.20221108 | - |
| gtest | 1.13.0 | - |
| benchmark | 1.7.0 | - |
| yaml-cpp | 0.7.0 | - |
| marisa | 0.2.6 | - |
| glog | 0.7.1 | - |
| gflags | 2.2.2 | - |
| double-conversion | 3.3.0 | - |
| libsodium | cci.20220430 | - |
| xsimd | 9.0.1 | - |
| xz_utils | 5.4.5 | - |
| prometheus-cpp | 1.2.4 | - |
| re2 | 20230301 | - |
| folly | 2024.08.12.00 | @milvus/dev |
| google-cloud-cpp | 2.28.0 | @milvus/dev |
| opentelemetry-cpp | 1.23.0 | @milvus/dev |
| librdkafka | 1.9.1 | - |
| roaring | 3.0.0 | - |
| crc32c | 1.1.2 | - |
| simde | 0.8.2 | - |
| xxhash | 0.8.3 | - |
| unordered_dense | 4.4.0 | - |
| geos | 3.12.0 | - |
| icu | 74.2 | - |
| libavrocpp | 1.12.1.1 | @milvus/dev |

### In `requirements()` method

These use `force=True` to override transitive dependency versions (Conan 2.x requires explicit force).

| Package | Version | User/Channel | Notes |
|---------|---------|-------------|-------|
| boost | 1.83.0 | - | force=True |
| openssl | 3.3.2 | - | force=True |
| protobuf | 5.27.0 | @milvus/dev | force=True |
| grpc | 1.67.1 | @milvus/dev | force=True |
| zlib | 1.3.1 | - | force=True |
| libcurl | 8.10.1 | - | force=True |
| nlohmann_json | 3.11.3 | - | force=True |
| abseil | 20250127.0 | - | force=True |
| fmt | 11.0.2 | - | force=True |
| rapidjson | cci.20230929 | - | force=True |
| aws-sdk-cpp | 1.11.692 | @milvus/dev | (no force) |
| libunwind | 1.8.1 | - | Linux only |
| s2n | 1.6.0 | - | Linux only, overrides s2n/1.4.1 from aws-c-io for OpenSSL 3.x FIPS |


## Full Resolved Package List

All packages in the Milvus dependency graph.

### Runtime/Library Packages

| # | Package | Version | User/Channel | Direct Dependencies |
|---|---------|---------|-------------|-------------------|
| 1 | abseil | 20250127.0 | - | (none) |
| 2 | aws-c-auth | 0.9.1 | - | aws-c-http, aws-c-sdkutils, aws-c-common |
| 3 | aws-c-cal | 0.9.8 | - | aws-c-common, openssl |
| 4 | aws-c-common | 0.12.5 | - | (none) |
| 5 | aws-c-compression | 0.3.1 | - | aws-c-common |
| 6 | aws-c-event-stream | 0.5.7 | - | aws-checksums, aws-c-io |
| 7 | aws-c-http | 0.10.5 | - | aws-c-compression, aws-c-io |
| 8 | aws-c-io | 0.23.2 | - | aws-c-cal, aws-c-common, s2n |
| 9 | aws-c-mqtt | 0.13.3 | - | aws-c-http, aws-c-io |
| 10 | aws-c-s3 | 0.9.2 | - | aws-c-auth, aws-c-sdkutils, aws-c-http, aws-checksums, aws-c-common |
| 11 | aws-c-sdkutils | 0.2.4 | - | aws-c-common |
| 12 | aws-checksums | 0.2.6 | - | aws-c-common |
| 13 | aws-crt-cpp | 0.35.2 | - | aws-c-mqtt, aws-c-event-stream, aws-c-s3, aws-c-auth, aws-c-sdkutils, aws-c-http, aws-c-io, aws-c-cal, s2n, aws-checksums, aws-c-common |
| 14 | **aws-sdk-cpp** | **1.11.692** | **@milvus/dev** | aws-crt-cpp, aws-c-common, aws-c-event-stream, aws-checksums, aws-c-cal, aws-c-http, aws-c-io, aws-c-auth, aws-c-compression, aws-c-mqtt, aws-c-sdkutils, aws-c-s3(s3-crt), libcurl, openssl |
| 15 | **arrow** | **17.0.0** | **@milvus/dev-2.6** | thrift, jemalloc, boost, rapidjson, **aws-sdk-cpp**, **azure-sdk-for-cpp**, xsimd, zstd, re2, openssl |
| 16 | **azure-sdk-for-cpp** | **1.11.3** | **@milvus/dev** | libcurl, openssl, libxml2 |
| 17 | benchmark | 1.7.0 | - | (none) |
| 18 | boost | 1.83.0 | - | zlib, bzip2, libbacktrace |
| 19 | bzip2 | 1.0.8 | - | (none) |
| 20 | c-ares | 1.19.1 | - | (none) |
| 21 | crc32c | 1.1.2 | - | (none) |
| 22 | cyrus-sasl | 2.1.27 | - | openssl, zlib |
| 23 | double-conversion | 3.3.0 | - | (none) |
| 24 | fmt | 11.0.2 | - | (none) |
| 25 | **folly** | **2024.08.12.00** | **@milvus/dev** | boost, bzip2, double-conversion, glog, gflags, libevent, openssl, lz4, snappy, zstd, libdwarf, libsodium, libiberty, libunwind, xz_utils, zlib, fmt |
| 26 | geos | 3.12.0 | - | (none) |
| 27 | gflags | 2.2.2 | - | (none) |
| 28 | glog | 0.7.1 | - | gflags, libunwind |
| 29 | google-cloud-cpp | 2.28.0 | @milvus/dev | abseil, nlohmann_json, crc32c, libcurl, openssl, zlib (storage-only) |
| 30 | googleapis | cci.20221108 | - | protobuf |
| 31 | **grpc** | **1.67.1** | **@milvus/dev** | abseil, **protobuf**, c-ares, openssl, re2, zlib |
| 32 | gtest | 1.13.0 | - | (none) |
| 33 | hwloc | 2.9.3 | - | (none) |
| 34 | icu | 74.2 | - | (none) |
| 35 | jemalloc | 5.3.0 | - | (none) |
| 36 | **libavrocpp** | **1.12.1.1** | **@milvus/dev** | boost/[>=1.81 <=1.89], snappy/[>=1.1.9], fmt/[>=11 <13], zlib/[>=1.3.1] |
| 37 | libbacktrace | cci.20210118 | - | (none) |
| 38 | libcurl | 8.10.1 | - | openssl, zlib |
| 39 | libdwarf | 20191104 | - | libelf, zlib |
| 40 | libelf | 0.8.13 | - | (none) |
| 41 | libevent | 2.1.12 | - | openssl, zlib |
| 42 | libiberty | 9.1.0 | - | (none) |
| 43 | libiconv | 1.17 | - | (none) |
| 44 | librdkafka | 1.9.1 | - | lz4, zstd(opt), cyrus-sasl(opt), openssl(opt), zlib(opt) |
| 45 | libsodium | cci.20220430 | - | (none) |
| 46 | libunwind | 1.8.1 | - | xz_utils, zlib |
| 47 | libxml2 | 2.15.1 | - | libiconv, zlib |
| 48 | lz4 | 1.9.4 | - | (none) |
| 49 | marisa | 0.2.6 | - | (none) |
| 50 | nlohmann_json | 3.11.3 | - | (none, header_only) |
| 51 | onetbb | 2021.9.0 | - | hwloc |
| 52 | openssl | 3.3.2 | - | zlib |
| 53 | **opentelemetry-cpp** | **1.23.0** | **@milvus/dev** | opentelemetry-proto/1.7.0, **grpc/1.67.1@milvus/dev**, abseil, **protobuf/5.27.0@milvus/dev**, nlohmann_json/3.11.2, libcurl/7.86.0, openssl/1.1.1t |
| 54 | opentelemetry-proto | 1.7.0 | - | (none) |
| 55 | prometheus-cpp | 1.2.4 | - | zlib (with_pull=False: no civetweb) |
| 56 | **protobuf** | **5.27.0** | **@milvus/dev** | abseil, zlib |
| 57 | rapidjson | cci.20230929 | - | (none, header_only) (force=True override) |
| 58 | re2 | 20230301 | - | (none) |
| 59 | roaring | 3.0.0 | - | (none) |
| 60 | **rocksdb** | **6.29.5** | **@milvus/dev** | zstd (only dep; other with_* default False) |
| 61 | s2n | 1.6.0 | - | openssl (overrides s2n/1.4.1 from aws-c-io) |
| 62 | simde | 0.8.2 | - | (none, header_only) |
| 63 | snappy | 1.2.1 | - | (none) |
| 64 | thrift | 0.17.0 | - | boost, libevent, openssl, zlib |
| 65 | unordered_dense | 4.4.0 | - | (none, header_only) |
| 66 | xsimd | 9.0.1 | - | (none, header_only) |
| 67 | xxhash | 0.8.3 | - | (none) |
| 68 | xz_utils | 5.4.5 | - | (none) |
| 69 | yaml-cpp | 0.7.0 | - | (none) |
| 70 | zlib | 1.3.1 | - | (none) |
| 71 | zstd | 1.5.5 | - | (none) |

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
libcurl/[>=7.78 <9]
openssl/[>=1.1 <4]
zlib/[>=1.2.11 <2]
    |
    +-- google-cloud-cpp/2.28.0@milvus/dev --> abseil,
                                     nlohmann_json, crc32c,
                                     libcurl, openssl, zlib
```
Note: google-cloud-cpp/2.28.0@milvus/dev builds storage component only (REST, no grpc/protobuf).
Has no relationship with aws-c-common or the AWS C SDK chain.

### OpenTelemetry Chain
```
opentelemetry-proto/1.7.0
grpc/1.67.1@milvus/dev
abseil/20250127.0
protobuf/5.27.0@milvus/dev
nlohmann_json/3.11.2  (recipe-declared; Milvus forces 3.11.3)
openssl/1.1.1t        (recipe-declared; Milvus forces 3.3.2)
libcurl/7.86.0        (recipe-declared; Milvus forces 8.10.1)
    |
    +-- opentelemetry-cpp/1.23.0@milvus/dev --> opentelemetry-proto, grpc,
                                                 abseil, protobuf, nlohmann_json,
                                                 libcurl, openssl
```
Note: otel 1.23.0 removed Jaeger support (no more thrift/boost deps).
with_prometheus=False by default — prometheus-cpp is a direct Milvus dep, not through otel.

### AWS SDK Chain (0.12.5-based, declared in aws-sdk-cpp recipe)

The aws-sdk-cpp/1.11.692 recipe pins specific aws-c-* versions (0.12.5-based chain).
These are resolved from CCI at build time.

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
    +-- aws-sdk-cpp/1.11.692@milvus/dev --> all above + libcurl, openssl
```

### Folly Chain (recipe: recipes/folly/all/conanfile.py, version >= 2023.10.30.00)
```
boost/1.83.0 ---------> zlib, bzip2, libbacktrace/cci.20210118
double-conversion/3.3.0
gflags/2.2.2
glog/0.7.1 -----------> gflags, libunwind/1.8.1
libevent/2.1.12 ------> openssl, zlib
lz4/1.9.4
snappy/1.2.1
zstd/1.5.5
libsodium/cci.20220430
xz_utils/5.4.5
libunwind/1.8.1 ------> xz_utils, zlib
fmt/11.0.2
libdwarf/20191104 ----> libelf/0.8.13, zlib
libiberty/9.1.0 (Linux)
openssl/[>=3.0 <4]
zlib/[>=1.2.11 <2]
    |
    +-- folly/2024.08.12.00@milvus/dev --> boost, bzip2, double-conversion,
                                            glog, gflags, libevent, openssl,
                                            lz4, snappy, zstd, libdwarf,
                                            libsodium, libiberty, libunwind,
                                            xz_utils, zlib, fmt
```

### Arrow Chain (recipe: recipes/arrow/all/conanfile.py)

Arrow deps are conditional on options. With Milvus options (with_thrift, with_jemalloc,
with_boost, with_openssl, with_s3, with_azure, with_re2, with_zstd, encryption):

```
thrift/0.17.0         (with_thrift)
jemalloc/5.3.0        (with_jemalloc)
boost/1.85.0          (with_boost; recipe-declared, Milvus forces 1.83.0)
rapidjson/1.1.0       (encryption=True; recipe-declared, Milvus forces cci.20230929)
aws-sdk-cpp/1.11.692@milvus/dev  (with_s3)
azure-sdk-for-cpp/1.11.3@milvus/dev  (with_azure) --> libcurl, openssl, libxml2
xsimd/9.0.1           (simd_level/runtime_simd_level)
zstd/1.5.5            (with_zstd)
re2/20230301          (with_re2)
openssl/[>=1.1 <4]    (with_openssl)
    |
    +-- arrow/17.0.0@milvus/dev-2.6 --> thrift, jemalloc, boost, rapidjson,
                                          aws-sdk-cpp, azure-sdk-for-cpp,
                                          xsimd, zstd, re2, openssl
```
Note: lz4, snappy, zlib, bz2, protobuf, gflags, glog are NOT enabled (defaults False).
libcurl, libxml2 come transitively through aws-sdk-cpp and azure-sdk-for-cpp.

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
lz4/1.9.4            (always required)
zstd/1.5.5            (zstd=True)
cyrus-sasl/2.1.27 --- (sasl=True, Linux) --> openssl, zlib
openssl/[>=1.1 <4]    (ssl=True)
zlib/[>=1.2.11 <2]    (zlib=True, default)
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
| folly | 2024.08.12.00 | @milvus/dev | Milvus-compatible dep versions |
| google-cloud-cpp | 2.28.0 | @milvus/dev | Milvus-compatible dep versions (storage-only) |
| rocksdb | 6.29.5 | @milvus/dev | Custom build options for Milvus |
| libavrocpp | 1.12.1.1 | @milvus/dev | Custom recipe |
| aws-sdk-cpp | 1.11.692 | @milvus/dev | Custom build config |
| azure-sdk-for-cpp | 1.11.3 | @milvus/dev | Custom recipe |
| arrow | 17.0.0 | @milvus/dev-2.6 | Custom build with S3, Azure, encryption |

## Build Order (scripts/build-milvus-deps.sh)

### Phase 1: Foundation (no dependencies)
```
zlib/1.3.1
bzip2/1.0.8
lz4/1.9.4
snappy/1.2.1
zstd/1.5.5
gflags/2.2.2 (shared=True)
double-conversion/3.3.0 (shared=True)
crc32c/1.1.2
nlohmann_json/3.11.3
rapidjson/cci.20230929
xsimd/9.0.1
fmt/11.0.2
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
libevent/2.1.12 (shared=True)
libsodium/cci.20220430
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
azure-sdk-for-cpp/1.11.3@milvus/dev
```

### Phase 6: AWS SDK (Level 5-7)
```
aws-sdk-cpp/1.11.692@milvus/dev  (uses CCI 0.12.5 chain)
```

### Phase 7: Application Libraries
```
opentelemetry-cpp/1.23.0@milvus/dev
folly/2024.08.12.00@milvus/dev
google-cloud-cpp/2.28.0@milvus/dev
rocksdb/6.29.5@milvus/dev
libavrocpp/1.12.1.1@milvus/dev
```

### Phase 8: Final
```
arrow/17.0.0@milvus/dev-2.6
```

### Phase 9: Conancenter-only packages
```
simde/0.8.2
xxhash/0.8.3
unordered_dense/4.4.0
icu/74.2
```

## Packages with Multiple Versions

No packages require multiple versions in the current build.
aws-sdk-cpp/1.11.692 resolves its aws-c-* deps from CCI (0.12.5-based chain).

## ASCII Dependency Tree

Full dependency tree from Milvus's perspective. Each node shows `package/version[@user/channel]`.
Only runtime dependencies are shown (build tools in separate tree below).

Versions shown are from the local repo's recipes. Where recipes declare version ranges,
the resolved version depends on Milvus's force=True overrides.

```
Milvus conanfile.py
|
|-- (from requires tuple - no force)
|-- zstd/1.5.5 .................................................. (no deps)
|-- lz4/1.9.4 .................................................. (no deps)
|-- snappy/1.2.1 ................................................ (no deps)
|-- onetbb/2021.9.0 ............................................ hwloc/2.9.3
|-- libevent/2.1.12 ............................................ openssl, zlib
|-- googleapis/cci.20221108 .................................... protobuf
|-- gtest/1.13.0 ................................................ (no deps)
|-- benchmark/1.7.0 ............................................. (no deps)
|-- yaml-cpp/0.7.0 .............................................. (no deps)
|-- marisa/0.2.6 ................................................ (no deps)
|-- glog/0.7.1 .................................................. gflags, libunwind(Linux)
|-- gflags/2.2.2 ................................................ (no deps)
|-- double-conversion/3.3.0 ..................................... (no deps)
|-- libsodium/cci.20220430 ...................................... (no deps)
|-- xsimd/9.0.1 ................................................. (no deps)
|-- xz_utils/5.4.5 .............................................. (no deps)
|-- prometheus-cpp/1.2.4 ........................................ zlib (with_pull=False: no civetweb)
|-- re2/20230301 ................................................ (no deps)
|-- librdkafka/1.9.1 ............................................ lz4, zstd, cyrus-sasl, openssl, zlib
|-- roaring/3.0.0 ............................................... (no deps)
|-- simde/0.8.2 ................................................. (no deps)
|-- xxhash/0.8.3 ................................................ (no deps)
|-- unordered_dense/4.4.0 ....................................... (no deps)
|-- geos/3.12.0 ................................................. (no deps)
|-- icu/74.2 .................................................... (no deps)
|
|-- (from requirements() - with force=True overrides)
|-- boost/1.83.0 (force) ....................................... zlib, bzip2, libbacktrace
|-- openssl/3.3.2 (force) ...................................... zlib
|-- protobuf/5.27.0@milvus/dev (force) ........................ abseil, zlib
|-- grpc/1.67.1@milvus/dev (force) ............................ abseil, protobuf, c-ares, openssl,
|                                                               re2, zlib
|-- zlib/1.3.1 (force)
|-- libcurl/8.10.1 (force) ..................................... openssl, zlib
|-- nlohmann_json/3.11.3 (force) ............................... (no deps)
|-- abseil/20250127.0 (force) .................................. (no deps)
|-- fmt/11.0.2 (force)  ........................................ (no deps)
|-- rapidjson/cci.20230929 (force) ............................. (no deps)
|-- libunwind/1.8.1 (Linux) .................................... xz_utils, zlib
|-- s2n/1.6.0 (Linux) ......................................... openssl (overrides s2n/1.4.1 from aws-c-io)
|
|-- (from requires tuple - custom recipes)
|-- folly/2024.08.12.00@milvus/dev
|   +-- boost/1.83.0
|   |   +-- zlib, bzip2, libbacktrace
|   +-- bzip2/1.0.8
|   +-- double-conversion/3.3.0
|   +-- glog/0.7.1
|   |   +-- gflags, libunwind
|   +-- gflags/2.2.2
|   +-- libevent/2.1.12
|   |   +-- openssl, zlib
|   +-- openssl/[>=3.0 <4]
|   +-- lz4/1.9.4
|   +-- snappy/1.2.1
|   +-- zstd/1.5.5
|   +-- libdwarf/20191104
|   |   +-- libelf/0.8.13
|   |   +-- zlib
|   +-- libsodium/cci.20220430
|   +-- libiberty/9.1.0 (Linux)
|   +-- libunwind/1.8.1 (Linux)
|   +-- xz_utils/5.4.5
|   +-- zlib
|   +-- fmt/11.0.2
|
|-- google-cloud-cpp/2.28.0@milvus/dev (storage-only, REST)
|   +-- abseil/20250127.0
|   +-- nlohmann_json/3.11.3
|   +-- crc32c/1.1.2
|   +-- libcurl/[>=7.78 <9]
|   +-- openssl/[>=1.1 <4]
|   +-- zlib/[>=1.2.11 <2]
|
|-- opentelemetry-cpp/1.23.0@milvus/dev
|   +-- opentelemetry-proto/1.7.0
|   +-- grpc/1.67.1@milvus/dev
|   |   +-- abseil, protobuf, c-ares, openssl, re2, zlib
|   +-- abseil/20250127.0
|   +-- protobuf/5.27.0@milvus/dev
|   +-- nlohmann_json/3.11.2  (recipe-declared; overridden by Milvus force 3.11.3)
|   +-- openssl/1.1.1t        (recipe-declared; overridden by Milvus force 3.3.2)
|   +-- libcurl/7.86.0        (recipe-declared; overridden by Milvus force 8.10.1)
|   (with_prometheus=False by default — no prometheus-cpp)
|
|-- rocksdb/6.29.5@milvus/dev
|   +-- zstd/1.5.5  (only dep; other with_* default False)
|
|-- libavrocpp/1.12.1.1@milvus/dev
|   +-- boost/[>=1.81 <=1.89]
|   +-- snappy/[>=1.1.9 <2]
|   +-- fmt/[>=11 <13]
|   +-- zlib/[>=1.3.1 <2]
|
|-- (from requirements() - no force)
|-- aws-sdk-cpp/1.11.692@milvus/dev
|   +-- aws-crt-cpp/0.35.2 (recipe pins 0.12.5-based chain)
|   |   +-- aws-c-mqtt/0.13.3
|   |   |   +-- aws-c-http/0.10.5
|   |   |   |   +-- aws-c-compression/0.3.1
|   |   |   |   |   +-- aws-c-common/0.12.5
|   |   |   |   +-- aws-c-io/0.23.2
|   |   |   |       +-- aws-c-cal/0.9.8 --> aws-c-common, openssl
|   |   |   |       +-- aws-c-common/0.12.5
|   |   |   |       +-- s2n/1.6.0 --> openssl (Milvus overrides from 1.4.1)
|   |   +-- aws-c-event-stream/0.5.7
|   |   |   +-- aws-checksums/0.2.6 --> aws-c-common
|   |   |   +-- aws-c-io/0.23.2
|   |   +-- aws-c-s3/0.9.2
|   |   |   +-- aws-c-auth/0.9.1
|   |   |   |   +-- aws-c-http/0.10.5
|   |   |   |   +-- aws-c-sdkutils/0.2.4 --> aws-c-common
|   |   |   +-- aws-checksums/0.2.6
|   |   |   +-- aws-c-common/0.12.5
|   +-- libcurl/[>=7.78 <9]
|   +-- openssl/[>=1.1 <4]
|
+-- arrow/17.0.0@milvus/dev-2.6
    +-- thrift/0.17.0         (with_thrift)
    |   +-- boost/[>=1.78 <=1.85]
    |   +-- libevent/2.1.12
    |   +-- openssl/[>=1.1 <4]
    |   +-- zlib/[>=1.2.11 <2]
    +-- jemalloc/5.3.0        (with_jemalloc)
    +-- boost/1.85.0          (with_boost; Milvus forces 1.83.0)
    +-- rapidjson/1.1.0       (encryption=True; Milvus forces cci.20230929)
    +-- aws-sdk-cpp/1.11.692@milvus/dev  (with_s3)
    |   +-- (full aws-c-* 0.12.5 chain, see above)
    +-- azure-sdk-for-cpp/1.11.3@milvus/dev  (with_azure)
    |   +-- libcurl/[>=7.78 <9]
    |   +-- openssl/[>=1.1 <4]
    |   +-- libxml2/[>=2.12.5 <3]
    |       +-- libiconv/1.17
    |       +-- zlib
    +-- xsimd/9.0.1           (simd_level)
    +-- zstd/1.5.5            (with_zstd)
    +-- re2/20230301          (with_re2)
    +-- openssl/[>=1.1 <4]    (with_openssl)
    (NOT enabled: lz4, snappy, zlib, bz2, protobuf, gflags, glog)
```

## ASCII Build Tools Tree

Build-time dependencies used during compilation. These are `tool_requires` (not linked into final binaries).

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
cmake/3.31.11 ......... glog/0.7.1, folly/2024.08.12.00, googleapis/cci.20221108, libxml2/2.15.1, arrow/17.0.0
b2/5.4.2 .............. boost/1.83.0
```
