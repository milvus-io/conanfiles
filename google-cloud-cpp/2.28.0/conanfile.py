import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, replace_in_file, rmdir
from conan.tools.microsoft import check_min_vs, is_msvc
from conan.tools.scm import Version
from conan.errors import ConanInvalidConfiguration

required_conan_version = ">=1.56.0"


def _load_components_2_28_0():
    """Lazy-load the components definition for 2.28.0."""
    import sys
    module_dir = os.path.dirname(os.path.abspath(__file__))
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    import components_2_28_0
    return components_2_28_0


class GoogleCloudCppConan(ConanFile):
    name = "google-cloud-cpp"
    description = "C++ Client Libraries for Google Cloud Services"
    license = "Apache-2.0"
    topics = (
        "google",
        "cloud",
        "google-cloud-storage",
        "google-cloud-platform",
    )
    homepage = "https://github.com/googleapis/google-cloud-cpp"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "components": ["ANY"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "components": "storage",
    }
    exports = ["components_2_28_0.py"]

    short_paths = True

    # Some components require custom dependency definitions in package_info().
    _REQUIRES_CUSTOM_DEPENDENCIES = {
        "bigquery", "bigtable", "iam", "oauth2", "pubsub", "spanner", "storage",
    }

    _SKIPPED_COMPONENTS = {
        'asset',
        'channel',
        'storagetransfer',
    }

    @property
    def _is_legacy_one_profile(self):
        return not hasattr(self, "settings_build")

    def _get_components_module(self):
        if str(self.version) == "2.28.0":
            return _load_components_2_28_0()
        raise ConanInvalidConfiguration(
            f"Unknown version {self.version}. Only 2.28.0 is supported by this recipe."
        )

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
            self.options["protobuf"].shared = True
            self.options["grpc"].shared = True

    def validate(self):
        check_min_vs(self, "192")
        if is_msvc(self) and self.info.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} shared not supported by Visual Studio")

        if hasattr(self, "settings_build") and cross_building(self):
            raise ConanInvalidConfiguration(
                "Recipe not prepared for cross-building (yet)"
            )

        if (
            self.settings.compiler == "clang"
            and Version(self.settings.compiler.version) < "6.0"
        ):
            raise ConanInvalidConfiguration("Clang version must be at least 6.0.")

        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 14)

        if (
            self.settings.compiler == "gcc"
            and Version(self.settings.compiler.version) < "5.4"
        ):
            raise ConanInvalidConfiguration("Building requires GCC >= 5.4")

        if self.info.options.shared and \
           (not self.dependencies["protobuf"].options.shared or \
            not self.dependencies["grpc"].options.shared):
            raise ConanInvalidConfiguration(
                "If built as shared, protobuf, and grpc must be shared as well."
                " Please, use `protobuf/*:shared=True`, and `grpc/*:shared=True`.")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], destination=self.source_folder, strip_root=True)

    def requirements(self):
        self.requires("protobuf/3.21.12", transitive_headers=True)
        self.requires("abseil/[>=20230125.3 <=20230802.1]", transitive_headers=True)
        self.requires("grpc/1.54.3", transitive_headers=True)
        self.requires("nlohmann_json/3.11.3")
        self.requires("crc32c/1.1.2")
        self.requires("libcurl/[>=7.78 <9]")
        self.requires("openssl/[>=1.1 <4]")
        self.requires("zlib/[>=1.2.11 <2]")

    def build_requirements(self):
        if not self._is_legacy_one_profile:
            self.tool_requires("grpc/<host_version>")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.variables["GOOGLE_CLOUD_CPP_WITH_MOCKS"] = False
        tc.variables["GOOGLE_CLOUD_CPP_ENABLE_MACOS_OPENSSL_CHECK"] = False
        tc.variables["GOOGLE_CLOUD_CPP_ENABLE_WERROR"] = False
        tc.variables["GOOGLE_CLOUD_CPP_ENABLE"] = ",".join(self._selected_components())
        tc.generate()
        VirtualBuildEnv(self).generate()
        if self._is_legacy_one_profile:
            VirtualRunEnv(self).generate(scope="build")
        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        settings_build = getattr(self, "settings_build", self.settings)
        if settings_build.os == "Macos":
            replace_in_file(self, os.path.join(self.source_folder, "cmake/CompileProtos.cmake"),
                            "${Protobuf_PROTOC_EXECUTABLE} ARGS",
                            '${CMAKE_COMMAND} -E env "DYLD_LIBRARY_PATH=$ENV{DYLD_LIBRARY_PATH}" ${Protobuf_PROTOC_EXECUTABLE} ARGS')

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _selected_components(self):
        """Parse the 'components' option into a list of component names."""
        raw = str(self.options.components)
        return [c.strip() for c in raw.split(",") if c.strip()]

    def _all_ga_components(self):
        """Return the full set of GA components for the version."""
        mod = self._get_components_module()
        return mod.COMPONENTS

    def _all_proto_components(self):
        """Return the full set of proto components for the version."""
        mod = self._get_components_module()
        return mod.PROTO_COMPONENTS

    def _all_dependencies(self):
        """Return the dependency map for proto components."""
        mod = self._get_components_module()
        return mod.DEPENDENCIES

    def _needed_proto_components(self):
        """Compute the set of proto component names needed by the selected GA components.

        For each selected component, we need its corresponding *_protos library and
        all transitive proto dependencies. We also always need the GRPC_UTILS_REQUIRED_PROTOS.
        """
        selected = set(self._selected_components())
        deps_map = self._all_dependencies()

        # Always needed for grpc_utils
        GRPC_UTILS_REQUIRED_PROTOS = {
            "iam_credentials_v1_iamcredentials_protos",
            "iam_v1_policy_protos",
            "longrunning_operations_protos",
            "rpc_error_details_protos",
            "rpc_status_protos",
        }

        needed = set(GRPC_UTILS_REQUIRED_PROTOS)

        # For each selected component, add its *_protos and transitive deps
        for comp in selected:
            if comp == "storage":
                # storage doesn't depend on a *_protos library at runtime
                continue
            if comp == "oauth2":
                # oauth2 doesn't depend on protos
                continue
            protos_name = f"{comp}_protos"
            if protos_name in deps_map:
                needed.add(protos_name)
                # Add transitive proto dependencies
                self._collect_proto_deps(protos_name, deps_map, needed)

        return needed

    def _collect_proto_deps(self, proto_name, deps_map, collected):
        """Recursively collect proto dependencies."""
        deps = deps_map.get(proto_name, [])
        for dep in deps:
            # Only collect proto deps (those that end with _protos and are in deps_map)
            if dep.endswith("_protos") and dep in deps_map and dep not in collected:
                collected.add(dep)
                self._collect_proto_deps(dep, deps_map, collected)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, path=os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, path=os.path.join(self.package_folder, "lib", "pkgconfig"))

    def _generate_proto_requires(self, component):
        deps_map = self._all_dependencies()
        return deps_map.get(component, [])

    def _add_proto_component(self, component):
        self.cpp_info.components[component].requires = self._generate_proto_requires(component)
        self.cpp_info.components[component].libs = [f"google_cloud_cpp_{component}"]
        self.cpp_info.components[component].names["pkg_config"] = f"google_cloud_cpp_{component}"

    def _add_grpc_component(self, component, protos, extra=None):
        SHARED_REQUIRES = ["grpc_utils", "common", "grpc::grpc++", "grpc::_grpc", "protobuf::libprotobuf", "abseil::absl_memory"]
        self.cpp_info.components[component].requires = (extra or []) + [protos] + SHARED_REQUIRES
        self.cpp_info.components[component].libs = [f"google_cloud_cpp_{component}"]
        self.cpp_info.components[component].names["pkg_config"] = f"google_cloud_cpp_{component}"

    def package_info(self):
        selected = set(self._selected_components())

        # Check if any selected component needs gRPC (i.e., not just storage/oauth2)
        needs_grpc = any(c not in ("storage", "oauth2") for c in selected)
        needed_protos = self._needed_proto_components() if needs_grpc else set()

        # Common component (always needed)
        self.cpp_info.components["common"].requires = ["abseil::absl_any", "abseil::absl_flat_hash_map", "abseil::absl_memory", "abseil::absl_optional", "abseil::absl_time"]
        self.cpp_info.components["common"].libs = ["google_cloud_cpp_common"]
        self.cpp_info.components["common"].names["pkg_config"] = "google_cloud_cpp_common"

        # rest_internal (always needed)
        self.cpp_info.components["rest_internal"].requires = ["common", "libcurl::libcurl", "openssl::ssl", "openssl::crypto", "zlib::zlib"]
        self.cpp_info.components["rest_internal"].libs = ["google_cloud_cpp_rest_internal"]
        self.cpp_info.components["rest_internal"].names["pkg_config"] = "google_cloud_cpp_rest_internal"

        if needs_grpc:
            # grpc_utils required protos
            GRPC_UTILS_REQUIRED_PROTOS = {
                "iam_credentials_v1_iamcredentials_protos",
                "iam_v1_policy_protos",
                "longrunning_operations_protos",
                "rpc_error_details_protos",
                "rpc_status_protos",
            }
            for component in GRPC_UTILS_REQUIRED_PROTOS:
                self._add_proto_component(component)

            self.cpp_info.components["grpc_utils"].requires = list(GRPC_UTILS_REQUIRED_PROTOS) + ["common", "abseil::absl_function_ref", "abseil::absl_memory", "abseil::absl_time", "grpc::grpc++", "grpc::_grpc"]
            self.cpp_info.components["grpc_utils"].libs = ["google_cloud_cpp_grpc_utils"]
            self.cpp_info.components["grpc_utils"].names["pkg_config"] = "google_cloud_cpp_grpc_utils"

            # Add needed proto components
            for component in needed_protos:
                if component == 'storage_protos':
                    continue
                if component not in GRPC_UTILS_REQUIRED_PROTOS:
                    self._add_proto_component(component)

            # Interface libraries for backwards compatibility (only if relevant protos are present)
            compat_mappings = {
                "cloud_bigquery_protos": "bigquery_protos",
                "cloud_dialogflow_v2_protos": "dialogflow_es_protos",
                "cloud_speech_protos": "speech_protos",
                "cloud_texttospeech_protos": "texttospeech_protos",
                "devtools_cloudtrace_v2_trace_protos": "trace_protos",
                "devtools_cloudtrace_v2_tracing_protos": "trace_protos",
                "logging_type_type_protos": "logging_type_protos",
            }
            for compat, target in compat_mappings.items():
                if target in needed_protos:
                    self.cpp_info.components[compat].requires = [target]

        # Add selected GA components
        for component in selected:
            protos = f"{component}_protos"
            if component in self._REQUIRES_CUSTOM_DEPENDENCIES:
                continue
            if needs_grpc:
                self._add_grpc_component(component, protos)

        # Custom dependency components
        if "bigtable" in selected:
            self._add_grpc_component("bigtable", "bigtable_protos")

        if "iam" in selected:
            self._add_grpc_component("iam", "iam_protos")

        if "pubsub" in selected:
            self._add_grpc_component("pubsub", "pubsub_protos", ["abseil::absl_flat_hash_map"])

        if "spanner" in selected:
            self._add_grpc_component("spanner", "spanner_protos", ["abseil::absl_fixed_array", "abseil::absl_numeric", "abseil::absl_strings", "abseil::absl_time"])

        if "bigquery" in selected:
            self._add_grpc_component("bigquery", "bigquery_protos")

        if "oauth2" in selected:
            self.cpp_info.components["rest_protobuf_internal"].requires = ["rest_internal", "grpc_utils", "common"]
            self.cpp_info.components["rest_protobuf_internal"].libs = ["google_cloud_cpp_rest_protobuf_internal"]
            self.cpp_info.components["rest_protobuf_internal"].names["pkg_config"] = "google_cloud_cpp_rest_protobuf_internal"
            self.cpp_info.components["oauth2"].requires = ["rest_internal", "common", "nlohmann_json::nlohmann_json", "libcurl::libcurl", "openssl::ssl", "openssl::crypto", "zlib::zlib"]
            self.cpp_info.components["oauth2"].libs = ["google_cloud_cpp_oauth2"]
            self.cpp_info.components["oauth2"].names["pkg_config"] = "google_cloud_cpp_oauth2"

        # Storage (always available as default)
        if "storage" in selected:
            self.cpp_info.components["storage"].requires = ["rest_internal", "common", "nlohmann_json::nlohmann_json", "abseil::absl_memory", "abseil::absl_strings", "abseil::absl_str_format", "abseil::absl_time", "abseil::absl_variant", "crc32c::crc32c", "libcurl::libcurl", "openssl::ssl", "openssl::crypto", "zlib::zlib"]
            self.cpp_info.components["storage"].libs = ["google_cloud_cpp_storage"]
            self.cpp_info.components["storage"].names["pkg_config"] = "google_cloud_cpp_storage"
