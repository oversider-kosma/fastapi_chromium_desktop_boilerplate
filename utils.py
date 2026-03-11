import ctypes
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
import threading

import psutil
import toml
import zstandard

from contextlib import contextmanager


from config import BUILD_NO_FILE, CHROMIUM_DIR, CHROMIUM_REPACKED_ZIP, VENDOR_DIR


def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.resolve()
    else:
        return Path(__file__).parent.resolve()


def get_free_port():
    """Находит свободный userspace порт"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def compress_folder_to_zstd(folder_path, output_archive, compression_level=3, threads=-1):
    folder_path = Path(folder_path)
    cctx = zstandard.ZstdCompressor(level=compression_level, threads=threads)
    with open(output_archive, 'wb') as f_out:
        with cctx.stream_writer(f_out) as compressor:
            with tarfile.open(fileobj=compressor, mode='w|') as tar:
                tar.add(folder_path, arcname=folder_path.name)


def decompress_zstd_archive(archive_path, extract_to):
    dctx = zstandard.ZstdDecompressor()
    with open(archive_path, 'rb') as f_in:
        with dctx.stream_reader(f_in) as reader:
            with tarfile.open(fileobj=reader, mode='r|') as tar:
                tar.extractall(path=extract_to)


def bumb():
    '''bump but for build_no, so it is bumb'''
    fpath = get_base_path() / BUILD_NO_FILE
    try:
        with open(fpath, 'r') as fp:
            build_no = fp.read()
            build_no = int(build_no)
    except Exception:
        build_no = 0
    build_no += 1
    with open(fpath, 'w') as fp:
        fp.write(f"{build_no}")


def remove_nuitka_splash():
    if "NUITKA_ONEFILE_PARENT" in os.environ:
        splash_filename = os.path.join(
            tempfile.gettempdir(),
            "onefile_%d_splash_feedback.tmp" % int(os.environ["NUITKA_ONEFILE_PARENT"]),
        )
        if os.path.exists(splash_filename):
            os.unlink(splash_filename)

    if "NUITKA_ONEFILE_PARENT" in os.environ:
        ctypes.windll.kernel32.SetEvent(int(os.environ["NUITKA_ONEFILE_PARENT"]))


def _read_pyproject_toml():
    pyproject_toml_file = Path(__file__).parent / "pyproject.toml"
    if pyproject_toml_file.exists() and pyproject_toml_file.is_file():
        return toml.load(pyproject_toml_file)
    return None

def print_current_dir():
    print("base_path:", get_base_path())
    print("cwd:", os.getcwd())

def clear_old_caches():
    base_dir = get_base_path()
    try:
        current = tuple(map(int, base_dir.name.split('.')))
    except:
        return

    to_delete = []
    for entry in base_dir.parent.iterdir():
        entry = entry.resolve()
        if entry.is_dir() and entry != base_dir:
            try:
                some = tuple(map(int, entry.name.split('.')))
                if len(some) != 4:
                    continue
                if some < current:
                    if (entry / BUILD_NO_FILE).is_file():
                        to_delete.append(entry)
            except ValueError:
                pass
    
    for entry in to_delete:
        print(f"[!] Deleting old version cache {entry}")
        shutil.rmtree(entry)


def kill_proc_tree(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
        psutil.wait_procs(children + [parent], timeout=3)
    except psutil.NoSuchProcess:
        pass

@contextmanager
def managed_process(*args, **kwargs):
    proc = subprocess.Popen(*args, **kwargs)
    try:
        yield proc
    finally:
        kill_proc_tree(proc.pid)

def fetch_chromium():
    threading.current_thread().chromium_fetched = False
    base_path = get_base_path()
    zip_file_name = base_path / VENDOR_DIR / CHROMIUM_REPACKED_ZIP
    target_dir = base_path / CHROMIUM_DIR
    decompress_zstd_archive(zip_file_name, base_path)
    print(f"[*] Cleint fetched into {target_dir}")
    threading.current_thread().chromium_fetched = True




def get_version():
    '''fetch version from pyproject.toml and join it with build number'''
    data = _read_pyproject_toml()
    if data is None:
        version = "0.0.0"
    else:
        if "project" in data and "version" in data["project"]:
            version = data["project"]["version"]

    build_no_path = get_base_path() / BUILD_NO_FILE
    if not build_no_path.exists():
        with open(build_no_path, "w") as f:
            f.write("1")
        build_no = "1"
    else:
        with open(build_no_path, "r") as f:
            build_no = f.read().strip()
    version_string = f"{version}.{build_no}"
    return version_string

def get_description():
    '''fetch description from pyproject.toml'''
    data = _read_pyproject_toml()
    if data is None:
        return ""
    if "project" in data and "description" in data["project"]:
        return data["project"]["description"]

def get_name():
    '''fetch project name from pyproject.toml'''
    data = _read_pyproject_toml()
    if data is None:
        return ""
    if "project" in data and "name" in data["project"]:
        return data["project"]["name"]

if __name__ == "__main__":
    # most of this is needed for build purpuse
    if 'bumb' in sys.argv: 
        bumb()
        sys.exit(0)

    if 'get_version' in sys.argv:
        print(get_version())
        sys.exit(0)
    
    if 'get_name' in sys.argv:
        print(get_name())
        sys.exit(0)
