# Regex patterns for the eight v1 attributes, written against real CUAD phrasing.
from __future__ import annotations

import re

CAP_MULTIPLE = re.compile(
    r"(?:\(\s*(?P<mult>\d+(?:\.\d+)?)\s*\)\s*times|(?P<mult2>\d+(?:\.\d+)?)\s*(?:x|times))"
    r"\s+(?:the\s+)?(?:fees|amounts?)\s+paid",
    re.IGNORECASE,
)
FIXED_CAP_AMOUNT = re.compile(r"\$\s?(?P<amount>[\d,]+(?:\.\d{2})?)", re.IGNORECASE)
LOOKBACK_MONTHS = re.compile(r"(?:preceding|prior|twelve|12|6|six)\s*\(?(?P<months>\d{1,2})?\)?\s*month", re.IGNORECASE)
NOTICE_DAYS = re.compile(r"(?P<days>\d{1,3})\s*(?:calendar\s+|business\s+)?days?\s*(?:prior\s+|written\s+)?notice", re.IGNORECASE)
RENEWAL_MONTHS = re.compile(r"renew(?:s|ed|al)?\s+for\s+(?:an?\s+)?(?:additional\s+)?(?P<months>\d{1,2})\s*month", re.IGNORECASE)
AUTO_RENEW = re.compile(r"automatically\s+renew", re.IGNORECASE)
JURISDICTION = re.compile(
    r"laws?\s+of\s+(?:the\s+)?(?:state\s+of\s+)?(?P<jurisdiction>[A-Z][a-zA-Z\s]+?)(?:,|\.|without)", re.IGNORECASE
)
UNCAPPED_CARVE_OUT_MARKERS = re.compile(
    r"(confidential|indemnif|gross negligence|wilful|willful|fraud|IP|intellectual property)", re.IGNORECASE
)
