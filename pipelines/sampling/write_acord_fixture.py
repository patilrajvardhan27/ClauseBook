# Writes eval/fixtures/acord_queries.csv from ACORD's own queries and qrels, with stable ids that survive a reseed.
from __future__ import annotations

import csv
from pathlib import Path

from pipelines.bronze.acord import download, extract_acord
from pipelines.seed.acord_precedent import seed_acord_precedent

OUTPUT_PATH = Path("eval/fixtures/acord_queries.csv")
SPLIT = "test"


def write_fixture() -> int:
    seed_acord_precedent()

    archive_path = download()
    data = extract_acord(archive_path)
    query_text_by_id = {q["_id"]: q["text"] for q in data["queries"]}
    corpus_ids = {entry["_id"] for entry in data["corpus"]}

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0

    with OUTPUT_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["query_id", "query_text", "precedent_id", "relevance"])

        for query_id, corpus_id, relevance in data["qrels"][SPLIT]:
            query_text = query_text_by_id.get(query_id)
            if corpus_id not in corpus_ids or query_text is None:
                continue
            writer.writerow([query_id, query_text, f"acord:{corpus_id}", relevance])
            row_count += 1

    print(f"Wrote {row_count} query/precedent rows (split={SPLIT}) to {OUTPUT_PATH}")
    return row_count


if __name__ == "__main__":
    write_fixture()
