# Computes Cohen's kappa between two labelers on the gold clause CSV's shared rows.
from __future__ import annotations

import sys

import pandas as pd
from sklearn.metrics import cohen_kappa_score


# Computes Cohen's kappa between the "primary" and "second_rater" rows sharing a clause_id.
def compute_kappa(csv_path: str) -> float:
    df = pd.read_csv(csv_path)
    primary = df[df["labeled_by"] == "primary"].set_index("clause_id")
    second = df[df["labeled_by"] == "second_rater"].set_index("clause_id")

    shared_ids = primary.index.intersection(second.index)
    if len(shared_ids) == 0:
        raise ValueError("No shared clause_ids between 'primary' and 'second_rater' rows")

    return cohen_kappa_score(
        primary.loc[shared_ids, "gold_matched_position_id"],
        second.loc[shared_ids, "gold_matched_position_id"],
    )


if __name__ == "__main__":
    kappa = compute_kappa(sys.argv[1])
    print(f"Cohen's kappa on shared rows: {kappa:.3f}")
    if kappa < 0.6:
        print("Below 0.6 -- tighten position definitions and relabel before trusting the full set.")
