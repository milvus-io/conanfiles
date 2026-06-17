import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir

required_conan_version = ">=1.53.0"


class LibbsonConan(ConanFile):
    name = "libbson"
    description = (
        "libbson: the BSON serialization library from the MongoDB C driver, "
        "built WITHOUT libmongoc (no networking/SASL/TLS, no utf8proc)."
    )
    license = "Apache-2.0"
    url = "https://github.com/milvus-io/conanfiles"
    homepage = "https://github.com/mongodb/mongo-c-driver"
    topics = ("bson", "mongodb", "serialization", "json")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        # libbson is a pure C library: its package id must not depend on C++ settings.
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        # Build libbson ONLY — never libmongoc (which is what drags in utf8proc,
        # OpenSSL, SASL, etc.).
        tc.cache_variables["ENABLE_MONGOC"] = "OFF"
        tc.cache_variables["ENABLE_BSON"] = "ON"
        tc.cache_variables["ENABLE_SHARED"] = self.options.shared
        tc.cache_variables["ENABLE_STATIC"] = not self.options.shared
        tc.cache_variables["ENABLE_TESTS"] = "OFF"
        tc.cache_variables["ENABLE_EXAMPLES"] = "OFF"
        tc.cache_variables["ENABLE_MAN_PAGES"] = "OFF"
        tc.cache_variables["ENABLE_HTML_DOCS"] = "OFF"
        tc.cache_variables["ENABLE_MAINTAINER_FLAGS"] = "OFF"
        tc.cache_variables["ENABLE_UNINSTALL"] = "OFF"
        tc.cache_variables["ENABLE_EXTRA_ALIGNMENT"] = "ON"
        tc.cache_variables["ENABLE_AUTOMATIC_INIT_AND_CLEANUP"] = "ON"
        tc.cache_variables["ENABLE_PIC"] = self.options.get_safe("fPIC", True)
        tc.cache_variables["BUILD_VERSION"] = self.version
        # Avoid installing VC runtime stuff on Windows.
        tc.variables["CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS_SKIP"] = "TRUE"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "THIRD_PARTY_NOTICES",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        # Match libbson's native CMake config name (bson-1.0) and target
        # (mongo::bson_shared / mongo::bson_static) so consumers can find_package
        # it exactly as they would the upstream package.
        self.cpp_info.set_property("cmake_file_name", "bson-1.0")
        lib_type = "shared" if self.options.shared else "static"
        self.cpp_info.set_property("cmake_target_name", f"mongo::bson_{lib_type}")
        self.cpp_info.set_property(
            "cmake_target_aliases", [f"bson::{lib_type}", "libbson::libbson"])
        self.cpp_info.set_property(
            "pkg_config_name",
            "libbson-1.0" if self.options.shared else "libbson-static-1.0")

        if self.options.shared:
            self.cpp_info.libs = ["bson-1.0"]
        else:
            self.cpp_info.libs = ["bson-static-1.0"]
            self.cpp_info.defines = ["BSON_STATIC"]

        self.cpp_info.includedirs = [os.path.join("include", "libbson-1.0")]

        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs = ["m", "pthread", "rt"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32"]
