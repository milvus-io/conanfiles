from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import get, copy, chdir
from conan.tools.env import Environment, VirtualBuildEnv
import os


class B2Conan(ConanFile):
    name = "b2"
    homepage = "https://www.bfgroup.xyz/b2/"
    description = "B2 makes it easy to build C++ projects, everywhere."
    topics = ("installer", "builder")
    license = "BSL-1.0"
    package_type = "application"
    settings = "os", "arch"
    url = "https://github.com/conan-io/conan-center-index"

    '''
    * use_cxx_env: False, True

    Indicates if the build will use the CXX and
    CXXFLAGS environment variables. The common use is to add additional flags
    for building on specific platforms or for additional optimization options.

    * toolset: 'auto', 'cxx', 'cross-cxx',
    'acc', 'borland', 'clang', 'como', 'gcc-nocygwin', 'gcc',
    'intel-darwin', 'intel-linux', 'intel-win32', 'kcc', 'kylix',
    'mingw', 'mipspro', 'pathscale', 'pgi', 'qcc', 'sun', 'sunpro',
    'tru64cxx', 'vacpp', 'vc12', 'vc14', 'vc141', 'vc142', 'vc143'

    Specifies the toolset to use for building. The default of 'auto' detects
    a usable compiler for building and should be preferred. The 'cxx' toolset
    uses the 'CXX' and 'CXXFLAGS' solely for building. Using the 'cxx'
    toolset will also turn on the 'use_cxx_env' option. And the 'cross-cxx'
    toolset uses the 'BUILD_CXX' and 'BUILD_CXXFLAGS' vars. This frees the
    'CXX' and 'CXXFLAGS' variables for use in subprocesses.
    '''
    options = {
        'use_cxx_env': [False, True],
        'toolset': [
            'auto', 'cxx', 'cross-cxx',
            'acc', 'borland', 'clang', 'como', 'gcc-nocygwin', 'gcc',
            'intel-darwin', 'intel-linux', 'intel-win32', 'kcc', 'kylix',
            'mingw', 'mipspro', 'pathscale', 'pgi', 'qcc', 'sun', 'sunpro',
            'tru64cxx', 'vacpp', 'vc12', 'vc14', 'vc141', 'vc142', 'vc143']
    }
    default_options = {
        'use_cxx_env': False,
        'toolset': 'auto'
    }

    def configure(self):
        if (self.options.toolset == 'cxx' or self.options.toolset == 'cross-cxx') and not self.options.use_cxx_env:
            raise ConanInvalidConfiguration(
                "Option toolset 'cxx' and 'cross-cxx' requires 'use_cxx_env=True'")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            strip_root=True, destination="source")

    def build(self):
        use_windows_commands = os.name == 'nt'
        command = "build" if use_windows_commands else "./build.sh"
        if self.options.toolset != 'auto':
            command += " " + str(self.options.toolset)
        build_dir = os.path.join(self.source_folder, "source")
        engine_dir = os.path.join(build_dir, "src", "engine")

        with chdir(self, engine_dir):
            env = Environment()
            env.define("VSCMD_START_DIR", os.curdir)
            if not self.options.use_cxx_env:
                # To avoid using the CXX env vars we clear them out for the build.
                env.define("CXX", "")
                env.define("CXXFLAGS", "")
            with env.vars(self).apply():
                self.run(command)

        with chdir(self, build_dir):
            b2_command = os.path.join(
                engine_dir, "b2.exe" if use_windows_commands else "b2")
            if self.options.toolset != 'auto':
                full_command = "{0} --ignore-site-config --prefix=../output --abbreviate-paths" \
                               " toolset={1} install".format(b2_command, self.options.toolset)
            else:
                full_command = "{0} --ignore-site-config --prefix=../output --abbreviate-paths" \
                               " install".format(b2_command)
            self.run(full_command)

    def package(self):
        copy(self, "LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=os.path.join(self.source_folder, "source"))
        copy(self, "*b2", dst=os.path.join(self.package_folder, "bin"), src=os.path.join(self.source_folder, "output", "bin"))
        copy(self, "*b2.exe", dst=os.path.join(self.package_folder, "bin"), src=os.path.join(self.source_folder, "output", "bin"))
        copy(self, "*.jam", dst=os.path.join(self.package_folder, "bin", "b2_src"), src=os.path.join(self.source_folder, "output", "share", "boost-build"))

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = ["bin"]

        # For Conan 2.x: set environment for consumers
        self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
        self.buildenv_info.define("BOOST_BUILD_PATH", os.path.join(
            self.package_folder, "bin", "b2_src", "src", "kernel"))

    def package_id(self):
        del self.info.options.use_cxx_env
        del self.info.options.toolset
