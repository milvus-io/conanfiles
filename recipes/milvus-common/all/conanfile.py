import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, cppstd_flag
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, replace_in_file
from conan.tools.gnu import PkgConfigDeps
from conan.tools.microsoft import is_msvc, msvc_runtime_flag


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
        "prometheus-cpp/*:with_pull": False,
        "with_ut": False,
        "with_asan": False,
    }

    @property
    def _minimum_cpp_standard(self):
        return 17

    def validate(self):
        check_min_cppstd(self, self._minimum_cpp_standard)

    def requirements(self):
        if self.options.with_ut:
            self.requires("gtest/1.15.0", visible=False)
        self.requires("glog/0.7.1", transitive_headers=True, transitive_libs=True)
        self.requires("fmt/11.0.2", transitive_headers=True, transitive_libs=True)
        self.requires("prometheus-cpp/1.2.4", transitive_headers=True, transitive_libs=True)
        self.requires("gflags/2.2.2", transitive_headers=True, transitive_libs=True)
        self.requires("opentelemetry-cpp/1.23.0@milvus/dev", transitive_headers=True, transitive_libs=True)
        self.requires("folly/2024.08.12.00@milvus/dev", transitive_headers=True, transitive_libs=True)
        self.requires("protobuf/5.27.0@milvus/dev", override=True)
        self.requires("lz4/1.9.4", override=True)
        self.requires("openssl/3.3.2", override=True)
        self.requires("libcurl/8.10.1", override=True)
        self.requires("nlohmann_json/3.11.3", force=True)
        if self.settings.os != "Macos":
            self.requires("openblas/0.3.27", transitive_headers=True, transitive_libs=True)

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
        if self.dependencies["opentelemetry-cpp"].options.with_otlp_grpc:
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
