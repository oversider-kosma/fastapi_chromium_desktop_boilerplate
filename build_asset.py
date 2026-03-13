from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse


class  BuildAsset:
    def __init__(self, url: str, sha_256: str, filename=None):
        self.url = url
        self.sha_256 = sha_256
        self.filename = filename or Path(urlparse(url).path).name


    @property
    def path(self):
        from config import BUILD_ASSETS_DIR
        return Path(BUILD_ASSETS_DIR) / self.filename

    def found(self):
        return self.path.is_file()

    def hash_ok(self):
        hash = sha256()
        with open(self.path, "rb") as f:
             for byte_block in iter(lambda: f.read(64 * 1024), b""):
                hash.update(byte_block)
        if hash.hexdigest() != self.sha_256:
            return False
        return True

    def is_intact(self):
        return self.found() and self.hash_ok()
