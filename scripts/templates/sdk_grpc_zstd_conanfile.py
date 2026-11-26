from conan.tools.cmake import CMakeDeps, CMakeToolchain

from registry_base import MilvusSdkCppConan as RegistrySdk


class MilvusSdkCppConan(RegistrySdk):
    exports = "registry_base.py"
    options = {**RegistrySdk.options, "with_grpc_zstd": [True, False]}
    default_options = {**RegistrySdk.default_options, "with_grpc_zstd": True}

    def requirements(self):
        if not self.options.with_grpc_zstd:
            return super().requirements()
        self.requires(self.conan_data["grpc_zstd"][str(self.version)])
        self.requires("protobuf/5.27.0#99c5d5f87d1eea580a2234238020821b")
        self.requires("abseil/20240116.2#f223c3320ef9e6feee1d904ae925197d")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["MILVUS_BUILD_TEST"] = False
        tc.variables["BUILD_FROM_CONAN"] = "ON"
        tc.variables["MILVUS_SDK_VERSION"] = self.version
        tc.variables["MILVUS_GRPC_ZSTD"] = bool(self.options.with_grpc_zstd)
        tc.generate()
        CMakeDeps(self).generate()
