from contextlib import suppress
import os
import shutil
import sys
import tarfile
import tempfile
import platform
from pathlib import Path



from nuitka.plugins.PluginBase import NuitkaPluginBase

from nuitka.utils.Execution import executeProcess
from nuitka.Tracing import plugins_logger

import toml
from tqdm import tqdm
import requests

plugin_dir = str(Path(__file__).parent / "app")
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from config import ASSETS, BUILD_ASSETS_DIR, CHROMIUM_DIR, CHROMIUM_REPACKED_ZIP, VENDOR_DIR  # noqa: E402
from utils import compress_folder_to_zstd  # noqa: E402
from build_asset import BuildAsset  # noqa: E402

PLATFORM = platform.system()
ARCH_IS_64 = platform.machine().endswith('64')


def build_info_toml():
    pyproject_toml = toml.load(Path('pyproject.toml'))
    project = pyproject_toml['project']
    info = {k:v for k,v in project.items() if k in ['name', 'version', 'description']}
    info = {"project": info}
    with open(Path(__file__).parent / "app" / "info.toml", "w", encoding="utf-8") as fd:
        toml.dump(info, fd)


class Prebuild(NuitkaPluginBase):
    plugin_name = "prebuild"

    def __init__(self) -> None:
        self.base_path = Path(__file__).parent.resolve()
        self.prepare_chromium()
        build_info_toml()

    def prepare_chromium(self) -> None:
        assets_dir = self.base_path / BUILD_ASSETS_DIR
        assets_dir.mkdir(parents=True, exist_ok=True)
        repacked_path = self.base_path / "app" /VENDOR_DIR / CHROMIUM_REPACKED_ZIP
        if repacked_path.exists():
            return

        plugins_logger.info(f"Target {repacked_path} not found. Starting preparation...")
        supported_system = PLATFORM in ('Windows', 'Linux') and ARCH_IS_64
        if not supported_system:
            self.sysexit(f"Fow now, auto-creation of {Path(VENDOR_DIR) / CHROMIUM_REPACKED_ZIP} is currently Windows x64 and Linux x64. \n"
                         f"On other systems it must be provided manualy.")

        for asset in ASSETS[PLATFORM].values():
            self.prepare_asset(asset)

        if platform.system() == "Windows":
            self._repack_chromium_win()
        elif platform.system() == "Linux":
            self._repack_chromium_lin()
        else:
            assert False, "Unsupported patform"

        if not repacked_path.exists():
            self.sysexit("Failed to create repacked chromium archive.")

    def prepare_asset(self, asset: BuildAsset) -> None:
        if asset.is_intact():
            plugins_logger.info(f"Using cached asset: {asset.filename}")
        else:
            if not asset.found():
                plugins_logger.info(f"Asset {asset.filename} not found")
            elif not asset.hash_ok():
                plugins_logger.info(f"Asset {asset.filename} have hashsum mismatch")
            try:
                with requests.get(asset.url, stream=True) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading {asset.filename}") as pbar:
                        with open(asset.path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=1024*64):
                                f.write(chunk)
                                pbar.update(len(chunk))
            except Exception as e:
                self.sysexit(f"Failed to download {asset.filename}: {e}")
            if not asset.is_intact():
                self.sysexit(f"Failed to prepare required asset {asset.filename}")


    def _cut_the_crap(self, where: Path, keep: list[str]):
         """deletes everything in target_path except keep"""
         for item in where.iterdir():
             if item.is_file() and item.name not in keep:
                 item.unlink()


    def _pack_chromium_to_zip(self, unpacked_path: Path, target_zip):
            content_dirs = [d for d in unpacked_path.iterdir() if d.is_dir()]
            if not content_dirs:
                self.sysexit("Extracted archive is empty or contains no directories.")

            # not perfect, but the subfolder name doesn't match
            # the archive name directly. Given there's only one
            # subfolder, let's keep it this way
            src_folder = content_dirs[0]
            target_folder = unpacked_path / CHROMIUM_DIR

            with suppress(FileNotFoundError):
                self._cut_the_crap(Path(src_folder) / "Locales", keep=['en-US.pak'])
            with suppress(FileNotFoundError):
                self._cut_the_crap(Path(src_folder) / "locales", keep=['en-US.pak'])

            if src_folder != target_folder:
                shutil.move(str(src_folder), str(target_folder))

            plugins_logger.info(f"Compresing to ZSTD: {target_zip.name}")
            compress_folder_to_zstd(target_folder, target_zip, compression_level=17)

    def _repack_chromium_win(self) -> None:
        exe7z = self.base_path / ASSETS[PLATFORM]['7zip'].path
        orig_7z = self.base_path / ASSETS[PLATFORM]['chromium'].path
        repack_zip = self.base_path / "app" / VENDOR_DIR / CHROMIUM_REPACKED_ZIP

        with tempfile.TemporaryDirectory() as tmp_dir:
            plugins_logger.info(f"Extracting {orig_7z.name}...")

            sevenzip_cmd = [str(exe7z), 'x', str(orig_7z), f'-o{tmp_dir}', '-y']
            stderr, exit_code = executeProcess(command=sevenzip_cmd)[-2:]
            if exit_code != 0:
                self.sysexit(f"7zip failed with exit code {exit_code}. Error: {stderr}")
            self._pack_chromium_to_zip(Path(tmp_dir), repack_zip)

    def _repack_chromium_lin(self) -> None:
        orig_xz = self.base_path / ASSETS[PLATFORM]['chromium'].path
        repack_zip = self.base_path / "app" / VENDOR_DIR / CHROMIUM_REPACKED_ZIP
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._lin_extract_tarxz(orig_xz, Path(tmp_dir))
            self._pack_chromium_to_zip(Path(tmp_dir), repack_zip)

    def _lin_extract_tarxz(self, archive_path: Path|str, extract_path: Path|str) -> None:
        try:
            with tarfile.open(archive_path, "r:xz") as tar:
                tar.extractall(path=extract_path, filter='data')
        except tarfile.ReadError as e:
            self.sysexit(f"Error opening tar file: {e}")
        except Exception as e:
            self.sysexit(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    if 'build_info_toml' in sys.argv:
        build_info_toml()
        sys.exit(0)

    # shurtcut to run this out of Nuitka's build
    if 'prepack_chromium' in sys.argv:
        prebuild = Prebuild()
        sys.exit(0)
