"""A small, hand-written stand-in for the real CUAD training split.

CUAD itself (510 contracts, 41 categories, CC BY 4.0) is pulled by
pipelines/bronze/cuad.py and is too large to vendor here. These dozen
sentences exist so the classifier, the placement engine and the worker can
be exercised end to end with no download and no API key -- useful for a
laptop demo, not a substitute for training on the real corpus.
"""
from __future__ import annotations

SAMPLE_TEXTS = [
    "In no event shall either party's aggregate liability exceed three (3) times the fees paid in the preceding twelve (12) months.",
    "Notwithstanding the foregoing, there shall be no cap on liability arising from a breach of confidentiality obligations or gross negligence.",
    "Either party may terminate this Agreement for convenience upon 60 days prior written notice to the other party.",
    "Client must provide written notice of non-renewal at least 90 days before the end of the then-current term.",
    "This Agreement shall automatically renew for successive twelve (12) month terms unless either party provides notice of non-renewal.",
    "This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to conflicts of law principles.",
    "This Agreement shall be governed by the laws of the State of New York.",
    "Neither party may assign this Agreement without the prior written consent of the other party, except in connection with a change of control.",
    "Company may, upon reasonable notice and no more than once per year, audit Vendor's records at Company's own expense.",
    "Vendor shall maintain records sufficient to permit an audit by Client, upon 30 days notice, not more than once annually, at Vendor's expense.",
    "The total liability of either party under this Agreement shall not exceed the amount set forth in Schedule B.",
    "Damages are limited to direct damages actually incurred, up to the total contract value paid in the prior year.",
]

SAMPLE_LABELS = [
    ["Cap On Liability"],
    ["Uncapped Liability"],
    ["Termination For Convenience"],
    ["Notice Period To Terminate Renewal"],
    ["Renewal Term"],
    ["Governing Law"],
    ["Governing Law"],
    ["Anti-Assignment"],
    ["Audit Rights"],
    ["Audit Rights"],
    ["Cap On Liability"],
    ["Cap On Liability"],
]
