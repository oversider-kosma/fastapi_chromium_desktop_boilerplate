import os
from pathlib import Path
import toml
import platform
import shutil
import subprocess
import tempfile
import requests

from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.options import Options

from tqdm import tqdm

from utils import compress_folder_to_zstd, bumb


from config import *

class Prebuild(NuitkaPluginBase):
    plugin_name = "prebuild" 
        
    def __init__(self):
        self.base_path = Path(__file__).parent.resolve()
        os.makedirs(self.base_path / BUILD_ASSETS_DIR, exist_ok=True)
        repacked_path = self.base_path / VENDOR_DIR / CHROMIUM_REPACKED_ZIP
        if not repacked_path.exists():
            self.report(f"{repacked_path} not found. Will be [re]created.")
            if platform.system().lower() != "windows":
                msg = f"Fow now, auto-creation of {repacked_path} is supported on Windows only. On other systems, it has to be provided manually"
                self.report(msg)
                raise NotImplementedError(msg)
            for asset in ASSETS:
                self.prepare_asset(asset)
            self.repack_chromium()
        assert(repacked_path.exists())


    @classmethod
    def report(cls, *args, **kwargs):
        print(f"Nuitka-User-Plugin: [{cls.plugin_name}]", *args, **kwargs)

    @classmethod
    def download_with_progress(cls, url, save_path):
        with requests.get(url, stream=True) as r:
            r.raise_for_status()

            total_size = int(r.headers.get('content-length', 0))
            
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk)) # Обновляем бар на размер чанка

    def prepare_asset(self, asset):
        asset_path = self.base_path / BUILD_ASSETS_DIR / asset
        asset_url = ASSETS[asset]

        if asset_path.exists():
            self.report(f"Found archive: {asset_path}")
        else:
            self.report(f"File {asset_path} not found. Downloading archive from {asset_url}")
            self.download_with_progress(asset_url, asset_path)

    
    def repack_chromium(self):
        exe7z = self.base_path / BUILD_ASSETS_DIR / SEVENZIP_EXE
        orig = self.base_path / BUILD_ASSETS_DIR / CHROMIUM_ORIG_7Z
        repack = self.base_path / VENDOR_DIR / CHROMIUM_REPACKED_ZIP

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            self.report(f"Unpacking {orig} to {tmp_dir}...")
            subprocess.run(
                    [str(exe7z), 'x', str(orig), f'-o{tmp_dir}', '-y'], 
                    check=True)
            subfolder = os.listdir(tmp_path)[0]
            old_path = tmp_path/subfolder
            new_path = tmp_path/CHROMIUM_DIR
            shutil.move(old_path, new_path)
            self.report(f"Packing {new_path} to {repack}")
            compress_folder_to_zstd(new_path, repack)

    

# Это обязательная часть, чтобы Nuitka «увидела» класс
class MyPluginDetector(NuitkaPluginBase):
    pass 
