"""Deterministic term extraction, by clause type.

Rules run first because a regex for '3x the fees paid' is cheap, fast and
explainable. The LLM extractor (not wired in this slice) only runs on the
attributes a rule returns nothing for, and its output is still validated
against a Pydantic schema before it reaches the placement engine.
"""
