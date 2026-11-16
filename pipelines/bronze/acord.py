# Pulls ACORD (The Atticus Project, CC BY 4.0) and stores it unmodified, keyed by SHA-256.
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import httpx

ACORD_URL = "https://huggingface.co/datasets/theatticusproject/acord/resolve/main/ACORD%20Dataset%20%26%20ReadMe.zip"
BRONZE_DIR = Path("data/bronze/acord")
INNER_DIR_NAME = "ACORD Dataset & ReadMe (external)"


# Downloads the ACORD archive once; a second call is a no-op unless force=True.
def download(force: bool = False) -> Path:
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = BRONZE_DIR / "ACORD_Dataset.zip"

    if archive_path.exists() and not force:
        return archive_path

    with httpx.stream("GET", ACORD_URL, timeout=120.0, follow_redirects=True) as response:
        response.raise_for_status()
        with open(archive_path, "wb") as f:
            f.writelines(response.iter_bytes())

    _write_manifest(archive_path)
    return archive_path


# Records the download's source URL, license and SHA-256 next to the archive.
def _write_manifest(archive_path: Path) -> None:
    sha256 = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    manifest = {"source_url": ACORD_URL, "license": "CC BY 4.0", "sha256": sha256, "file": archive_path.name}
    (BRONZE_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))


# Reads queries.jsonl, corpus.jsonl and the three qrels TSVs out of the zip.
def extract_acord(archive_path: Path) -> dict:
    with zipfile.ZipFile(archive_path) as zf:
        def _inner(name: str) -> str:
            return f"{INNER_DIR_NAME}/{name}"

        with zf.open(_inner("corpus.jsonl")) as f:
            corpus = [json.loads(line) for line in f.read().decode("utf-8").splitlines() if line]
        with zf.open(_inner("queries.jsonl")) as f:
            queries = [json.loads(line) for line in f.read().decode("utf-8").splitlines() if line]

        qrels: dict[str, list[tuple[str, str, int]]] = {}
        for split in ("train", "valid", "test"):
            with zf.open(_inner(f"qrels/{split}.tsv")) as f:
                lines = f.read().decode("utf-8").splitlines()[1:]  # skip header
                qrels[split] = [tuple(line.split("\t")) for line in lines if line]  # type: ignore[misc]

    return {"corpus": corpus, "queries": queries, "qrels": qrels}
