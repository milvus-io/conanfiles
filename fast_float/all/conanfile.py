from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import get, copy
import os


# Dual-targetable: works on Conan v1 (>=1.54.0) and Conan v2.
required_conan_version = ">=1.54.0"


class FastFloatConan(ConanFile):
    name = "fast_float"
    version = "8.0.0"
    description = "Fast and exact implementation of the C++ from_chars functions for number types"
    homepage = "https://github.com/fastfloat/fast_float"
    license = "Apache-2.0 OR MIT OR BSL-1.0"
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["FASTFLOAT_TEST"] = False
        tc.variables["FASTFLOAT_SANITIZE"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_id(self):
        # Header-only: package_id should not vary with settings/options.
        # `self.info.clear()` is the v2 idiom, shimmed in Conan v1.54+.
        self.info.clear()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "FastFloat")
        self.cpp_info.set_property("cmake_target_name", "FastFloat::fast_float")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        # Legacy v1 generator names.
        self.cpp_info.filenames["cmake_find_package"] = "FastFloat"
        self.cpp_info.filenames["cmake_find_package_multi"] = "FastFloat"
        self.cpp_info.names["cmake_find_package"] = "FastFloat"
        self.cpp_info.names["cmake_find_package_multi"] = "FastFloat"
