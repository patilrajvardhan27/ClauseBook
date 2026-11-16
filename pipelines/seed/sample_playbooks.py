# Eight sample ladders, not any real firm's guidance. Written from public drafting commentary.
from __future__ import annotations

# Each entry: (clause_type_cuad_category, attribute_key, attribute_kind,
# higher_is_better, [(rank, label, is_walk_away, op, value, approved_text), ...])
SAMPLE_LADDERS = [
    (
        "Cap On Liability", "cap_multiple", "number", False,
        [
            (0, "1x fees paid (12-month lookback)", False, "<=", 1.0,
             "Each party's aggregate liability under this Agreement shall not exceed the fees paid by Client in the twelve (12) months preceding the claim."),
            (1, "2x fees paid", False, "<=", 2.0,
             "Each party's aggregate liability under this Agreement shall not exceed two (2) times the fees paid by Client in the twelve (12) months preceding the claim."),
            (2, "3x fees paid (walk-away)", True, "<=", 3.0,
             "Each party's aggregate liability under this Agreement shall not exceed three (3) times the fees paid by Client in the twelve (12) months preceding the claim."),
        ],
    ),
    (
        "Termination For Convenience", "notice_days", "number", True,
        [
            (0, "90 days notice", False, ">=", 90,
             "Either party may terminate this Agreement for convenience upon ninety (90) days prior written notice."),
            (1, "60 days notice", False, ">=", 60,
             "Either party may terminate this Agreement for convenience upon sixty (60) days prior written notice."),
            (2, "30 days notice (walk-away)", True, ">=", 30,
             "Either party may terminate this Agreement for convenience upon thirty (30) days prior written notice."),
        ],
    ),
    (
        "Notice Period To Terminate Renewal", "notice_days", "number", True,
        [
            (0, "90 days notice of non-renewal", False, ">=", 90,
             "Either party may decline to renew this Agreement by providing written notice at least ninety (90) days before the end of the then-current term."),
            (1, "60 days notice of non-renewal (walk-away)", True, ">=", 60,
             "Either party may decline to renew this Agreement by providing written notice at least sixty (60) days before the end of the then-current term."),
        ],
    ),
    (
        "Renewal Term", "renewal_months", "number", False,
        [
            (0, "12-month renewal, no auto-renew", False, "<=", 12,
             "This Agreement may be renewed for successive twelve (12) month terms upon the written agreement of both parties."),
            (1, "12-month auto-renewal (walk-away)", True, "<=", 12,
             "This Agreement shall automatically renew for successive twelve (12) month terms unless either party provides notice of non-renewal."),
        ],
    ),
    (
        "Governing Law", "jurisdiction", "enum", True,
        [
            (0, "Delaware", False, "=", "Delaware",
             "This Agreement shall be governed by the laws of the State of Delaware, without regard to conflicts of law principles."),
            (1, "New York (walk-away)", True, "=", "New York",
             "This Agreement shall be governed by the laws of the State of New York, without regard to conflicts of law principles."),
        ],
    ),
    (
        "Anti-Assignment", "consent_required", "bool", True,
        [
            (0, "Consent required, no change-of-control carve-out", False, "=", True,
             "Neither party may assign this Agreement without the prior written consent of the other party."),
            (1, "Consent required, change-of-control carve-out allowed (walk-away)", True, "=", True,
             "Neither party may assign this Agreement without the prior written consent of the other party, except that either party may assign this Agreement to an acquirer in connection with a change of control."),
        ],
    ),
    (
        "Audit Rights", "frequency_per_year", "number", False,
        [
            (0, "Once per year, auditor's own expense", False, "<=", 1,
             "Client may audit Vendor's records relevant to this Agreement no more than once per year, upon thirty (30) days written notice, at Client's own expense."),
            (1, "Twice per year (walk-away)", True, "<=", 2,
             "Client may audit Vendor's records relevant to this Agreement no more than twice per year, upon thirty (30) days written notice, at Client's own expense."),
        ],
    ),
    (
        "Uncapped Liability", "carve_outs", "list", True,
        [
            (0, "Narrow carve-outs only", False, "contains_all", ["confidentiality"],
             "Nothing in this Agreement limits either party's liability for breach of confidentiality obligations."),
            (1, "Broad carve-outs (walk-away)", True, "contains_all", ["confidentiality", "indemnification"],
             "Nothing in this Agreement limits either party's liability for breach of confidentiality obligations, indemnification obligations, or gross negligence or willful misconduct."),
        ],
    ),
]
