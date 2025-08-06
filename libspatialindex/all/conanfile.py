from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
from conan.tools.scm import Version
import os

required_conan_version = ">=1.54.0"


class LibspatialindexConan(ConanFile):
    name = "libspatialindex"
    description = "A general framework for developing spatial indices."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://libspatialindex.org/"
    topics = ("spatial", "index", "geometry", "rtree")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _min_cppstd(self):
        return "11"

    @property
    def _compilers_minimum_version(self):
        return {
            "11": {
                "gcc": "5",
                "clang": "3.4",
                "apple-clang": "5.1",
                "Visual Studio": "14",
                "msvc": "190",
            },
        }.get(self._min_cppstd, {})

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "SpatialIndex")
        self.cpp_info.set_property("cmake_target_name", "SpatialIndex::spatialindex")
        self.cpp_info.set_property("pkg_config_name", "spatialindex")

        self.cpp_info.filenames["cmake_find_package"] = "SpatialIndex"
        self.cpp_info.filenames["cmake_find_package_multi"] = "SpatialIndex"
        self.cpp_info.names["cmake_find_package"] = "SpatialIndex"
        self.cpp_info.names["cmake_find_package_multi"] = "SpatialIndex"

        # spatialindex library
        self.cpp_info.components["spatialindex"].set_property("cmake_target_name", "SpatialIndex::spatialindex")
        self.cpp_info.components["spatialindex"].names["cmake_find_package"] = "spatialindex"
        self.cpp_info.components["spatialindex"].names["cmake_find_package_multi"] = "spatialindex"
        self.cpp_info.components["spatialindex"].libs = ["spatialindex"]
        
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["spatialindex"].system_libs.append("m")

        # spatialindex_c library (C API)
        self.cpp_info.components["spatialindex_c"].set_property("cmake_target_name", "SpatialIndex::spatialindex_c")
        self.cpp_info.components["spatialindex_c"].names["cmake_find_package"] = "spatialindex_c"
        self.cpp_info.components["spatialindex_c"].names["cmake_find_package_multi"] = "spatialindex_c"
        self.cpp_info.components["spatialindex_c"].libs = ["spatialindex_c"]
        self.cpp_info.components["spatialindex_c"].requires = ["spatialindex"] 
