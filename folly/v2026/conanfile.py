from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.env import VirtualBuildEnv
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import get, copy, rmdir, replace_in_file, save, rm
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version
import os


# Dual-targetable recipe: works on both Conan v1 (>=1.54.0) and Conan v2.
# All body code uses `conan.tools.*` idioms that both runtimes implement.
required_conan_version = ">=1.54.0"


class FollyConan(ConanFile):
    name = "folly"
    version = "2026.04.20.00"
    description = "An open-source C++ components library developed and used at Facebook"
    topics = ("facebook", "components", "core", "efficiency")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/facebook/folly"
    license = "Apache-2.0"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "fmt:header_only": False,
    }

    @property
    def _min_cppstd(self):
        return 20

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "10",
            "clang": "10",
            "apple-clang": "14",
            "msvc": "192",
            "Visual Studio": "16",
        }

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if is_msvc(self):
            self.package_type = "static-library"
            del self.options.shared

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.83.0", transitive_headers=True, transitive_libs=True)
        self.requires("bzip2/1.0.8")
        self.requires("double-conversion/3.3.0", transitive_headers=True, transitive_libs=True)
        self.requires("fast_float/8.0.0@milvus/dev", transitive_headers=True)
        self.requires("gflags/2.2.2")
        self.requires("glog/0.7.1", transitive_headers=True, transitive_libs=True)
        self.requires("libevent/2.1.12", transitive_headers=True, transitive_libs=True)
        self.requires("openssl/[>=1.1 <4]")
        self.requires("lz4/1.10.0", transitive_libs=True)
        self.requires("snappy/1.2.1")
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("zstd/1.5.5", transitive_libs=True)
        if not is_msvc(self):
            self.requires("libdwarf/0.9.1")
        self.requires("libsodium/1.0.19")
        self.requires("xz_utils/[>=5.4.5 <6]")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.requires("libiberty/9.1.0")
            # Aligned with knowhere's own libunwind/1.8.1 pin to avoid
            # Conan v2 "Version conflict" at install time.
            self.requires("libunwind/1.8.1")
        # liburing removed: liburing 2.6 compat.h redefines __kernel_timespec
        # conflicting with newer kernel headers on ubuntu-latest runners.
        # Folly io_uring support is optional.
        # INFO: Folly does not support fmt 11 on MSVC: https://github.com/facebook/folly/issues/2250
        self.requires("fmt/10.2.1", transitive_headers=True, transitive_libs=True)

    def build_requirements(self):
        # INFO: Required due ZIP_LISTS CMake feature in conan_deps.cmake
        self.tool_requires("cmake/[>=3.17 <4]")

    @property
    def _required_boost_components(self):
        # In 2026.04.20.00, Boost components are: context, filesystem, program_options, regex
        # (thread only needed on Windows for pthread compatibility layer)
        return ["context", "filesystem", "program_options", "regex"]

    @property
    def _required_boost_conan_components(self):
        return [f"boost::{comp}" for comp in self._required_boost_components]

    @property
    def _required_boost_cmake_targets(self):
        return [f"Boost::{comp}" for comp in self._required_boost_components]

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support.")

        if self.settings.os == "Windows" and self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration(f"{self.ref} Folly requires a 64bit target architecture on Windows.")

        if self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version) < "14.0":
            raise ConanInvalidConfiguration(f"{self.ref} could not be built by apple-clang < 14.0. Use apple-clang >= 14.0")

        boost = self.dependencies["boost"]
        if boost.options.header_only:
            raise ConanInvalidConfiguration(f"{self.ref} could not be built with a header only Boost. Use -o 'boost/*:header_only=False'")

        miss_boost_required_comp = any(getattr(boost.options, f"without_{boost_comp}", True) for boost_comp in self._required_boost_components)
        if miss_boost_required_comp:
            required_components = ", ".join(self._required_boost_components)
            raise ConanInvalidConfiguration(f"{self.ref} requires these Boost components: {required_components}. Try with '-o boost/*:without_{required_components}=False'")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=False)

    def _cppstd_flag_value(self, cppstd):
        if is_msvc(self):
            prefix = "c"
            year = str(cppstd)
            if year > "17":
                year = "latest"
        return f"{prefix}++{year}"

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_PROJECT_folly_INCLUDE"] = "conan_deps.cmake"
        # Folly fails to check Gflags: https://github.com/conan-io/conan/issues/12012
        tc.variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)

        if is_apple_os(self) and cross_building(self):
            for var in ["FOLLY_HAVE_UNALIGNED_ACCESS", "FOLLY_HAVE_LINUX_VDSO", "FOLLY_HAVE_WCHAR_SUPPORT", "HAVE_VSNPRINTF_ERRORS"]:
                tc.cache_variables[f"{var}_EXITCODE"] = 0

        # Folly is not respecting this from the helper https://github.com/conan-io/conan-center-index/pull/15726/files#r1097068754
        tc.cache_variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
        # Relocatable shared lib on Macos
        if is_apple_os(self):
            tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        # Honor BUILD_SHARED_LIBS from conan_toolchain (see https://github.com/conan-io/conan/issues/11840)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        # Honor Boost_ROOT set by boost recipe
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0074"] = "NEW"

        # Enable SSE4.2 on x86/x86_64 so that __SSE4_2__ is defined and Folly
        # compiles F14 hash maps in SimdAndCrc mode. Without this flag, Folly
        # uses Simd-only mode, but consumers that inherit -msse4.2 (e.g. from
        # knowhere) will expect SimdAndCrc mode, causing a linker mismatch on
        # F14 template instantiations.
        if str(self.settings.arch) in ["x86_64", "x86"] and not is_msvc(self):
            tc.variables["CMAKE_C_FLAGS"] = "-msse4.2"
            tc.variables["CMAKE_CXX_FLAGS"] = "-msse4.2"

        if is_msvc(self):
            cxx_std_value = self._cppstd_flag_value(self.settings.get_safe("compiler.cppstd", self._min_cppstd))
            tc.cache_variables["MSVC_LANGUAGE_VERSION"] = cxx_std_value
            tc.cache_variables["MSVC_ENABLE_ALL_WARNINGS"] = False
            tc.cache_variables["MSVC_USE_STATIC_RUNTIME"] = is_msvc_static_runtime(self)
            tc.preprocessor_definitions["NOMINMAX"] = ""

        if not self.dependencies["boost"].options.header_only:
            tc.cache_variables["BOOST_LINK_STATIC"] = not self.dependencies["boost"].options.shared

        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0074"] = "NEW"  # Honor Boost_ROOT set by boost recipe
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("boost", "cmake_file_name", "Boost")
        deps.set_property("bzip2", "cmake_file_name", "BZip2")
        deps.set_property("double-conversion", "cmake_file_name", "DoubleConversion")
        deps.set_property("fast_float", "cmake_file_name", "FastFloat")
        deps.set_property("fmt", "cmake_file_name", "fmt")
        deps.set_property("gflags", "cmake_file_name", "Gflags")
        deps.set_property("glog", "cmake_file_name", "Glog")
        deps.set_property("libdwarf", "cmake_file_name", "LibDwarf")
        deps.set_property("libevent", "cmake_file_name", "LibEvent")
        deps.set_property("libiberty", "cmake_file_name", "Libiberty")
        deps.set_property("libsodium", "cmake_file_name", "Libsodium")
        deps.set_property("libunwind", "cmake_file_name", "LibUnwind")
        # liburing removed due to kernel header conflict
        deps.set_property("lz4", "cmake_file_name", "LZ4")
        deps.set_property("openssl", "cmake_file_name", "OpenSSL")
        deps.set_property("snappy", "cmake_file_name", "Snappy")
        deps.set_property("xz_utils", "cmake_file_name", "LibLZMA")
        deps.set_property("zlib", "cmake_file_name", "ZLIB")
        deps.set_property("zstd", "cmake_file_name", "Zstd")
        deps.generate()

    def _patch_sources(self):
        # Make sure will consume Conan dependencies
        folly_deps = os.path.join(self.source_folder, "CMake", "folly-deps.cmake")
        replace_in_file(self, folly_deps, " MODULE", " REQUIRED CONFIG")
        # In 2026.04.20.00, Boost is linked per-target, no ${Boost_LIBRARIES} global substitution needed
        replace_in_file(self, folly_deps, "OpenSSL 1.1.1", "OpenSSL")
        # Disable example
        save(self, os.path.join(self.source_folder, "folly", "logging", "example", "CMakeLists.txt"), "")
        # Disable custom find modules to use Conan CMakeDeps instead
        rm(self, "Find*.cmake", os.path.join(self.source_folder, "CMake"))
        rm(self, "Find*.cmake", os.path.join(self.source_folder, "build", "fbcode_builder", "CMake"))
        # Skip generating .pc file to avoid Windows errors when trying to compile with pkg-config
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"), "gen_pkgconfig_vars(FOLLY_PKGCONFIG folly_deps)", "")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "folly")
        self.cpp_info.set_property("cmake_target_name", "folly::folly")
        self.cpp_info.set_property("pkg_config_name", "libfolly")

        self.cpp_info.components["libfolly"].set_property("cmake_target_name", "Folly::folly")
        self.cpp_info.components["libfolly"].set_property("pkg_config_name", "libfolly")
        self.cpp_info.components["libfolly"].libs = ["folly"]
        self.cpp_info.components["libfolly"].requires = ["fmt::fmt", "fast_float::fast_float"] + self._required_boost_conan_components + [
            "double-conversion::double-conversion",
            "gflags::gflags",
            "glog::glog",
            "libevent::libevent",
            "lz4::lz4",
            "openssl::openssl",
            "bzip2::bzip2",
            "snappy::snappy",
            "zlib::zlib",
            "zstd::zstd",
            "libsodium::libsodium",
            "xz_utils::xz_utils",
        ]
        if not is_msvc(self):
            self.cpp_info.components["libfolly"].requires.append("libdwarf::libdwarf")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["libfolly"].requires.extend(["libiberty::libiberty", "libunwind::libunwind"])
        if self.settings.os == "Linux":
            self.cpp_info.components["libfolly"].system_libs.extend(["pthread", "dl", "rt"])
            self.cpp_info.components["libfolly"].defines.extend(["FOLLY_HAVE_ELF", "FOLLY_HAVE_DWARF"])
        elif self.settings.os == "Windows":
            self.cpp_info.components["libfolly"].system_libs.extend(["ws2_32", "iphlpapi", "crypt32"])

        # Propagate FOLLY_SSE defines so consumers compile F14 in the same
        # SimdAndCrc mode that this library was built with.
        if str(self.settings.arch) in ["x86_64", "x86"]:
            self.cpp_info.components["libfolly"].defines.extend(["FOLLY_SSE=4", "FOLLY_SSE_MINOR=2"])

        if  self.settings.get_safe("compiler.libcxx") == "libstdc++" or \
            (self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version.value) == "9.0" and \
              self.settings.get_safe("compiler.libcxx") == "libc++"):
            self.cpp_info.components["libfolly"].system_libs.append("atomic")

        if self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version.value) >= "11.0":
            self.cpp_info.components["libfolly"].system_libs.append("c++abi")

        self.cpp_info.components["follybenchmark"].set_property("cmake_target_name", "Folly::follybenchmark")
        self.cpp_info.components["follybenchmark"].set_property("pkg_config_name", "libfollybenchmark")
        self.cpp_info.components["follybenchmark"].libs = ["follybenchmark"]
        self.cpp_info.components["follybenchmark"].requires = ["libfolly"]

        self.cpp_info.components["folly_test_util"].set_property("cmake_target_name", "Folly::folly_test_util")
        self.cpp_info.components["folly_test_util"].set_property("pkg_config_name", "libfolly_test_util")
        self.cpp_info.components["folly_test_util"].libs = ["folly_test_util"]
        self.cpp_info.components["folly_test_util"].requires = ["libfolly"]

        # In 2026.04.20.00, exception_tracer/counter code is compiled into libfolly.so
        # (the modular build merges them as object libraries), so no separate
        # component declarations are needed.

        # Legacy v1 generator names — consumers still using
        # generators="cmake_find_package" / "cmake_find_package_multi" need
        # these. Conan v2 ignores them silently.
        self.cpp_info.filenames["cmake_find_package"] = "folly"
        self.cpp_info.filenames["cmake_find_package_multi"] = "folly"
        self.cpp_info.names["cmake_find_package"] = "Folly"
        self.cpp_info.names["cmake_find_package_multi"] = "Folly"
        self.cpp_info.components["libfolly"].names["cmake_find_package"] = "folly"
        self.cpp_info.components["libfolly"].names["cmake_find_package_multi"] = "folly"
        self.cpp_info.components["follybenchmark"].names["cmake_find_package"] = "follybenchmark"
        self.cpp_info.components["follybenchmark"].names["cmake_find_package_multi"] = "follybenchmark"
        self.cpp_info.components["folly_test_util"].names["cmake_find_package"] = "folly_test_util"
        self.cpp_info.components["folly_test_util"].names["cmake_find_package_multi"] = "folly_test_util"
