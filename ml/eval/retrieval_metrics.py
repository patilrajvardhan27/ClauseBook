# nDCG@k and Recall@k, computed once here so acord_eval.py and any future retrieval suite agree.
from __future__ import annotations

import math


# Discounted cumulative gain at k for a ranked list of relevance scores, in rank order.
def _dcg_at_k(relevances: list[float], k: int) -> float:
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances[:k]))


# nDCG@k: DCG@k divided by the best possible DCG@k for the same relevance values.
def ndcg_at_k(ranked_relevances: list[float], k: int) -> float:
    dcg = _dcg_at_k(ranked_relevances, k)
    ideal = _dcg_at_k(sorted(ranked_relevances, reverse=True), k)
    return dcg / ideal if ideal > 0 else 0.0


# Fraction of all relevant documents that appear in the top k results.
def recall_at_k(ranked_relevant_flags: list[bool], total_relevant: int, k: int) -> float:
    if total_relevant == 0:
        return 0.0
    found = sum(1 for flag in ranked_relevant_flags[:k] if flag)
    return found / total_relevant
