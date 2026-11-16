# Runs a batch of contracts through a live API, timing each review and reporting p50/p95.
from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

API_BASE_URL = "http://localhost:8000"
PLAYBOOK_NAME = "Sample Sell-Side SaaS Playbook"
POLL_INTERVAL_SECONDS = 0.5
POLL_TIMEOUT_SECONDS = 300


@dataclass
class ReviewTiming:
    contract_path: str
    pages: int
    time_to_first_finding_s: float
    total_time_s: float


# Finds the sample playbook's id, so every run targets the same ladder.
def _get_sample_playbook_id(client: httpx.Client) -> str:
    response = client.get(f"{API_BASE_URL}/v1/playbooks")
    response.raise_for_status()
    for playbook in response.json():
        if playbook["name"] == PLAYBOOK_NAME:
            return playbook["id"]
    raise RuntimeError(f"Playbook '{PLAYBOOK_NAME}' not found; run pipelines/seed/run_seed.py first")

# Uploads one document and times its review to first finding and to completion, reading the SSE
# stream directly rather than polling status, so "time to first finding" means what it says.
def _time_one_review(client: httpx.Client, playbook_id: str, contract_path: Path) -> ReviewTiming:
    with contract_path.open("rb") as f:
        upload = client.post(f"{API_BASE_URL}/v1/documents", files={"file": f})
    upload.raise_for_status()
    document_id = upload.json()["id"]

    start = time.monotonic()
    review = client.post(f"{API_BASE_URL}/v1/reviews", json={"document_id": document_id, "playbook_id": playbook_id})
    review.raise_for_status()
    review_id = review.json()["id"]

    first_finding_time = None
    with client.stream("GET", f"{API_BASE_URL}/v1/reviews/{review_id}/events", timeout=POLL_TIMEOUT_SECONDS) as stream:
        event_name = None
        for line in stream.iter_lines():
            if line.startswith("event: "):
                event_name = line.removeprefix("event: ").strip()
                if event_name in ("done", "error"):
                    break
            elif line.startswith("data: ") and event_name == "finding_ready" and first_finding_time is None:
                first_finding_time = time.monotonic()

    total_time = time.monotonic() - start
    return ReviewTiming(
        contract_path=str(contract_path),
        pages=0,  # filled in by the document row once parsing reports a real page count
        time_to_first_finding_s=(first_finding_time or time.monotonic()) - start,
        total_time_s=total_time,
    )


# Computes the pth percentile of a list of numbers with no numpy dependency.
def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(int(len(ordered) * p), len(ordered) - 1)
    return ordered[index]


def main() -> None:
    contract_paths = [Path(p) for p in sys.argv[1:]]
    if not contract_paths:
        print("Usage: python3 ml/eval/perf.py path/to/contracts/*.docx")
        return

    with httpx.Client(timeout=POLL_TIMEOUT_SECONDS) as client:
        playbook_id = _get_sample_playbook_id(client)
        timings = [_time_one_review(client, playbook_id, path) for path in contract_paths]

    total_times = [t.total_time_s for t in timings]
    first_finding_times = [t.time_to_first_finding_s for t in timings]

    print(f"Ran {len(timings)} contracts")
    print(f"Time to first finding: p50 {_percentile(first_finding_times, 0.5):.1f}s, p95 {_percentile(first_finding_times, 0.95):.1f}s")
    print(f"Total review time:     p50 {_percentile(total_times, 0.5):.1f}s, p95 {_percentile(total_times, 0.95):.1f}s")


if __name__ == "__main__":
    main()
