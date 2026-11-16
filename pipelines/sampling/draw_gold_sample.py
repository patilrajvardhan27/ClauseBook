# Draws the 150-clause gold set: at least 10 per clause type, at most 2 per contract, fixed seed.
#
# Run after pipelines/gold/run_gold.py has written data/gold/segments.csv.
# Writes a draft CSV with everything but the label columns filled in, so
# labeling is "open this file, fill in two columns" rather than starting
# from a blank sheet.
from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

GOLD_SEGMENTS_PATH = Path("data/gold/segments.csv")
DRAFT_PATH = Path("eval/fixtures/gold_clauses_draft.csv")

TARGET_TOTAL = 150
MIN_PER_CATEGORY = 10
MAX_PER_CONTRACT = 2
RANDOM_SEED = 20261115  # fixed so the draw is reproducible; change only with a comment explaining why

V1_CATEGORIES = [
    "Cap On Liability",
    "Uncapped Liability",
    "Termination For Convenience",
    "Notice Period To Terminate Renewal",
    "Renewal Term",
    "Governing Law",
    "Anti-Assignment",
    "Audit Rights",
]


# One candidate row: a segment plus the single v1 category it was drawn for.
def _read_candidates() -> dict[str, list[dict]]:
    by_category: dict[str, list[dict]] = defaultdict(list)
    with GOLD_SEGMENTS_PATH.open() as f:
        for row in csv.DictReader(f):
            categories = json.loads(row["categories_json"])
            for category in categories:
                if category in V1_CATEGORIES:
                    by_category[category].append(row)
    return by_category


# Draws up to `count` rows for one category, skipping contracts already at their cap.
def _draw_for_category(rows: list[dict], count: int, contract_counts: dict[str, int], rng: random.Random) -> list[dict]:
    shuffled = rows.copy()
    rng.shuffle(shuffled)
    picked: list[dict] = []
    for row in shuffled:
        if len(picked) >= count:
            break
        if contract_counts[row["contract_id"]] >= MAX_PER_CONTRACT:
            continue
        picked.append(row)
        contract_counts[row["contract_id"]] += 1
    return picked


# Draws the full 150-clause sample and writes the labeling draft CSV.
def draw_sample() -> int:
    rng = random.Random(RANDOM_SEED)
    candidates = _read_candidates()
    contract_counts: dict[str, int] = defaultdict(int)

    per_category_target = max(MIN_PER_CATEGORY, TARGET_TOTAL // len(V1_CATEGORIES))
    picked_rows: list[tuple[str, dict]] = []

    for category in V1_CATEGORIES:
        rows = candidates.get(category, [])
        drawn = _draw_for_category(rows, per_category_target, contract_counts, rng)
        picked_rows.extend((category, row) for row in drawn)

    picked_rows = picked_rows[:TARGET_TOTAL]

    DRAFT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DRAFT_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["clause_id", "cuad_category", "clause_text", "deal_context_json",
             "gold_matched_position_id", "gold_proposed_position_id", "labeled_by"]
        )
        for i, (category, row) in enumerate(picked_rows):
            writer.writerow([f"gold-{i + 1:03d}", category, row["text"], "{}", "", "", "primary"])

    print(f"Drew {len(picked_rows)} candidate clauses across {len(V1_CATEGORIES)} categories to {DRAFT_PATH}")
    print("Fill in gold_matched_position_id and gold_proposed_position_id by hand, then rename to gold_clauses.csv.")
    return len(picked_rows)


if __name__ == "__main__":
    draw_sample()
