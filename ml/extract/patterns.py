"""Regex patterns for the eight v1 attributes.

Each pattern is written against real CUAD phrasing, not a textbook example,
which is why some look oddly specific -- "fees paid in the twelve (12)
months" is how contracts actually say "lookback_months".
"""
from __future__ import annotations

import re

CAP_MULTIPLE = re.compile(
    r"(?:\(\s*(?P<mult>\d+(?:\.\d+)?)\s*\)\s*times|(?P<mult2>\d+(?:\.\d+)?)\s*(?:x|times))"
    r"\s+(?:the\s+)?(?:fees|amounts?)\s+paid",
    re.I,
)
FIXED_CAP_AMOUNT = re.compile(r"\$\s?(?P<amount>[\d,]+(?:\.\d{2})?)", re.I)
LOOKBACK_MONTHS = re.compile(r"(?:preceding|prior|twelve|12|6|six)\s*\(?(?P<months>\d{1,2})?\)?\s*month", re.I)
NOTICE_DAYS = re.compile(r"(?P<days>\d{1,3})\s*(?:calendar\s+|business\s+)?days?\s*(?:prior\s+|written\s+)?notice", re.I)
RENEWAL_MONTHS = re.compile(r"renew(?:s|ed|al)?\s+for\s+(?:an?\s+)?(?:additional\s+)?(?P<months>\d{1,2})\s*month", re.I)
AUTO_RENEW = re.compile(r"automatically\s+renew", re.I)
JURISDICTION = re.compile(
    r"laws?\s+of\s+(?:the\s+)?(?:state\s+of\s+)?(?P<jurisdiction>[A-Z][a-zA-Z\s]+?)(?:,|\.|without)", re.I
)
UNCAPPED_CARVE_OUT_MARKERS = re.compile(
    r"(confidential|indemnif|gross negligence|wilful|willful|fraud|IP|intellectual property)", re.I
)
