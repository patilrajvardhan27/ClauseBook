"""Pulls CUAD v1 and stores it unmodified, keyed by SHA-256.

CUAD (510 commercial contracts, lawyer-labeled spans across 41 categories,
CC BY 4.0) is the project's one real-world corpus. Bronze keeps exactly what
was downloaded, so a bug discovered three layers downstream can always be
traced back to the original file rather than a half-remembered transform.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import httpx

CUAD_URL = "https://zenodo.org/record/4595826/files/CUAD_v1.zip"
BRONZE_DIR = Path("data/bronze/cuad")


def download(force: bool = False) -> Path:
    """Downloads the CUAD v1 archive once; a second call is a no-op unless
    force=True, which is the idempotency this stage promises."""
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = BRONZE_DIR / "CUAD_v1.zip"

    if archive_path.exists() and not force:
        return archive_path

    with httpx.stream("GET", CUAD_URL, timeout=120.0, follow_redirects=True) as response:
        response.raise_for_status()
        with open(archive_path, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)

    _write_manifest(archive_path)
    return archive_path


def _write_manifest(archive_path: Path) -> None:
    sha256 = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    manifest = {
        "source_url": CUAD_URL,
        "license": "CC BY 4.0",
        "sha256": sha256,
        "file": archive_path.name,
    }
    (BRONZE_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))


def extract_json(archive_path: Path) -> dict:
    """CUAD ships its labels as a single SQuAD-style JSON inside the zip."""
    with zipfile.ZipFile(archive_path) as zf:
        json_names = [n for n in zf.namelist() if n.endswith(".json")]
        with zf.open(json_names[0]) as f:
            return json.load(f)
