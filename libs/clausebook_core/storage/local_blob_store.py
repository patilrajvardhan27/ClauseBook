# Stores and reads uploaded document bytes on local disk, keyed by content hash, standing in for S3.
from __future__ import annotations

from pathlib import Path

BLOB_DIR = Path("data/uploads")


# Writes a document's raw bytes to disk under its content hash and original filename's extension.
def write_blob(sha256: str, filename: str, content: bytes) -> Path:
    BLOB_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix or ".bin"
    path = BLOB_DIR / f"{sha256}{suffix}"
    if not path.exists():
        path.write_bytes(content)
    return path


# Finds a previously written blob by its content hash, regardless of extension.
def find_blob(sha256: str) -> Path | None:
    if not BLOB_DIR.exists():
        return None
    matches = list(BLOB_DIR.glob(f"{sha256}.*"))
    return matches[0] if matches else None
