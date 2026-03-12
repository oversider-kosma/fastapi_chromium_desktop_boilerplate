import os
import shutil
import subprocess
import tempfile
import platform
from pathlib import Path

from nuitka.plugins.PluginBase import NuitkaPluginBase

from nuitka.utils.Execution import executeProcess
from nuitka.Tracing import plugins_logger

from tqdm import tqdm
import requests

from utils import compress_folder_to_zstd
from config import *

class Prebuild(NuitkaPluginBase):
    plugin_name = "prebuild"

    def __init__(self) -> None:
        self.base_path = Path(__file__).parent.resolve()
        self.prepare_chromium()

    def prepare_chromium(self) -> None:
        assets_dir = self.base_path / BUILD_ASSETS_DIR
        assets_dir.mkdir(parents=True, exist_ok=True)
        repacked_path = self.base_path / VENDOR_DIR / CHROMIUM_REPACKED_ZIP
        if repacked_path.exists():
            return

        plugins_logger.info(f"Target {repacked_path} not found. Starting preparation...")
        if platform.system() != "Windows":
            self.sysexit(f"Fow now, auto-creation of {Path(VENDOR_DIR / CHROMIUM_REPACKED_ZIP)} is currently Windows-only. On other systems it must be provided manualy.")

        for asset in ASSETS.values():
            self.prepare_asset(asset)
        self.repack_chromium()

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

    def repack_chromium(self) -> None:
        exe7z = self.base_path / ASSETS['7zip'].path
        orig_7z = self.base_path / ASSETS['chromium'].path
        repack_zip = self.base_path / VENDOR_DIR / CHROMIUM_REPACKED_ZIP

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            plugins_logger.info(f"Extracting {orig_7z.name}...")

            sevenzip_cmd = [str(exe7z), 'x', str(orig_7z), f'-o{tmp_dir}', '-y']
            _, stderr, exit_code = executeProcess(command=sevenzip_cmd)
            if exit_code != 0:
                self.sysexit(f"7zip failed with exit code {exit_code}. Error: {stderr}")


            content_dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
            if not content_dirs:
                self.sysexit("Extracted archive is empty or contains no directories.")

            # not perfect, but the subfolder name doesn't match
            # the archive name directly. Given there's only one
            # subfolder, let's keep it this way
            src_folder = content_dirs[0]
            target_folder = tmp_path / CHROMIUM_DIR

            if src_folder != target_folder:
                shutil.move(str(src_folder), str(target_folder))

            plugins_logger.info(f"Compresing to ZSTD: {repack_zip.name}")
            compress_folder_to_zstd(target_folder, repack_zip)
