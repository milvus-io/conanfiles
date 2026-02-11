from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir, replace_in_file
import os

required_conan_version = ">=1.54.0"


class RDKitConan(ConanFile):
    name = "rdkit"
    description = (
        "Minimal RDKit build: SMILES/MOL parsing, pickle serialization, "
        "molecular fingerprints (Morgan/MACCS/RDKit), substructure matching."
    )
    license = "BSD-3-Clause"
    url = "https://github.com/862103595/rdkit"
    homepage = "https://www.rdkit.org"
    topics = ("chemistry", "cheminformatics", "smiles", "fingerprint", "rdkit")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "boost/*:without_locale": False,
        "boost/*:without_test": True,
    }
    requires = "boost/1.83.0"

    # Libraries listed in *reverse* dependency order for static linking.
    _NEEDED_LIBS = {
        "RDKitRDGeneral",
        "RDKitDataStructs",
        "RDKitRDGeometryLib",
        "RDKitRingDecomposerLib",
        "RDKitGraphMol",
        "RDKitSmilesParse",
        "RDKitGenericGroups",
        "RDKitSubstructMatch",
        "RDKitSubgraphs",
        "RDKitCIPLabeler",
        "RDKitFingerprints",
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        # Consumed through a C ABI boundary (mol_c.h),
        # compatible across minor compiler versions.
        del self.info.settings.compiler.version

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)

        # C++20 required by RDKit for constexpr destructors
        tc.variables["CMAKE_CXX_STANDARD"] = "20"
        tc.variables["CMAKE_CXX_STANDARD_REQUIRED"] = "ON"

        # Boost from Conan
        boost_info = self.dependencies["boost"].cpp_info
        tc.variables["BOOST_ROOT"] = boost_info.rootpath
        tc.variables["Boost_INCLUDE_DIR"] = ";".join(boost_info.includedirs)
        tc.variables["BOOST_LIBRARYDIR"] = ";".join(boost_info.libdirs)
        tc.variables["Boost_NO_SYSTEM_PATHS"] = "ON"

        # Install layout
        tc.variables["RDK_INSTALL_INTREE"] = "OFF"
        tc.variables["RDK_INSTALL_DEV_COMPONENT"] = "ON"

        # Shared / static
        tc.variables["RDK_INSTALL_STATIC_LIBS"] = "OFF" if self.options.shared else "ON"

        # Minimal build – disable everything not needed
        for opt in [
            "RDK_BUILD_PYTHON_WRAPPERS", "RDK_BUILD_INCHI_SUPPORT",
            "RDK_BUILD_AVALON_SUPPORT", "RDK_BUILD_CPP_TESTS",
            "RDK_BUILD_SWIG_WRAPPERS", "RDK_BUILD_DESCRIPTORS3D",
            "RDK_BUILD_MOLINTERCHANGE_SUPPORT", "RDK_BUILD_FREETYPE_SUPPORT",
            "RDK_BUILD_COORDGEN_SUPPORT", "RDK_BUILD_CAIRO_SUPPORT",
            "RDK_BUILD_QT_SUPPORT", "RDK_BUILD_CHEMDRAW_SUPPORT",
            "RDK_BUILD_MAEPARSER_SUPPORT", "RDK_BUILD_PGSQL",
            "RDK_BUILD_CONTRIB", "RDK_BUILD_COMPRESSED_SUPPLIERS",
            "RDK_BUILD_SLN_SUPPORT", "RDK_BUILD_FUZZ_TARGETS",
            "RDK_BUILD_CFFI_LIB", "RDK_BUILD_MINIMAL_LIB",
            "RDK_BUILD_TEST_GZIP", "RDK_BUILD_RPATH_SUPPORT",
            "RDK_USE_BOOST_SERIALIZATION", "RDK_USE_BOOST_IOSTREAMS",
            "RDK_USE_BOOST_STACKTRACE", "RDK_TEST_MULTITHREADED",
            "RDK_USE_FLEXBISON",
        ]:
            tc.variables[opt] = "OFF"

        # Features we DO need
        tc.variables["RDK_BUILD_THREADSAFE_SSS"] = "ON"
        tc.variables["RDK_OPTIMIZE_POPCNT"] = "ON"

        tc.generate()

    def _patch_sources(self):
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        " CONFIG)", ")", strict=False)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "license*", src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"), keep_path=False)
        copy(self, "License*", src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"), keep_path=False)

        cmake = CMake(self)
        cmake.install()

        # Strip unneeded libraries to minimise package size
        lib_dir = os.path.join(self.package_folder, "lib")
        if os.path.isdir(lib_dir):
            for fname in os.listdir(lib_dir):
                fpath = os.path.join(lib_dir, fname)
                if not (os.path.isfile(fpath) or os.path.islink(fpath)):
                    continue
                is_lib = (
                    fname.endswith(".so") or ".so." in fname
                    or fname.endswith(".a") or fname.endswith(".dylib")
                )
                if not is_lib:
                    continue
                if not any(fname.startswith("lib" + n) for n in self._NEEDED_LIBS):
                    os.remove(fpath)

            rmdir(self, os.path.join(lib_dir, "cmake"))

        # Strip share/RDKit/{Contrib,Docs} to save ~91 MB
        for subdir in ("Contrib", "Docs"):
            rmdir(self, os.path.join(self.package_folder, "share", "RDKit", subdir))

    def package_info(self):
        self.cpp_info.libs = [
            "RDKitFingerprints",
            "RDKitCIPLabeler",
            "RDKitSubstructMatch",
            "RDKitSubgraphs",
            "RDKitGenericGroups",
            "RDKitSmilesParse",
            "RDKitGraphMol",
            "RDKitRingDecomposerLib",
            "RDKitRDGeometryLib",
            "RDKitDataStructs",
            "RDKitRDGeneral",
        ]
        self.cpp_info.includedirs = ["include", "include/rdkit"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs = ["pthread"]
