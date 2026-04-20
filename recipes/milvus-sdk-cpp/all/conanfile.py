from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import get
from conan.tools.build import check_min_cppstd


class MilvusSdkCppConan(ConanFile):
    name = "milvus-sdk-cpp"
    license = "Apache-2.0"
    url = "https://github.com/milvus-io/milvus-sdk-cpp"
    description = "Milvus C++ SDK"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
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
        self.cpp_info.libs = ["milvus_sdk"]
