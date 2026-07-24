from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import get
from conan.tools.build import check_min_cppstd


class MilvusSdkCppConan(ConanFile):
    name = "milvus-sdk-cpp"
    license = "Apache-2.0"
    url = "https://github.com/milvus-io/milvus-sdk-cpp"
    description = "Milvus C++ SDK"

    _legacy_nlohmann_versions = {"2.6.2", "2.6.3", "2.6.4", "3.0.0"}

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "grpc/*:shared": False,
        "protobuf/*:shared": False,
        "grpc/*:secure": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        check_min_cppstd(self, 14)

    def requirements(self):
        self.requires("grpc/1.65.0")
        self.requires("protobuf/5.27.0")
        self.requires("abseil/20240116.2")

        # These releases still call find_package(nlohmann_json) during
        # configuration. Newer releases use the SDK's namespaced vendored
        # headers and intentionally avoid a Conan nlohmann_json dependency.
        if str(self.version) in self._legacy_nlohmann_versions:
            self.requires("nlohmann_json/3.11.3")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["MILVUS_BUILD_TEST"] = False
        tc.variables["BUILD_FROM_CONAN"] = "ON"
        tc.variables["MILVUS_SDK_VERSION"] = self.version
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "milvus_sdk")
        self.cpp_info.set_property("cmake_target_name", "milvus_sdk::milvus_sdk")
        self.cpp_info.libs = ["milvus_sdk"]
        self.cpp_info.system_libs = ["dl"] if str(self.settings.os) == "Linux" else []
        self.cpp_info.builddirs = ["lib/cmake/milvus_sdk"]
        self.cpp_info.set_property("pkg_config_name", "milvus-sdk-cpp")

        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.bindirs = ["bin"]

        if not self.options.shared:
            self.cpp_info.requires = [
                "protobuf::libprotobuf",
                "grpc::grpc++",
                "abseil::absl_base",
            ]
            if str(self.version) in self._legacy_nlohmann_versions:
                self.cpp_info.requires.append("nlohmann_json::nlohmann_json")
