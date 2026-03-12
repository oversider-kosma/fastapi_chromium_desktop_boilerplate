from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

@dataclass(frozen=True, kw_only=True)
class  BuildAsset:
    filename: str
    url: str
    sha_256: str

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
