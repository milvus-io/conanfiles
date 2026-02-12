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
import platform


required_conan_version = ">=1.54.0"


class FollyConan(ConanFile):
    name = "folly"
    description = "An open-source C++ components library developed and used at Facebook"
    topics = ("facebook", "components", "core", "efficiency")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/facebook/folly"
    license = "Apache-2.0"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_sse4_2": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "use_sse4_2": True,
    }

    @property
    def _min_cppstd(self):
        return 17

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
        if str(self.settings.arch) not in ["x86", "x86_64"]:
            del self.options.use_sse4_2

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if is_msvc(self):
            del self.options.shared

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.85.0")
        self.requires("bzip2/1.0.8")
        self.requires("double-conversion/3.3.0")
        self.requires("gflags/2.2.2")
        self.requires("glog/0.7.1")
        self.requires("libevent/2.1.12")
        self.requires("openssl/[>=1.1 <4]")
        self.requires("lz4/1.10.0")
        self.requires("snappy/1.2.1")
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("zstd/1.5.5")
        if not is_msvc(self):
            self.requires("libdwarf/0.8.0")
        self.requires("libsodium/1.0.19")
        self.requires("xz_utils/[>=5.4.5 <6]")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.requires("libiberty/9.1.0")
            self.requires("libunwind/1.8.0")
        self.requires("fmt/10.2.1")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.17 <4]")

    @property
    def _required_boost_components(self):
        return ["context", "filesystem", "program_options", "regex", "system", "thread"]

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
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

        if self.settings.os == "Windows" and self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration(f"{self.ref} requires a 64bit target architecture on Windows.")

        if self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version) < "14.0":
            raise ConanInvalidConfiguration(f"{self.ref} could not be built by apple-clang < 14.0.")

        if self.options["boost"].header_only:
            raise ConanInvalidConfiguration(f"{self.ref} could not be built with a header only Boost.")

        miss_boost_required_comp = any(
            getattr(self.options["boost"], f"without_{boost_comp}", True)
            for boost_comp in self._required_boost_components
        )
        if miss_boost_required_comp:
            required_components = ", ".join(self._required_boost_components)
            raise ConanInvalidConfiguration(
                f"{self.ref} requires these Boost components: {required_components}"
            )

        if self.options.get_safe("use_sse4_2") and str(self.settings.arch) not in ["x86", "x86_64"]:
            raise ConanInvalidConfiguration(
                f"{self.ref} can use the option use_sse4_2 only on x86 and x86_64 archs."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=False)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_PROJECT_folly_INCLUDE"] = "conan_deps.cmake"
        tc.variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)

        if is_apple_os(self) and cross_building(self):
            for var in [
                "FOLLY_HAVE_UNALIGNED_ACCESS",
                "FOLLY_HAVE_LINUX_VDSO",
                "FOLLY_HAVE_WCHAR_SUPPORT",
                "HAVE_VSNPRINTF_ERRORS",
            ]:
                tc.cache_variables[f"{var}_EXITCODE"] = 0

        # SSE4.2 support
        if self.options.get_safe("use_sse4_2") and str(self.settings.arch) in ["x86", "x86_64"]:
            # Double check actual machine architecture to avoid misdetection on ARM+GPU machines
            if platform.machine() in ["x86_64", "x86", "AMD64", "i686"]:
                tc.preprocessor_definitions["FOLLY_SSE"] = "4"
                tc.preprocessor_definitions["FOLLY_SSE_MINOR"] = "2"
                if not is_msvc(self):
                    tc.variables["CMAKE_C_FLAGS"] = "-msse4.2"
                    tc.variables["CMAKE_CXX_FLAGS"] = "-msse4.2"
                else:
                    tc.variables["CMAKE_C_FLAGS"] = "/arch:SSE4.2"
                    tc.variables["CMAKE_CXX_FLAGS"] = "/arch:SSE4.2"

        tc.cache_variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
        # Relocatable shared lib on Macos
        if is_apple_os(self):
            tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        # Honor BUILD_SHARED_LIBS from conan_toolchain (see https://github.com/conan-io/conan/issues/11840)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        # Honor Boost_ROOT set by boost recipe
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0074"] = "NEW"

        if is_msvc(self):
            cppstd = self.settings.get_safe("compiler.cppstd", self._min_cppstd)
            year = str(cppstd)
            if year > "17":
                year = "latest"
            cxx_std_value = f"c++{year}"
            tc.cache_variables["MSVC_LANGUAGE_VERSION"] = cxx_std_value
            tc.cache_variables["MSVC_ENABLE_ALL_WARNINGS"] = False
            tc.cache_variables["MSVC_USE_STATIC_RUNTIME"] = is_msvc_static_runtime(self)
            tc.preprocessor_definitions["NOMINMAX"] = ""

        if not self.options["boost"].header_only:
            tc.cache_variables["BOOST_LINK_STATIC"] = not self.options["boost"].shared

        # Set RPATH for proper library linking
        if self.settings.os != "Windows":
            tc.variables["CMAKE_INSTALL_RPATH_USE_LINK_PATH"] = "TRUE"
            tc.variables["CMAKE_BUILD_WITH_INSTALL_RPATH"] = "TRUE"
            tc.variables["CMAKE_INSTALL_RPATH"] = "${CMAKE_INSTALL_PREFIX}/lib"

        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("boost", "cmake_file_name", "Boost")
        deps.set_property("bzip2", "cmake_file_name", "BZip2")
        deps.set_property("double-conversion", "cmake_file_name", "DoubleConversion")
        deps.set_property("fmt", "cmake_file_name", "fmt")
        deps.set_property("gflags", "cmake_file_name", "Gflags")
        deps.set_property("glog", "cmake_file_name", "Glog")
        deps.set_property("libdwarf", "cmake_file_name", "LibDwarf")
        deps.set_property("libevent", "cmake_file_name", "LibEvent")
        deps.set_property("libiberty", "cmake_file_name", "Libiberty")
        deps.set_property("libsodium", "cmake_file_name", "Libsodium")
        deps.set_property("libunwind", "cmake_file_name", "LibUnwind")
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
        replace_in_file(self, folly_deps, "${Boost_LIBRARIES}", f"{' '.join(self._required_boost_cmake_targets)}")
        replace_in_file(self, folly_deps, "OpenSSL 1.1.1", "OpenSSL")
        # Make liburing optional since we don't ship it
        replace_in_file(self, folly_deps,
                        "find_package(LibUring REQUIRED CONFIG)",
                        "find_package(LibUring CONFIG QUIET)",
                        strict=False)
        # Disable example
        save(self, os.path.join(self.source_folder, "folly", "logging", "example", "CMakeLists.txt"), "")
        # Disable custom find modules to use Conan CMakeDeps instead
        rm(self, "Find*.cmake", os.path.join(self.source_folder, "CMake"))
        rm(self, "Find*.cmake", os.path.join(self.source_folder, "build", "fbcode_builder", "CMake"))
        # Skip generating .pc file to avoid Windows errors when trying to compile with pkg-config
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "gen_pkgconfig_vars(FOLLY_PKGCONFIG folly_deps)", "", strict=False)

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
        self.cpp_info.set_property("cmake_target_name", "Folly::folly")
        self.cpp_info.set_property("pkg_config_name", "libfolly")

        self.cpp_info.components["libfolly"].set_property("cmake_target_name", "Folly::folly")
        self.cpp_info.components["libfolly"].set_property("pkg_config_name", "libfolly")
        self.cpp_info.components["libfolly"].libs = ["folly"]
        self.cpp_info.components["libfolly"].requires = ["fmt::fmt"] + self._required_boost_conan_components + [
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
            self.cpp_info.components["libfolly"].requires.extend(
                ["libiberty::libiberty", "libunwind::libunwind"]
            )
        if self.settings.os == "Linux":
            self.cpp_info.components["libfolly"].system_libs.extend(["pthread", "dl", "rt"])
            self.cpp_info.components["libfolly"].defines.extend(["FOLLY_HAVE_ELF", "FOLLY_HAVE_DWARF"])
        elif self.settings.os == "Windows":
            self.cpp_info.components["libfolly"].system_libs.extend(["ws2_32", "iphlpapi", "crypt32"])

        if self.settings.get_safe("compiler.libcxx") == "libstdc++" or \
           (self.settings.compiler == "apple-clang" and
            Version(self.settings.compiler.version.value) == "9.0" and
            self.settings.get_safe("compiler.libcxx") == "libc++"):
            self.cpp_info.components["libfolly"].system_libs.append("atomic")

        if self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version.value) >= "11.0":
            self.cpp_info.components["libfolly"].system_libs.append("c++abi")

        # SSE4.2 defines for consumers
        if self.options.get_safe("use_sse4_2") and str(self.settings.arch) in ["x86", "x86_64"]:
            self.cpp_info.components["libfolly"].defines.extend(["FOLLY_SSE=4", "FOLLY_SSE_MINOR=2"])

        self.cpp_info.components["follybenchmark"].set_property("cmake_target_name", "Folly::follybenchmark")
        self.cpp_info.components["follybenchmark"].set_property("pkg_config_name", "libfollybenchmark")
        self.cpp_info.components["follybenchmark"].libs = ["follybenchmark"]
        self.cpp_info.components["follybenchmark"].requires = ["libfolly"]

        self.cpp_info.components["folly_test_util"].set_property("cmake_target_name", "Folly::folly_test_util")
        self.cpp_info.components["folly_test_util"].set_property("pkg_config_name", "libfolly_test_util")
        self.cpp_info.components["folly_test_util"].libs = ["folly_test_util"]
        self.cpp_info.components["folly_test_util"].requires = ["libfolly"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["folly_exception_tracer_base"].set_property("cmake_target_name", "Folly::folly_exception_tracer_base")
            self.cpp_info.components["folly_exception_tracer_base"].set_property("pkg_config_name", "libfolly_exception_tracer_base")
            self.cpp_info.components["folly_exception_tracer_base"].libs = ["folly_exception_tracer_base"]
            self.cpp_info.components["folly_exception_tracer_base"].requires = ["libfolly"]

            self.cpp_info.components["folly_exception_tracer"].set_property("cmake_target_name", "Folly::folly_exception_tracer")
            self.cpp_info.components["folly_exception_tracer"].set_property("pkg_config_name", "libfolly_exception_tracer")
            self.cpp_info.components["folly_exception_tracer"].libs = ["folly_exception_tracer"]
            self.cpp_info.components["folly_exception_tracer"].requires = ["folly_exception_tracer_base"]

            self.cpp_info.components["folly_exception_counter"].set_property("cmake_target_name", "Folly::folly_exception_counter")
            self.cpp_info.components["folly_exception_counter"].set_property("pkg_config_name", "libfolly_exception_counter")
            self.cpp_info.components["folly_exception_counter"].libs = ["folly_exception_counter"]
            self.cpp_info.components["folly_exception_counter"].requires = ["folly_exception_tracer"]

        # TODO: to remove in conan v2 once cmake_find_package_* & pkg_config generators removed
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
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["folly_exception_tracer_base"].names["cmake_find_package"] = "folly_exception_tracer_base"
            self.cpp_info.components["folly_exception_tracer_base"].names["cmake_find_package_multi"] = "folly_exception_tracer_base"
            self.cpp_info.components["folly_exception_tracer"].names["cmake_find_package"] = "folly_exception_tracer"
            self.cpp_info.components["folly_exception_tracer"].names["cmake_find_package_multi"] = "folly_exception_tracer"
            self.cpp_info.components["folly_exception_counter"].names["cmake_find_package"] = "folly_exception_counter"
            self.cpp_info.components["folly_exception_counter"].names["cmake_find_package_multi"] = "folly_exception_counter"
