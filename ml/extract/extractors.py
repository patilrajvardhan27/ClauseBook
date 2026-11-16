"""One extractor function per clause type, returning only what it found.

A missing key means "not found", never zero -- the placement engine treats
a missing attribute as "condition cannot be satisfied", which is the safe
default when extraction fails.
"""
from __future__ import annotations

from ml.extract import patterns as p


def extract_cap_on_liability(text: str) -> dict:
    attrs: dict = {}
    if m := p.CAP_MULTIPLE.search(text):
        attrs["cap_basis"] = "fees_paid"
        attrs["cap_multiple"] = float(m.group("mult") or m.group("mult2"))
    elif m := p.FIXED_CAP_AMOUNT.search(text):
        attrs["cap_basis"] = "fixed_amount"
        attrs["cap_amount"] = float(m.group("amount").replace(",", ""))
    if m := p.LOOKBACK_MONTHS.search(text):
        months = m.group("months")
        attrs["lookback_months"] = int(months) if months else 12
    attrs["carve_outs"] = sorted(set(m.group(0).lower() for m in p.UNCAPPED_CARVE_OUT_MARKERS.finditer(text)))
    return attrs


def extract_uncapped_liability(text: str) -> dict:
    carve_outs = sorted(set(m.group(0).lower() for m in p.UNCAPPED_CARVE_OUT_MARKERS.finditer(text)))
    return {"carve_outs": carve_outs}


def extract_termination_for_convenience(text: str) -> dict:
    attrs: dict = {}
    if m := p.NOTICE_DAYS.search(text):
        attrs["notice_days"] = int(m.group("days"))
    lowered = text.lower()
    if "either party" in lowered:
        attrs["who_may_terminate"] = "either"
    elif "company" in lowered or "client" in lowered:
        attrs["who_may_terminate"] = "client_only"
    return attrs


def extract_notice_period_to_terminate_renewal(text: str) -> dict:
    if m := p.NOTICE_DAYS.search(text):
        return {"notice_days": int(m.group("days"))}
    return {}


def extract_renewal_term(text: str) -> dict:
    attrs: dict = {"auto_renew": bool(p.AUTO_RENEW.search(text))}
    if m := p.RENEWAL_MONTHS.search(text):
        attrs["renewal_months"] = int(m.group("months"))
    return attrs


def extract_governing_law(text: str) -> dict:
    if m := p.JURISDICTION.search(text):
        return {"jurisdiction": m.group("jurisdiction").strip()}
    return {}


def extract_anti_assignment(text: str) -> dict:
    lowered = text.lower()
    return {
        "consent_required": "consent" in lowered,
        "change_of_control_trigger": "change of control" in lowered or "change-of-control" in lowered,
    }


def extract_audit_rights(text: str) -> dict:
    attrs: dict = {}
    if m := p.NOTICE_DAYS.search(text):
        attrs["notice_days"] = int(m.group("days"))
    lowered = text.lower()
    if "once" in lowered or "annually" in lowered or "per year" in lowered:
        attrs["frequency_per_year"] = 1
    attrs["cost_bearer"] = "auditing_party" if "its own expense" in lowered or "its expense" in lowered else "audited_party"
    return attrs


EXTRACTORS_BY_CUAD_CATEGORY = {
    "Cap On Liability": extract_cap_on_liability,
    "Uncapped Liability": extract_uncapped_liability,
    "Termination For Convenience": extract_termination_for_convenience,
    "Notice Period To Terminate Renewal": extract_notice_period_to_terminate_renewal,
    "Renewal Term": extract_renewal_term,
    "Governing Law": extract_governing_law,
    "Anti-Assignment": extract_anti_assignment,
    "Audit Rights": extract_audit_rights,
}


def extract(cuad_category: str, text: str) -> dict:
    extractor = EXTRACTORS_BY_CUAD_CATEGORY.get(cuad_category)
    return extractor(text) if extractor else {}
