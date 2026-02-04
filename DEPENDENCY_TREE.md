# Dependency Tree for Conanfiles Repository

This document shows the dependency relationships between packages in this repository.

## Legend
- `→` depends on
- Packages in **bold** are in this repository
- Packages in (parentheses) are external dependencies from conancenter

## Level 0 - No Dependencies (Leaf Packages)

These packages have no dependencies on other packages:

```
zlib
bzip2
lz4
snappy
zstd (optional: zlib)
gflags
gtest
double-conversion
crc32c
rapidjson
rapidxml
nlohmann_json
roaring
marisa
geos
xsimd
fmt
yaml-cpp
ninja
gnu-config
m4
sqlite3
lzo
json-c
libspatialindex
openblas
simdjson
aws-c-common
opentelemetry-proto
```

## Level 1 - Single-Level Dependencies

```
xz_utils → (msys2)
openssl → zlib, (nasm, perl)
c-ares → (none)
re2 → (abseil - newer versions), (icu - optional)
protobuf → zlib
libunwind → xz_utils, zlib
libelf → (autoconf), gnu-config
libiberty → (msys2)
libevent → openssl
flex → m4
autoconf → m4
bison → m4, (automake, flex)
meson → ninja
libsodium → (libtool)
benchmark → (cmake, libpfm4)
s2n → openssl
glog → gflags, (libunwind - optional)
```

## Level 2 - Two-Level Dependencies

```
automake → autoconf → m4

libtool → automake → autoconf → m4

pkgconf → meson → ninja

boost → zlib, bzip2, xz_utils, zstd, (libbacktrace), (icu), (libiconv), (b2)

libdwarf → libelf, zlib

aws-checksums → aws-c-common
aws-c-cal → aws-c-common, openssl
aws-c-compression → aws-c-common
aws-c-sdkutils → aws-c-common

prometheus-cpp → zlib, (civetweb), (libcurl)
```

## Level 3 - Three-Level Dependencies

```
aws-c-io → aws-c-common, aws-c-cal, (s2n)
         ↓
         aws-c-common, openssl

libcurl → openssl, zlib, (zstd), c-ares, (libtool), (pkgconf)

libtiff → zlib, xz_utils, (zstd), (libjpeg)

libgeotiff → libtiff, proj
           ↓
           proj → nlohmann_json, sqlite3, (libtiff), (libcurl)
```

## Level 4+ - Complex Dependencies

### AWS SDK Chain
```
aws-c-common (L0)
    ↓
aws-checksums (L1)
aws-c-cal (L1) → openssl
aws-c-compression (L1)
aws-c-sdkutils (L1)
    ↓
aws-c-io (L2) → aws-c-cal
    ↓
aws-c-http (L3) → aws-c-io, aws-c-compression
    ↓
aws-c-auth (L4) → aws-c-http, aws-c-io, aws-c-cal, aws-c-sdkutils
aws-c-mqtt (L4) → aws-c-http, aws-c-io, aws-c-cal
    ↓
aws-c-event-stream (L5) → aws-c-io, aws-checksums
aws-c-s3 (L5) → aws-c-auth, aws-c-http, aws-c-io, aws-checksums
    ↓
aws-crt-cpp (L6) → aws-c-auth, aws-c-s3, aws-c-mqtt, aws-c-event-stream, ...
    ↓
aws-sdk-cpp (L7) → aws-crt-cpp, aws-c-common, aws-c-event-stream, libcurl, openssl
```

### gRPC Chain
```
zlib (L0)
protobuf (L1) → zlib
c-ares (L0)
openssl (L1) → zlib
re2 (L1)
abseil (L0)
    ↓
grpc (L2) → protobuf, c-ares, openssl, re2, zlib, abseil
```

### Google Cloud Chain
```
grpc (L2)
protobuf (L1)
abseil (L0)
nlohmann_json (L0)
crc32c (L0)
libcurl (L3)
openssl (L1)
zlib (L0)
googleapis (L2) → protobuf
    ↓
google-cloud-cpp (L3) → grpc, protobuf, abseil, nlohmann_json, crc32c,
                        libcurl, openssl, zlib, googleapis
```

### OpenTelemetry Chain
```
abseil (L0)
protobuf (L1)
opentelemetry-proto (L0)
grpc (L2)
nlohmann_json (L0)
openssl (L1)
libcurl (L3)
prometheus-cpp (L2)
thrift (L3) → boost, openssl, zlib, libevent, (flex, bison)
    ↓
opentelemetry-cpp (L4) → abseil, protobuf, opentelemetry-proto, grpc,
                          nlohmann_json, openssl, libcurl, prometheus-cpp, thrift
```

### Folly Chain
```
boost (L2)
bzip2 (L0)
double-conversion (L0)
gflags (L0)
glog (L1)
libevent (L1)
openssl (L1)
lz4 (L0)
snappy (L0)
zlib (L0)
zstd (L0)
libsodium (L1)
xz_utils (L1)
libunwind (L1)
fmt (L0)
libdwarf (L2)
libiberty (L1)
    ↓
folly (L3) → boost, bzip2, double-conversion, gflags, glog, libevent,
             openssl, lz4, snappy, zlib, zstd, libsodium, xz_utils,
             libunwind, fmt, libdwarf, libiberty
```

### Arrow Chain
```
thrift (L3)
protobuf (L1)
jemalloc (L1)
boost (L2)
gflags (L0)
glog (L1)
grpc (L2)
rapidjson (L0)
openssl (L1)
opentelemetry-cpp (L4)
aws-sdk-cpp (L7)
bzip2 (L0)
lz4 (L0)
snappy (L0)
xsimd (L0)
zstd (L0)
re2 (L1)
    ↓
arrow (L8) → thrift, protobuf, jemalloc, boost, gflags, glog, grpc,
             rapidjson, openssl, opentelemetry-cpp, aws-sdk-cpp,
             bzip2, lz4, snappy, xsimd, zstd, re2
```

### RocksDB Chain
```
gflags (L0)
snappy (L0)
lz4 (L0)
zlib (L0)
zstd (L0)
onetbb (L1)
jemalloc (L1)
    ↓
rocksdb (L2) → gflags, snappy, lz4, zlib, zstd, onetbb, jemalloc
```

### libavrocpp Chain
```
boost (L2)
snappy (L0)
fmt (L0)
zlib (L0)
    ↓
libavrocpp (L3) → boost, snappy, fmt, zlib
```

## Build Order for Milvus Dependencies

Recommended build order (dependencies first):

### Phase 1: Foundation (No deps)
```
zlib, bzip2, lz4, snappy, zstd, gflags, double-conversion,
rapidjson, nlohmann_json, roaring, marisa, geos, xsimd, fmt,
yaml-cpp, ninja, m4, gtest, sqlite3, aws-c-common,
opentelemetry-proto, crc32c
```

### Phase 2: Basic Dependencies
```
xz_utils, openssl, c-ares, protobuf, libunwind, libevent,
flex, autoconf, re2, abseil, glog, aws-checksums, aws-c-cal,
aws-c-compression, aws-c-sdkutils, benchmark
```

### Phase 3: Intermediate
```
automake, libtool, meson, pkgconf, boost, libdwarf, aws-c-io,
prometheus-cpp, googleapis, onetbb, jemalloc
```

### Phase 4: Complex Libraries
```
bison, libcurl, aws-c-http, grpc, librdkafka
```

### Phase 5: High-Level Libraries
```
aws-c-auth, aws-c-mqtt, aws-c-event-stream, aws-c-s3,
thrift, google-cloud-cpp
```

### Phase 6: AWS SDK
```
aws-crt-cpp, aws-sdk-cpp
```

### Phase 7: Application Libraries
```
opentelemetry-cpp, folly, rocksdb, libavrocpp
```

### Phase 8: Final
```
arrow
```

## External Dependencies (Not in this repo)

These packages are required but will be fetched from conancenter:
- simde
- xxhash
- unordered_dense
- icu
- libiconv
- libbacktrace
- b2
- msys2
- nasm
- perl/strawberryperl
- libjpeg/libjpeg-turbo
- libxml2
- and other optional dependencies
