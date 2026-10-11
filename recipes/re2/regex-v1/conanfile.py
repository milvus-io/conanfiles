from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, patch, rmdir
import os

required_conan_version = ">=2.0"


class MilvusRe2Conan(ConanFile):
    name = "re2"
    description = "RE2 with a public, bounded necessary-literal API"
    license = ("BSD-3-Clause", "Apache-2.0")
    homepage = "https://github.com/google/re2"
    url = "https://github.com/milvus-io/conanfiles"
    topics = ("regex", "required-literals", "fm-index")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False],
               "with_icu": [True, False]}
    default_options = {"shared": False, "fPIC": True, "with_icu": False}
    exports_sources = "required_literals.patch", "required_literals.cc", "LICENSE.Apache-2.0"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_icu:
            self.requires("icu/74.2")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, "11")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        patch(self, base_path=self.source_folder,
              patch_file=os.path.join(self.export_sources_folder, "required_literals.patch"))
        copy(self, "required_literals.cc", src=self.export_sources_folder,
             dst=os.path.join(self.source_folder, "re2"))

    def generate(self):
        toolchain = CMakeToolchain(self)
        toolchain.variables["RE2_BUILD_TESTING"] = False
        toolchain.variables["RE2_USE_ICU"] = bool(self.options.with_icu)
        toolchain.generate()
        CMakeDeps(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "LICENSE.Apache-2.0", src=self.export_sources_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        CMake(self).install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "re2")
        self.cpp_info.set_property("cmake_target_name", "re2::re2")
        self.cpp_info.set_property("pkg_config_name", "re2")
        self.cpp_info.libs = ["re2"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs = ["m", "pthread"]
