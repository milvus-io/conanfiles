import os, sys

def system(command):
    retcode = os.system(command)
    if retcode != 0:
        raise Exception("Error while executing:\n\t %s" % command)

if __name__ == "__main__":
    system("conan export abseil/all abseil/20230125.3@")
    system("conan export arrow/all arrow/15.0.0@")
    system("conan export autoconf/all autoconf/2.71@")
    system("conan export automake/all automake/1.16.5@")
    system("conan export aws-c-auth/all aws-c-auth/0.6.11@")
    system("conan export aws-c-cal/all aws-c-cal/0.5.13@")
    system("conan export aws-c-common/all aws-c-common/0.8.2@")
    system("conan export aws-c-compression/all aws-c-compression/0.2.15@")
    system("conan export aws-c-event-stream/all aws-c-event-stream/0.2.7@")
    system("conan export aws-c-http/all aws-c-http/0.6.13@")
    system("conan export aws-c-io/all aws-c-io/0.10.20@")
    system("conan export aws-c-mqtt/all aws-c-mqtt/0.7.10@")
    system("conan export aws-c-s3/all aws-c-s3/0.1.37@")
    system("conan export aws-c-sdkutils/all aws-c-sdkutils/0.1.3@")
    system("conan export aws-checksums/all aws-checksums/0.1.13@")
    system("conan export aws-crt-cpp/all aws-crt-cpp/0.17.23@")
    system("conan export aws-sdk-cpp/all aws-sdk-cpp/1.9.234@")
    system("conan export benchmark/all benchmark/1.7.0@")
    system("conan export bison/all bison/3.8.2@")
    system("conan export boost/all boost/1.82.0@")
    system("conan export bzip2/all bzip2/1.0.8@")
    system("conan export c-ares/all c-ares/1.32.1@")
    system("conan export crc32c/all crc32c/1.1.1@")
    system("conan export cyrus-sasl/all cyrus-sasl/2.1.27@")
    system("conan export cyrus-sasl/all cyrus-sasl/2.1.28@")
    system("conan export double-conversion/all double-conversion/3.2.1@")
    system("conan export flex/all flex/2.6.4@")
    system("conan export fmt/all fmt/9.1.0@")
    system("conan export gflags/all gflags/2.2.2@")
    system("conan export glog/all glog/0.6.0@")
    system("conan export gnu-config/all gnu-config/cci.20210814@")
    system("conan export google-cloud-cpp/2.x google-cloud-cpp/2.5.0@")
    system("conan export googleapis/all googleapis/cci.20221108@")
    system("conan export grpc/all grpc/1.50.1@")
    system("conan export grpc/all grpc/1.54.3@")
    system("conan export gtest/all gtest/1.8.1@")
    system("conan export gtest/all gtest/1.13.0@")
    system("conan export hwloc/all hwloc/2.9.3@")
    system("conan export jemalloc/all jemalloc/5.3.0@")
    system("conan export libbacktrace/all libbacktrace/cci.20210118@")
    system("conan export libcurl/all libcurl/7.86.0@")
    system("conan export libdwarf/all libdwarf/20191104@")
    system("conan export libelf/all libelf/0.8.13@")
    system("conan export libevent/all libevent/2.1.12@")
    system("conan export libiberty/all libiberty/9.1.0@")
    system("conan export libiconv/all libiconv/1.17@")
    system("conan export librdkafka/all librdkafka/1.9.1@")
    system("conan export libsodium/all libsodium/cci.20220430@")
    system("conan export libtool/all libtool/2.4.7@")
    system("conan export libunwind/all libunwind/1.7.2@")
    system("conan export lz4/all lz4/1.9.4@")
    system("conan export lzo/all lzo/2.10@")
    system("conan export m4/all m4/1.4.19@")
    system("conan export marisa/all marisa/0.2.6@")
    system("conan export meson/all meson/1.2.2@")
    system("conan export ninja/all ninja/1.11.1@")
    system("conan export nlohmann_json/all nlohmann_json/3.11.2@")
    system("conan export onetbb/all onetbb/2021.7.0@")
    system("conan export onetbb/all onetbb/2021.9.0@")
    system("conan export opentelemetry-proto/all opentelemetry-proto/0.19.0@")
    system("conan export pkgconf/all pkgconf/1.9.3@")
    system("conan export pkgconf/all pkgconf/2.1.0@")
    system("conan export prometheus-cpp/all prometheus-cpp/1.1.0@")
    system("conan export protobuf/all protobuf/3.21.4@")
    system("conan export rapidxml/all rapidxml/1.13@")
    system("conan export re2/all re2/20230301@")
    system("conan export roaring/all roaring/3.0.0@")
    system("conan export s2n/all s2n/1.3.55@")
    system("conan export snappy/all snappy/1.1.9@")
    system("conan export thrift/all thrift/0.17.0@")
    system("conan export xsimd/all xsimd/9.0.1@")
    system("conan export xz_utils/all xz_utils/5.4.0@")
    system("conan export yaml-cpp/all yaml-cpp/0.7.0@")
    system("conan export zlib/all zlib/1.2.13@")
    system("conan export zstd/all zstd/1.5.4@")
    system("conan export b2/portable b2/5.2.1@")
    system("conan export cmake/binary cmake/3.30.0@")
    system("conan export openssl/3.x.x openssl/3.1.2@")

    system("conan upload '*' -r artifactory --all -c")
