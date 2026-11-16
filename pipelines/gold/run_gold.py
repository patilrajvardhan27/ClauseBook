# Runs bronze through gold for the full CUAD corpus and writes one row per segment to disk.
#
# This is the step the sampling and training scripts both read from, so it
# runs once and writes a flat file instead of every downstream script
# re-parsing the zip. Needs CUAD already downloaded (pipelines/bronze/cuad.py).
from __future__ import annotations

import csv
import json
from pathlib import Path

from pipelines.bronze.cuad import download, extract_json
from pipelines.gold.segments import build_gold_segments
from pipelines.silver.cuad import CuadSpan, normalize

GOLD_SEGMENTS_PATH = Path("data/gold/segments.csv")
CONTRACTS_DIR_NAME = "full_contract_txt"


# Loads every contract's raw text from the extracted CUAD archive.
def _load_contract_texts(archive_path: Path) -> dict[str, str]:
    import zipfile

    texts: dict[str, str] = {}
    with zipfile.ZipFile(archive_path) as zf:
        for name in zf.namelist():
            if CONTRACTS_DIR_NAME in name and name.endswith(".txt"):
                contract_id = Path(name).stem
                with zf.open(name) as f:
                    texts[contract_id] = f.read().decode("utf-8", errors="replace")
    return texts


# Builds gold segments for every contract and writes them to a flat CSV.
def run_gold_pipeline() -> int:
    archive_path = download()
    cuad_json = extract_json(archive_path)
    spans: list[CuadSpan] = normalize(cuad_json)
    contract_texts = _load_contract_texts(archive_path)

    GOLD_SEGMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0

    with GOLD_SEGMENTS_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["contract_id", "ord", "start_char", "end_char", "text", "heading", "categories_json"])

        for contract_id, contract_text in contract_texts.items():
            gold_segments = build_gold_segments(contract_id, contract_text, spans)
            for gold in gold_segments:
                writer.writerow(
                    [
                        contract_id,
                        gold.segment.ord,
                        gold.segment.start_char,
                        gold.segment.end_char,
                        gold.segment.text,
                        gold.segment.heading or "",
                        json.dumps(gold.categories),
                    ]
                )
                row_count += 1

    print(f"Wrote {row_count} gold segments across {len(contract_texts)} contracts to {GOLD_SEGMENTS_PATH}")
    return row_count


if __name__ == "__main__":
    run_gold_pipeline()
