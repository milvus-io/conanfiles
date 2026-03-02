from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import is_msvc, msvc_runtime_flag
from conan.tools.build import check_min_cppstd, can_run, valid_min_cppstd
from conan.tools.scm import Version
from conan.tools.files import get, copy, rmdir, replace_in_file, apply_conandata_patches, export_conandata_patches
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
import os

required_conan_version = ">=2.0"


class FollyConan(ConanFile):
    name = "folly"
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
        "use_sse4_2": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "use_sse4_2": False
    }

    @property
    def _minimum_cpp_standard(self):
        return 17 if Version(self.version) >= "2022.01.31.00" else 14

    @property
    def _minimum_compilers_version(self):
        return {
            "msvc": "191",
            "gcc": "5",
            "clang": "6",
            "apple-clang": "8",
        } if self._minimum_cpp_standard == 14 else {
            "gcc": "7",
            "msvc": "192",
            "clang": "6",
            "apple-clang": "10",
        }

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

        if str(self.settings.arch) not in ['x86', 'x86_64']:
            del self.options.use_sse4_2

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if Version(self.version) >= "2023.10.30.00":
            self.requires("boost/1.83.0", transitive_headers=True)
            self.requires("bzip2/1.0.8")
            self.requires("double-conversion/3.2.1", transitive_headers=True)
            self.requires("gflags/2.2.2", transitive_headers=True)
            self.requires("glog/0.6.0", transitive_headers=True)
            self.requires("libevent/2.1.12", transitive_headers=True)
            self.requires("openssl/3.1.2", transitive_headers=True)
            self.requires("lz4/1.9.4")
            self.requires("snappy/1.1.9")
            self.requires("zlib/1.2.13")
            self.requires("zstd/1.5.5")
            if not is_msvc(self):
                self.requires("libdwarf/20191104")
            self.requires("libsodium/cci.20220430")
            self.requires("xz_utils/5.4.0")
            if self.settings.os == "Linux":
                self.requires("libiberty/9.1.0")
                self.requires("libunwind/1.7.2")
            self.requires("fmt/9.1.0", transitive_headers=True)
        else:
            self.requires("boost/1.78.0")
            self.requires("bzip2/1.0.8")
            self.requires("double-conversion/3.2.0")
            self.requires("gflags/2.2.2")
            self.requires("glog/0.4.0")
            self.requires("libevent/2.1.12")
            self.requires("openssl/1.1.1q")
            self.requires("lz4/1.9.3")
            self.requires("snappy/1.1.9")
            self.requires("zlib/1.2.12")
            self.requires("zstd/1.5.2")
            if not is_msvc(self):
                self.requires("libdwarf/20191104")
            self.requires("libsodium/1.0.18")
            self.requires("xz_utils/5.2.5")
            # FIXME: Causing compilation issues on clang: self.requires("jemalloc/5.2.1")
            if self.settings.os == "Linux":
                self.requires("libiberty/9.1.0")
                self.requires("libunwind/1.5.0")
            if Version(self.version) >= "2020.08.10.00":
                self.requires("fmt/7.1.3")

    @property
    def _required_boost_components(self):
        return ["context", "filesystem", "program_options", "regex", "system", "thread"]

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)
        min_version = self._minimum_compilers_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warning("{} recipe lacks information about the {} compiler support.".format(self.name, self.settings.compiler))
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration("{} requires C++{} support. The current compiler {} {} does not support it.".format(
                    self.name, self._minimum_cpp_standard, self.settings.compiler, self.settings.compiler.version))

        if Version(self.version) < "2022.01.31.00" and self.settings.os != "Linux":
            raise ConanInvalidConfiguration("Conan support for non-Linux platforms starts with Folly version 2022.01.31.00")

        if self.settings.os == "Macos" and self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Conan currently requires a 64bit target architecture for Folly on Macos")

        if self.settings.os == "Windows" and self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Folly requires a 64bit target architecture on Windows")

        if self.settings.os in ["Macos", "Windows"] and self.options.shared:
            raise ConanInvalidConfiguration("Folly could not be built on {} as shared library".format(self.settings.os))

        if Version(self.version) == "2020.08.10.00" and self.settings.compiler == "clang" and self.options.shared:
            raise ConanInvalidConfiguration("Folly could not be built by clang as a shared library")

        if self.dependencies["boost"].options.header_only:
            raise ConanInvalidConfiguration("Folly could not be built with a header only Boost")

        miss_boost_required_comp = any(getattr(self.dependencies["boost"].options, "without_{}".format(boost_comp), True) for boost_comp in self._required_boost_components)
        if miss_boost_required_comp:
            raise ConanInvalidConfiguration("Folly requires these boost components: {}".format(", ".join(self._required_boost_components)))

        if self.options.get_safe("use_sse4_2") and str(self.settings.arch) not in ['x86', 'x86_64']:
            raise ConanInvalidConfiguration(f"{self.ref} can use the option use_sse4_2 only on x86 and x86_64 archs.")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)

        if can_run(self):
            tc.variables["FOLLY_HAVE_UNALIGNED_ACCESS_EXITCODE"] = "0"
            tc.variables["FOLLY_HAVE_UNALIGNED_ACCESS_EXITCODE__TRYRUN_OUTPUT"] = ""
            tc.variables["FOLLY_HAVE_LINUX_VDSO_EXITCODE"] = "0"
            tc.variables["FOLLY_HAVE_LINUX_VDSO_EXITCODE__TRYRUN_OUTPUT"] = ""
            tc.variables["FOLLY_HAVE_WCHAR_SUPPORT_EXITCODE"] = "0"
            tc.variables["FOLLY_HAVE_WCHAR_SUPPORT_EXITCODE__TRYRUN_OUTPUT"] = ""
            tc.variables["HAVE_VSNPRINTF_ERRORS_EXITCODE"] = "0"
            tc.variables["HAVE_VSNPRINTF_ERRORS_EXITCODE__TRYRUN_OUTPUT"] = ""

        if self.options.get_safe("use_sse4_2") and str(self.settings.arch) in ['x86', 'x86_64']:
            # in folly, if simd >=sse4.2, we also needs -mfma flag to avoid compiling error.
            if not is_msvc(self):
                tc.variables["CMAKE_C_FLAGS"] = "-mfma"
                tc.variables["CMAKE_CXX_FLAGS"] = "-mfma"
            else:
                tc.variables["CMAKE_C_FLAGS"] = "/arch:FMA"
                tc.variables["CMAKE_CXX_FLAGS"] = "/arch:FMA"

        if Version(self.version) >= "2023.10.30.00":
            tc.variables["FOLLY_HAVE_LIBUNWIND"] = False
            tc.variables["FOLLY_HAVE_BACKTRACE"] = False

        tc.variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)

        # Determine C++ standard
        cppstd = self.settings.get_safe("compiler.cppstd")
        if cppstd:
            # Remove 'gnu' prefix if present
            cxx_std_value = "c++{}".format(str(cppstd).replace("gnu", ""))
        else:
            cxx_std_value = "c++{}".format(self._minimum_cpp_standard)
        tc.variables["CXX_STD"] = cxx_std_value

        if is_msvc(self):
            tc.variables["MSVC_LANGUAGE_VERSION"] = cxx_std_value
            tc.variables["MSVC_ENABLE_ALL_WARNINGS"] = False
            tc.variables["MSVC_USE_STATIC_RUNTIME"] = "MT" in msvc_runtime_flag(self)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        apply_conandata_patches(self)
        if Version(self.version) >= "2023.10.30.00":
            replace_in_file(self, os.path.join(self.source_folder, "folly", "CMakeLists.txt"),
                            "add_subdirectory(logging/example)", "")
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
        self.cpp_info.set_property("cmake_file_name", "folly")
        self.cpp_info.set_property("cmake_target_name", "Folly::folly")
        self.cpp_info.set_property("pkg_config_name", "libfolly")

        if Version(self.version) == "2019.10.21.00":
            self.cpp_info.components["libfolly"].libs = [
                "follybenchmark",
                "folly_test_util",
                "folly"
            ]
        elif Version(self.version) >= "2020.08.10.00":
            if self.settings.os == "Linux":
                self.cpp_info.components["libfolly"].libs = [
                    "folly_exception_counter",
                    "folly_exception_tracer",
                    "folly_exception_tracer_base",
                    "folly_test_util",
                    "follybenchmark",
                    "folly"
                ]
            else:
                self.cpp_info.components["libfolly"].libs = [
                    "folly_test_util",
                    "follybenchmark",
                    "folly"
                ]

        self.cpp_info.components["libfolly"].requires = [
            "boost::boost",
            "bzip2::bzip2",
            "double-conversion::double-conversion",
            "gflags::gflags",
            "glog::glog",
            "libevent::libevent",
            "lz4::lz4",
            "openssl::openssl",
            "snappy::snappy",
            "zlib::zlib",
            "zstd::zstd",
            "libsodium::libsodium",
            "xz_utils::xz_utils"
        ]
        if not is_msvc(self):
            self.cpp_info.components["libfolly"].requires.append("libdwarf::libdwarf")
        if self.settings.os == "Linux":
            self.cpp_info.components["libfolly"].requires.extend(["libiberty::libiberty", "libunwind::libunwind"])
            self.cpp_info.components["libfolly"].system_libs.extend(["pthread", "dl", "rt"])

        if Version(self.version) >= "2020.08.10.00":
            self.cpp_info.components["libfolly"].requires.append("fmt::fmt")
            if self.settings.os == "Linux":
                self.cpp_info.components["libfolly"].defines.extend(["FOLLY_HAVE_ELF", "FOLLY_HAVE_DWARF"])

        elif self.settings.os == "Windows":
            self.cpp_info.components["libfolly"].system_libs.extend(["ws2_32", "iphlpapi", "crypt32"])

        if (self.settings.os == "Linux" and self.settings.compiler == "clang" and
            self.settings.compiler.libcxx == "libstdc++") or \
           (self.settings.os == "Macos" and self.settings.compiler == "apple-clang" and
            Version(self.settings.compiler.version.value) == "9.0" and self.settings.compiler.libcxx == "libc++"):
            self.cpp_info.components["libfolly"].system_libs.append("atomic")

        if self.settings.os == "Macos" and self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version.value) >= "11.0":
            self.cpp_info.components["libfolly"].system_libs.append("c++abi")

        if self.options.get_safe("use_sse4_2") and str(self.settings.arch) in ['x86', 'x86_64']:
            self.cpp_info.components["libfolly"].defines = ["FOLLY_SSE=4", "FOLLY_SSE_MINOR=2"]

        self.cpp_info.components["libfolly"].set_property("cmake_target_name", "Folly::folly")
        self.cpp_info.components["libfolly"].set_property("pkg_config_name", "libfolly")

        if Version(self.version) >= "2019.10.21.00":
            self.cpp_info.components["follybenchmark"].set_property("cmake_target_name", "Folly::follybenchmark")
            self.cpp_info.components["follybenchmark"].set_property("pkg_config_name", "libfollybenchmark")
            self.cpp_info.components["follybenchmark"].libs = ["follybenchmark"]
            self.cpp_info.components["follybenchmark"].requires = ["libfolly"]

            self.cpp_info.components["folly_test_util"].set_property("cmake_target_name", "Folly::folly_test_util")
            self.cpp_info.components["folly_test_util"].set_property("pkg_config_name", "libfolly_test_util")
            self.cpp_info.components["folly_test_util"].libs = ["folly_test_util"]
            self.cpp_info.components["folly_test_util"].requires = ["libfolly"]

        if Version(self.version) >= "2020.08.10.00" and self.settings.os == "Linux":
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
