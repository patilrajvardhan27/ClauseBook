# Exact-match checks for the deterministic term extractors, against real CUAD-style text.
from ml.extract.extractors import extract


# A cap multiple spelled "three (3) times" extracts as 3.0, with the lookback and carve-outs.
def test_cap_multiple_from_parenthetical_numeral():
    text = (
        "liable for damages exceeding three (3) times the fees paid in the "
        "preceding twelve (12) months, except for breaches of confidentiality"
    )
    attrs = extract("Cap On Liability", text)
    assert attrs["cap_multiple"] == 3.0
    assert attrs["lookback_months"] == 12
    assert "confidential" in attrs["carve_outs"]


# Notice days and which party may terminate extract correctly together.
def test_termination_for_convenience_notice_and_party():
    text = "Either party may terminate this Agreement for convenience upon 30 days written notice."
    attrs = extract("Termination For Convenience", text)
    assert attrs == {"notice_days": 30, "who_may_terminate": "either"}


# The governing-law jurisdiction extracts cleanly even with a trailing conflicts-of-law clause.
def test_governing_law_jurisdiction():
    text = "This Agreement shall be governed by the laws of the State of Delaware, without regard to conflicts of law."
    attrs = extract("Governing Law", text)
    assert attrs["jurisdiction"] == "Delaware"


# An unmapped clause type returns nothing rather than raising.
def test_unknown_clause_type_returns_empty():
    assert extract("Nonexistent Category", "anything") == {}
