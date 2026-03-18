from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir, save
import os
import textwrap

required_conan_version = ">=1.53.0"


class AwsLcConan(ConanFile):
    name = "aws-lc"
    description = (
        "AWS-LC is a general-purpose cryptographic library maintained by the AWS "
        "cryptography team for AWS and their customers. It is based on code from "
        "the Google BoringSSL project and the OpenSSL project."
    )
    topics = ("aws", "amazon", "cloud", "crypto", "fips")
    url = "https://github.com/milvus-io/conanfiles"
    homepage = "https://github.com/aws/aws-lc"
    license = "Apache-2.0"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "fips": [True, False],
    }
    default_options = {
        "fPIC": True,
        "fips": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        # aws-lc is a C library; remove C++ settings
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("aws-lc FIPS build is not supported on Windows")
        if self.options.fips and self.settings.os != "Linux":
            raise ConanInvalidConfiguration("aws-lc FIPS mode is only supported on Linux")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        # Always build static for S2N_INTERN_LIBCRYPTO usage
        tc.variables["BUILD_SHARED_LIBS"] = False
        tc.variables["DISABLE_GO"] = not self.options.fips
        tc.variables["DISABLE_PERL"] = False
        if self.options.fips:
            tc.variables["FIPS"] = True
        # Ensure PIC for embedding into shared libraries (e.g. s2n .so)
        tc.variables["CMAKE_POSITION_INDEPENDENT_CODE"] = True
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

        # Create cmake module alias so find_package(crypto) works for s2n
        self._create_cmake_module_alias_targets(
            os.path.join(self.package_folder, self._module_file_rel_path),
            {"AWS::crypto": "aws-lc::crypto"}
        )

    def _create_cmake_module_alias_targets(self, module_file, targets):
        content = ""
        for alias, aliased in targets.items():
            content += textwrap.dedent(f"""\
                if(TARGET {aliased} AND NOT TARGET {alias})
                    add_library({alias} INTERFACE IMPORTED)
                    set_property(TARGET {alias} PROPERTY INTERFACE_LINK_LIBRARIES {aliased})
                endif()
            """)
        save(self, module_file, content)

    @property
    def _module_file_rel_path(self):
        return os.path.join("lib", "cmake", f"conan-official-{self.name}-targets.cmake")

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "crypto")
        self.cpp_info.set_property("cmake_target_name", "AWS::crypto")

        # aws-lc installs as libcrypto.a (and optionally libssl.a)
        # We only need libcrypto for s2n
        self.cpp_info.components["crypto"].set_property("cmake_target_name", "AWS::crypto")
        self.cpp_info.components["crypto"].libs = ["crypto"]
        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.components["crypto"].system_libs = ["dl", "m", "pthread"]

        # TODO: to remove in conan v2 once cmake_find_package* generators removed
        self.cpp_info.build_modules["cmake_find_package"] = [self._module_file_rel_path]
        self.cpp_info.build_modules["cmake_find_package_multi"] = [self._module_file_rel_path]
