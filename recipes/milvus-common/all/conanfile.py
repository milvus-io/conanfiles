import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, cppstd_flag
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, replace_in_file
from conan.tools.gnu import PkgConfigDeps
from conan.tools.microsoft import is_msvc, msvc_runtime_flag
from conan.tools.system.package_manager import Brew


required_conan_version = ">=2.0"


class MilvusCommonConan(ConanFile):
    name = "milvus-common"
    license = "Apache-2.0"
    url = "https://github.com/zilliztech/milvus-common"
    homepage = "https://github.com/zilliztech/milvus-common"
    description = "Common C++ libraries for Milvus"
    package_type = "shared-library"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_ut": [True, False],
        "with_asan": [True, False],
    }
    default_options = {
        "folly/*:shared": True,
        "fmt/*:header_only": False,
        "gflags/*:shared": True,
        "glog/*:shared": True,
        "glog/*:with_gflags": True,
        "gtest/*:build_gmock": True,
        "openblas/*:use_openmp": True,
        "opentelemetry-cpp/*:with_stl": True,
        "openssl/*:shared": True,
        "openssl/*:no_apps": True,
        "prometheus-cpp/*:with_pull": False,
        "with_ut": False,
        "with_asan": False,
    }

    @property
    def _minimum_cpp_standard(self):
        return 20

    def validate(self):
        check_min_cppstd(self, self._minimum_cpp_standard)

    def system_requirements(self):
        if self.settings.os == "Macos":
            Brew(self).install(["libomp"])

    def build_requirements(self):
        if self.options.with_ut:
            self.test_requires("gtest/1.15.0")

    def requirements(self):
        self.requires("glog/0.7.1#a306e61d7b8311db8cb148ad62c48030", transitive_headers=True, transitive_libs=True)
        self.requires("fmt/11.2.0#eb98daa559c7c59d591f4720dde4cd5c", transitive_headers=True, transitive_libs=True, force=True)
        self.requires("prometheus-cpp/1.2.4#0918d66c13f97acb7809759f9de49b3f", transitive_headers=True, transitive_libs=True)
        self.requires("gflags/2.2.2#7671803f1dc19354cc90bd32874dcfda", transitive_headers=False, transitive_libs=False)
        self.requires("opentelemetry-cpp/1.23.0@milvus/dev#11bc565ec6e82910ae8f7471da756720", transitive_headers=True, transitive_libs=True)
        self.requires("folly/2026.04.20.00@milvus/dev#06852bea5b6449f0c4eb0df002b5779c", transitive_headers=True, transitive_libs=True)
        self.requires("grpc/1.67.1@milvus/dev#efeaa484b59bffaa579004d5e82ec4fd", transitive_headers=False, transitive_libs=False, override=True)
        self.requires("abseil/20250127.0#481edcc75deb0efb16500f511f0f0a1c", transitive_headers=False, transitive_libs=False, override=True)
        self.requires("xz_utils/5.4.5#fc4e36861e0a47ecd4a40a00e6d29ac8", transitive_headers=False, transitive_libs=False, override=True)
        self.requires("zlib/1.3.1#8045430172a5f8d56ba001b14561b4ea", transitive_headers=False, transitive_libs=False, override=True)
        self.requires("libevent/2.1.12#95065aaefcd58d3956d6dfbfc5631d97", transitive_headers=False, transitive_libs=False, override=True)
        self.requires("boost/1.83.0#4e8a94ac1b88312af95eded83cd81ca8", transitive_headers=True, transitive_libs=False)
        self.requires("protobuf/5.27.0@milvus/dev#42f031a96d21c230a6e05bcac4bdd633", transitive_headers=False, transitive_libs=False, force=True, override=True)
        self.requires("lz4/1.9.4#7f0b5851453198536c14354ee30ca9ae", transitive_headers=False, transitive_libs=False, force=True, override=True)
        self.requires("openssl/3.3.2#9f9f130d58e7c13e76bb8a559f0a6a8b", transitive_headers=False, transitive_libs=False, force=True, override=True)
        self.requires("libcurl/8.10.1#a3113369c86086b0e84231844e7ed0a9", transitive_headers=False, transitive_libs=False, force=True, override=True)
        self.requires("nlohmann_json/3.11.3#ffb9e9236619f1c883e36662f944345d", transitive_headers=False, transitive_libs=False, force=True)
        if self.settings.os != "Macos":
            self.requires("libunwind/1.8.1#748a981ace010b80163a08867b732e71", transitive_headers=False, transitive_libs=False, override=True)
        if self.settings.os == "Linux":
            self.requires("openblas/0.3.30", transitive_headers=True, transitive_libs=False)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generator = "Unix Makefiles"
        tc.variables["CMAKE_POSITION_INDEPENDENT_CODE"] = True
        tc.cache_variables["CMAKE_INSTALL_LIBDIR"] = "lib"
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5"

        cxx_std_flag = cppstd_flag(self)
        cxx_std_value = cxx_std_flag.split("=")[1] if cxx_std_flag else f"c++{self._minimum_cpp_standard}"
        tc.variables["CXX_STD"] = cxx_std_value
        if is_msvc(self):
            tc.variables["MSVC_LANGUAGE_VERSION"] = cxx_std_value
            tc.variables["MSVC_ENABLE_ALL_WARNINGS"] = False
            tc.variables["MSVC_USE_STATIC_RUNTIME"] = "MT" in msvc_runtime_flag(self)

        tc.variables["WITH_COMMON_UT"] = self.options.with_ut
        tc.variables["WITH_ASAN"] = self.options.with_asan
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("folly", "cmake_file_name", "folly")
        deps.set_property("gflags", "cmake_file_name", "gflags")
        deps.set_property("glog", "cmake_file_name", "glog")
        deps.set_property("fmt", "cmake_file_name", "fmt")
        deps.set_property("prometheus-cpp", "cmake_file_name", "prometheus-cpp")
        deps.set_property("nlohmann_json", "cmake_file_name", "nlohmann_json")
        deps.set_property("openblas", "cmake_file_name", "OpenBLAS")
        deps.generate()

        pc = PkgConfigDeps(self)
        pc.generate()

    def _patch_sources(self):
        cmakelists = os.path.join(self.source_folder, "CMakeLists.txt")
        replace_in_file(self, cmakelists, "find_package(prometheus-cpp REQUIRED)\n", "find_package(prometheus-cpp REQUIRED)\nfind_package(nlohmann_json REQUIRED CONFIG)\n")
        replace_in_file(self, cmakelists, "list(APPEND COMMON_LINKER_LIBS prometheus-cpp::core prometheus-cpp::push)\n", "list(APPEND COMMON_LINKER_LIBS prometheus-cpp::core prometheus-cpp::push)\nlist(APPEND COMMON_LINKER_LIBS nlohmann_json::nlohmann_json)\n")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.generator = "Unix Makefiles"
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.generator = "Unix Makefiles"
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "milvus-common")
        self.cpp_info.set_property("cmake_target_name", "milvus-common::milvus-common")
        self.cpp_info.libs = ["milvus-common"]
        self.cpp_info.defines = ["OPENTELEMETRY_STL_VERSION=2017"]
        self.cpp_info.requires = [
            "boost::headers",
            "opentelemetry-cpp::opentelemetry_trace",
            "opentelemetry-cpp::opentelemetry_exporter_ostream_span",
            "opentelemetry-cpp::opentelemetry_exporter_otlp_http",
            "folly::folly",
            "gflags::gflags",
            "glog::glog",
            "fmt::fmt",
            "nlohmann_json::nlohmann_json",
            "prometheus-cpp::prometheus-cpp-core",
            "prometheus-cpp::prometheus-cpp-push",
        ]
        if self.dependencies["opentelemetry-cpp"].options.get_safe("with_otlp_grpc"):
            self.cpp_info.requires.append("opentelemetry-cpp::opentelemetry_exporter_otlp_grpc")
            self.cpp_info.defines.append("HAVE_OTLP_GRPC_EXPORTER")
        if self.settings.os == "Linux":
            self.cpp_info.requires.append("openblas::openblas")
            self.cpp_info.system_libs.extend(["pthread", "dl"])
            if self.settings.compiler == "gcc":
                self.cpp_info.system_libs.extend(["gomp", "atomic"])
            elif self.settings.compiler == "clang":
                self.cpp_info.system_libs.append("omp")
        elif self.settings.os == "Macos":
            self.cpp_info.defines.append("BOOST_STACKTRACE_GNU_SOURCE_NOT_REQUIRED")
