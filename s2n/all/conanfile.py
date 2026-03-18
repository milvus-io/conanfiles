from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir, save
import os
import textwrap

required_conan_version = ">=1.53.0"


class S2nConan(ConanFile):
    name = "s2n"
    description = "An implementation of the TLS/SSL protocols"
    topics = ("aws", "amazon", "cloud", )
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/aws/s2n-tls"
    license = "Apache-2.0"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "crypto_backend": ["openssl", "aws-lc"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "crypto_backend": "openssl",
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.crypto_backend == "aws-lc":
            self.requires("aws-lc/1.70.0")
        else:
            self.requires("openssl/[>=1.1 <4]")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("Not supported (yet)")
        if self.options.crypto_backend == "aws-lc" and self.settings.os != "Linux":
            raise ConanInvalidConfiguration(
                "aws-lc crypto backend with S2N_INTERN_LIBCRYPTO is only supported on Linux"
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.variables["UNSAFE_TREAT_WARNINGS_AS_ERRORS"] = False
        tc.variables["SEARCH_LIBCRYPTO"] = False  # see CMakeLists wrapper
        if self.options.crypto_backend == "aws-lc":
            tc.variables["S2N_INTERN_LIBCRYPTO"] = True
            # s2n's S2N_INTERN_LIBCRYPTO needs the path to static libcrypto.a
            # for objcopy symbol prefixing. CMakeDeps creates INTERFACE targets
            # which don't have LOCATION, so we pass the paths directly.
            awslc_info = self.dependencies["aws-lc"].cpp_info
            tc.variables["crypto_STATIC_LIBRARY"] = os.path.join(
                awslc_info.libdirs[0], "libcrypto.a")
            tc.variables["crypto_INCLUDE_DIR"] = awslc_info.includedirs[0]
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "s2n"))

        # TODO: to remove in conan v2 once legacy generators removed
        self._create_cmake_module_alias_targets(
            os.path.join(self.package_folder, self._module_file_rel_path),
            {"AWS::s2n": "s2n::s2n"}
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
        self.cpp_info.set_property("cmake_file_name", "s2n")
        self.cpp_info.set_property("cmake_target_name", "AWS::s2n")
        self.cpp_info.libs = ["s2n"]
        if self.options.crypto_backend == "aws-lc":
            self.cpp_info.requires = ["aws-lc::crypto"]
        else:
            self.cpp_info.requires = ["openssl::crypto"]
        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.system_libs = ["m", "pthread"]

        # TODO: to remove in conan v2 once cmake_find_package* generators removed
        self.cpp_info.build_modules["cmake_find_package"] = [self._module_file_rel_path]
        self.cpp_info.build_modules["cmake_find_package_multi"] = [self._module_file_rel_path]
