from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import is_msvc, msvc_runtime_flag
from conan.tools.build import check_min_cppstd
from conan.tools.scm import Version
from conan.tools.files import get, copy, rmdir, apply_conandata_patches, export_conandata_patches
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
import os

required_conan_version = ">=2.0"


class VeloxConan(ConanFile):
    name = "velox"
    description = ""
    topics = ("facebook", "engine", "simd")
    url = "https://github.com/facebookincubator/velox"
    homepage = "https://github.com/facebookincubator/velox"
    license = "Apache-2.0"
    package_type = "library"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {"shared": False, "fPIC": True}

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    @property
    def _minimum_cpp_standard(self):
        return 17

    @property
    def _minimum_compilers_version(self):
        return {
            "gcc": "8",
            "msvc": "192",
            "clang": "6",
            "apple-clang": "10",
        }

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("folly/2023.02.24milvus/dev")
        self.requires("boost/1.81.0")
        self.requires("bzip2/1.0.8")
        self.requires("double-conversion/3.2.1")
        self.requires("xsimd/9.0.1")
        self.requires("gtest/1.8.1")
        self.requires("gflags/2.2.2")
        self.requires("glog/0.6.0")
        self.requires("libevent/2.1.12")
        self.requires("lz4/1.9.4")
        self.requires("lzo/2.10")
        self.requires("snappy/1.1.9")
        self.requires("zlib/1.2.13")
        self.requires("zstd/1.5.2")
        self.requires("re2/20220601")
        self.requires("libsodium/cci.20220430")
        self.requires("openssl/1.1.1q")
        self.requires("xz_utils/5.2.5")
        self.requires("protobuf/3.21.9")
        self.requires("flex/2.6.4")

    def build_requirements(self):
        self.tool_requires("m4/1.4.19")
        self.tool_requires("bison/3.5.3")
        self.tool_requires("flex/2.6.4")

    @property
    def _required_boost_components(self):
        return ["context", "filesystem", "program_options", "regex", "system", "thread"]

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)
        min_version = self._minimum_compilers_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warning(
                "{} recipe lacks information about the {} compiler support.".format(
                    self.name, self.settings.compiler
                )
            )
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    "{} requires C++{} support. The current compiler {} {} does not support it.".format(
                        self.name,
                        self._minimum_cpp_standard,
                        self.settings.compiler,
                        self.settings.compiler.version,
                    )
                )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
        # Relocatable shared lib on Macos
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        # Honor BUILD_SHARED_LIBS from conan_toolchain (see https://github.com/conan-io/conan/issues/11840)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"

        # Determine C++ standard
        cppstd = self.settings.get_safe("compiler.cppstd")
        if cppstd:
            cxx_std_value = "c++{}".format(str(cppstd).replace("gnu", ""))
        else:
            cxx_std_value = "c++{}".format(self._minimum_cpp_standard)
        tc.variables["CXX_STD"] = cxx_std_value

        if is_msvc(self):
            tc.variables["MSVC_LANGUAGE_VERSION"] = cxx_std_value
            tc.variables["MSVC_ENABLE_ALL_WARNINGS"] = False
            tc.variables["MSVC_USE_STATIC_RUNTIME"] = "MT" in msvc_runtime_flag(self)
        tc.variables["VELOX_BUILD_TESTING"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "velox")
        self.cpp_info.set_property("cmake_target_name", "Velox::velox_bundled")
        self.cpp_info.set_property("pkg_config_name", "libvelox")

        self.cpp_info.components["libvelox"].libs = [
            "velox_bundled",
            "velox_test_bundled",
        ]

        self.cpp_info.components["libvelox"].requires = [
            "boost::context",
            "boost::filesystem",
            "boost::program_options",
            "boost::regex",
            "boost::system",
            "boost::thread",
            "bzip2::bzip2",
            "double-conversion::double-conversion",
            "gflags::gflags",
            "glog::glog",
            "libevent::libevent",
            "lz4::lz4",
            "lzo::lzo",
            "snappy::snappy",
            "zlib::zlib",
            "zstd::zstd",
            "re2::re2",
            "libsodium::libsodium",
            "openssl::openssl",
            "xz_utils::xz_utils",
            "xsimd::xsimd",
            "gtest::gtest",
            "folly::folly",
        ]
        if (
            self.settings.os == "Linux"
            and self.settings.compiler == "clang"
            and self.settings.compiler.libcxx == "libstdc++"
        ):
            self.cpp_info.components["libvelox"].system_libs.append("atomic")

        if (
            self.settings.os == "Macos"
            and self.settings.compiler == "apple-clang"
            and Version(self.settings.compiler.version.value) >= "11.0"
        ) or (
            self.settings.os == "Macos"
            and self.settings.compiler == "clang"
            and Version(self.settings.compiler.version.value) >= "11.0"
        ):
            self.cpp_info.components["libvelox"].system_libs.append("c++abi")

        self.cpp_info.components["libvelox"].set_property("cmake_target_name", "Velox::velox")
        self.cpp_info.components["libvelox"].set_property("pkg_config_name", "libvelox")
