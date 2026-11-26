"""Stage a version-scoped SDK recipe only for tags declaring a zstd gRPC revision."""

import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import yaml


MARKER = "thirdparty/grpc-zstd/conan-reference.txt"
ASSETS = (
    "scripts/export_grpc_zstd.py",
    "cmake/PrepareGrpcZstd.cmake",
    "thirdparty/grpc-zstd/conanfile.py",
    "thirdparty/grpc-zstd/grpc.patch",
    "thirdparty/grpc-zstd/message_compress_zstd.h",
)
STOCK_GRPC = "grpc/1.65.0#38c2f71c0dcad882681a571439b2a21a"
REFERENCE = re.compile(r"grpc/1\.65\.0@milvus/zstd#[0-9a-f]{32}")
TEMPLATE = Path(__file__).resolve().parent / "templates" / "sdk_grpc_zstd_conanfile.py"


def read_release(stream, commit):
    """Read data from the same GitHub tag archive whose SHA256 goes in conandata."""
    with tarfile.open(fileobj=stream, mode="r:gz") as archive:
        root = archive.next().name
        try:
            marker = archive.getmember(f"{root}/{MARKER}")
        except KeyError:
            return None
        if archive.pax_headers.get("comment") != commit:
            raise ValueError("SDK tag archive does not match the dispatched commit")
        if not marker.isfile() or marker.size > 128:
            raise ValueError("invalid SDK gRPC reference file")
        reference = archive.extractfile(marker).read().decode("ascii").strip()
        if not REFERENCE.fullmatch(reference):
            raise ValueError("expected grpc/1.65.0@milvus/zstd with an exact recipe revision")

        files = {}
        for name in ASSETS:
            member = archive.getmember(f"{root}/{name}")
            if not member.isfile():
                raise ValueError(f"expected a regular SDK recipe file: {name}")
            files[name] = archive.extractfile(member).read()
        return reference, files


def create_recipe(root, version, release):
    """Keep existing versions on their existing registry recipe revision."""
    reference, files = release
    destination = root / f"grpc-zstd-{version}"
    destination.mkdir()
    shutil.copyfile(TEMPLATE, destination / "conanfile.py")
    shutil.copyfile(root / "all" / "conanfile.py", destination / "registry_base.py")
    shutil.copytree(root / "all" / "test_package", destination / "test_package")
    for name, data in files.items():
        path = destination / "bootstrap" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (destination / "conandata.yml").write_text(f'grpc_zstd:\n  "{version}": "{reference}"\nsources:\n')


def bootstrap(recipe_dir, version, remote):
    """Export the reviewed SDK codec recipe before resolving the SDK build graph."""
    reference = yaml.safe_load((recipe_dir / "conandata.yml").read_text())["grpc_zstd"][version]
    if not REFERENCE.fullmatch(reference):
        raise ValueError("invalid pinned gRPC recipe reference")
    # The source SDK's exporter takes one remote. Seed its exact ConanCenter
    # base using the registry mirror first, then the canonical public remote.
    if subprocess.run(["conan", "cache", "path", STOCK_GRPC], capture_output=True).returncode:
        for source_remote in dict.fromkeys((remote, "conancenter")):
            download = subprocess.run(["conan", "download", STOCK_GRPC, "--only-recipe", "-r", source_remote])
            if download.returncode == 0:
                break
        else:
            raise RuntimeError(f"could not download pinned base recipe {STOCK_GRPC}")
    export_script = recipe_dir / "bootstrap" / "scripts" / "export_grpc_zstd.py"
    subprocess.run([sys.executable, str(export_script), "--remote", remote], check=True)

    def cached_path(ref):
        return subprocess.check_output(["conan", "cache", "path", ref], text=True).strip()

    # Check the revision just exported, including when an older pinned revision is cached.
    if cached_path(reference.split("#")[0]) != cached_path(reference):
        raise ValueError(f"SDK gRPC export did not reproduce {reference}")


if __name__ == "__main__":
    bootstrap(Path(sys.argv[1]), sys.argv[2], sys.argv[3])
