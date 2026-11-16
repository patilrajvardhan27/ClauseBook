"""Exact-match checks for the deterministic term extractors.

These are the cases that broke during manual testing against real CUAD
text: digits spelled with a parenthetical numeral, and a lookback phrase
with no explicit "months" count split across two matches.
"""
from ml.extract.extractors import extract


def test_cap_multiple_from_parenthetical_numeral():
    text = (
        "liable for damages exceeding three (3) times the fees paid in the "
        "preceding twelve (12) months, except for breaches of confidentiality"
    )
    attrs = extract("Cap On Liability", text)
    assert attrs["cap_multiple"] == 3.0
    assert attrs["lookback_months"] == 12
    assert "confidential" in attrs["carve_outs"]


def test_termination_for_convenience_notice_and_party():
    text = "Either party may terminate this Agreement for convenience upon 30 days written notice."
    attrs = extract("Termination For Convenience", text)
    assert attrs == {"notice_days": 30, "who_may_terminate": "either"}


def test_governing_law_jurisdiction():
    text = "This Agreement shall be governed by the laws of the State of Delaware, without regard to conflicts of law."
    attrs = extract("Governing Law", text)
    assert attrs["jurisdiction"] == "Delaware"


def test_unknown_clause_type_returns_empty():
    assert extract("Nonexistent Category", "anything") == {}
