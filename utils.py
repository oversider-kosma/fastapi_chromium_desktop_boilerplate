import ctypes
import os
import platform
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
from pathlib import Path
from typing import Optional, Any, Generator

import psutil
import toml
import zstandard

from contextlib import contextmanager
from config import BUILD_NO_FILE, CHROMIUM_REPACKED_ZIP, VENDOR_DIR


def get_base_path() -> Path:
    """Returns the application base directory, handling frozen (Nuitka/PyInstaller) environments."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.resolve()
    else:
        return Path(__file__).parent.resolve()


def get_free_port() -> int:
    """Finds a free userspace port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def compress_folder_to_zstd(folder_path: str | Path, output_archive: str | Path, compression_level: int = 3, threads: int = -1) -> None:
    """Archives a folder into a tar file using Zstandard compression."""
    folder_path = Path(folder_path)
    cctx = zstandard.ZstdCompressor(level=compression_level, threads=threads)
    with open(output_archive, 'wb') as f_out:
        with cctx.stream_writer(f_out) as compressor:
            with tarfile.open(fileobj=compressor, mode='w|') as tar:
                tar.add(folder_path, arcname=folder_path.name)


def decompress_zstd_archive(archive_path: str | Path, extract_to: str | Path) -> None:
    """Decompresses a .tar.zstd archive to the specified directory."""
    dctx = zstandard.ZstdDecompressor()
    with open(archive_path, 'rb') as f_in:
        with dctx.stream_reader(f_in) as reader:
            with tarfile.open(fileobj=reader, mode='r|') as tar:
                tar.extractall(path=extract_to)


def bumb() -> None:
    """bump but for build_no, so it is bumb"""
    fpath = get_base_path() / BUILD_NO_FILE
    try:
        with open(fpath, 'r') as fp:
            build_no = int(fp.read().strip())
    except Exception:
        build_no = 0
    build_no += 1
    with open(fpath, 'w') as fp:
        fp.write(str(build_no))


def remove_nuitka_splash() -> None:
    """Hides the Nuitka splash screen and signals readiness to the parent process."""
    if platform.system() != "Windows":
        return

    parent_pid = os.environ.get("NUITKA_ONEFILE_PARENT")
    if parent_pid:
        splash_filename = os.path.join(
            tempfile.gettempdir(),
            f"onefile_{parent_pid}_splash_feedback.tmp",
        )
        if os.path.exists(splash_filename):
            os.unlink(splash_filename)

        # Signal readiness using Windows API
        ctypes.windll.kernel32.SetEvent(int(parent_pid)) # pyright: ignore[reportAttributeAccessIssue]


def _read_pyproject_toml() -> Optional[dict[str, Any]]:
    """Reads and parses the pyproject.toml file if it exists."""
    pyproject_toml_file = Path(__file__).parent / "pyproject.toml"
    if pyproject_toml_file.exists() and pyproject_toml_file.is_file():
        return toml.load(pyproject_toml_file)
    return None


def clear_old_caches() -> None:
    """Deletes old version cache directories based on semantic versioning (x.x.x.x)."""
    base_dir = get_base_path()
    try:
        current_version = tuple(map(int, base_dir.name.split('.')))
    except (ValueError, AttributeError):
        return

    to_delete = []
    for entry in base_dir.parent.iterdir():
        entry = entry.resolve()
        if entry.is_dir() and entry != base_dir:
            try:
                version_parts = tuple(map(int, entry.name.split('.')))
                if len(version_parts) != 4:
                    continue
                if version_parts < current_version:
                    if (entry / BUILD_NO_FILE).is_file():
                        to_delete.append(entry)
            except ValueError:
                pass

    for entry in to_delete:
        print(f"[!] Deleting old version cache: {entry}")
        shutil.rmtree(entry, ignore_errors=True)


def kill_proc_tree(pid: int) -> None:
    """Recursively terminates a process and all its children by PID."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
        psutil.wait_procs(children + [parent], timeout=3)
    except psutil.NoSuchProcess:
        pass


def wipe_dir(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'[!] Error deleting {file_path}: {e}')


@contextmanager
def managed_process(*args: Any, **kwargs: Any) -> Generator[subprocess.Popen, None, None]:
    """Context manager to run a process and ensure its entire process tree is terminated on exit."""
    proc = subprocess.Popen(*args, **kwargs)
    try:
        yield proc
    finally:
        kill_proc_tree(proc.pid)


def fetch_chromium(target_dir) -> None:
    """Extracts the Chromium binary from the archive and updates the thread status."""
    current_thread = threading.current_thread()
    setattr(current_thread, "chromium_fetched", False)
    base_path = get_base_path()
    zip_file_path = base_path / VENDOR_DIR / CHROMIUM_REPACKED_ZIP

    print(f"[*] Decompressing chromium to {target_dir}")
    decompress_zstd_archive(zip_file_path, target_dir)
    print(f"[*] Chromium extracted into {target_dir}")
    setattr(current_thread, "chromium_fetched", True)


def get_version() -> str:
    """Fetches the version from pyproject.toml and appends the build number."""
    data = _read_pyproject_toml()
    version = "0.0.0"
    if data and "project" in data:
        version = data["project"].get("version", "0.0.0")

    build_no_path = get_base_path() / BUILD_NO_FILE
    if not build_no_path.exists():
        print(f"[!] {build_no_path} not found!")
        try:
            build_no_path.write_text("1")
        except OSError: # we are readonly if we're inside AppImage
            pass
        build_no = "1"
    else:
        build_no = build_no_path.read_text().strip()

    return f"{version}.{build_no}"


def get_description() -> str:
    """Fetches the project description from pyproject.toml."""
    data = _read_pyproject_toml()
    if data and "project" in data:
        return data["project"].get("description", "").strip()
    return ""


def get_name() -> str:
    """Fetches the project name from pyproject.toml."""
    data = _read_pyproject_toml()
    if data and "project" in data:
        return data["project"].get("name", "")
    return ""

def get_repacked_name() -> str:
    return Path(VENDOR_DIR) / CHROMIUM_REPACKED_ZIP

if __name__ == "__main__":
    # Command-line interface for build purposes
    if 'bumb' in sys.argv:
        bumb()
        sys.exit(0)

    if 'get_version' in sys.argv:
        print(get_version())
        sys.exit(0)

    if 'get_name' in sys.argv:
        print(get_name())
        sys.exit(0)

    if 'get_description' in sys.argv:
        print(get_description())
        sys.exit(0)

    if 'get_repacked_name' in sys.argv:
        print(get_repacked_name())
        sys.exit(0)
