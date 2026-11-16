# Pulls CUAD v1 and stores it unmodified in bronze, keyed by SHA-256.
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import httpx

CUAD_URL = "https://zenodo.org/record/4595826/files/CUAD_v1.zip"
BRONZE_DIR = Path("data/bronze/cuad")


# Downloads the CUAD v1 archive once; a second call is a no-op unless force=True.
def download(force: bool = False) -> Path:
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = BRONZE_DIR / "CUAD_v1.zip"

    if archive_path.exists() and not force:
        return archive_path

    with httpx.stream("GET", CUAD_URL, timeout=120.0, follow_redirects=True) as response:
        response.raise_for_status()
        with open(archive_path, "wb") as f:
            f.writelines(response.iter_bytes())

    _write_manifest(archive_path)
    return archive_path


# Records the download's source URL, license and SHA-256 next to the archive.
def _write_manifest(archive_path: Path) -> None:
    sha256 = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    manifest = {
        "source_url": CUAD_URL,
        "license": "CC BY 4.0",
        "sha256": sha256,
        "file": archive_path.name,
    }
    (BRONZE_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))


# Reads the single SQuAD-style JSON file CUAD ships its labels in.
def extract_json(archive_path: Path) -> dict:
    with zipfile.ZipFile(archive_path) as zf:
        json_names = [n for n in zf.namelist() if n.endswith(".json")]
        with zf.open(json_names[0]) as f:
            return json.load(f)
