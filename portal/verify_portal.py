"""E1 fixture and presentation guardrails. Run: python portal/verify_portal.py
No API calls, scientific execution, or modifications of historical files.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALID_VERDICTS = {"falsified_in_tested_setup", "structural_pattern_in_tested_setup", "inconclusive", "interrupted", "blocked", "no_scientific_verdict"}
VALID_KINDS = {"historical_synthetic_experiment", "historical_record", "reproduced_measurement", "synthetic_ui_demo"}
VALID_VERIFICATION = {"recovered_and_cross_checked", "independently_reproduced", "reported_only", "unverified"}


def verify() -> None:
    records = json.loads((ROOT / "data/evidence.json").read_text(encoding="utf-8"))
    assert isinstance(records, list) and records, "Missing case records"
    seen = set()
    for case in records:
        assert case["schema_version"] == 1
        assert case["verdict"] in VALID_VERDICTS
        assert case["model_identity_status"] in {"unknown", "requested_only", "verified_by_returned_identity"}
        prov = case["provenance"]
        assert prov["repository"] == "sushan5140/Minos-J"
        assert prov["source_path"] and not prov["source_path"].startswith(("http:", "https:", "/"))
        assert prov["evidence_kind"] in VALID_KINDS
        assert prov["verification"] in VALID_VERIFICATION
        if prov["evidence_kind"] == "synthetic_ui_demo":
            assert prov["verification"] != "independently_reproduced"
        key = (case["experiment_id"], case["case_id"], case.get("arm_id"))
        assert key not in seen, f"Duplicate case: {key}"
        seen.add(key)
        if case["trace_status"] == "unavailable":
            assert case["trace_events"] == [], "Unavailable trace must not contain fabricated events"
        else:
            assert case["trace_status"] == "verified_events"
            assert case["trace_events"], "Empty verified trace"
            event_ids = set()
            for event in case["trace_events"]:
                assert event["source_path"] and event["event_id"] not in event_ids
                event_ids.add(event["event_id"])
        if "usage" in case:
            u = case["usage"]
            assert u["counting_basis"]
            for name in ["input_tokens", "output_tokens", "cached_input_tokens", "reported_total_tokens"]:
                v = u[name]
                assert v is None or (type(v) is int and v >= 0)
    assert len([c for c in records if c["experiment_id"] == "17-C"]) == 2
    assert all(c["verdict"] == "inconclusive" for c in records if c["experiment_id"] == "17-C")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    for needed in ["prefers-reduced-motion", "Recorded event replay unavailable", "Concept diagram", "escapeHTML", "aria-label", "data/evidence.json"]:
        assert needed in html, f"Missing safeguard: {needed}"
    assert "AeroCal" not in html
    print(f"PASS: {len(records)} records, unique IDs, provenance, no invented traces, inconclusive verdicts and UI safeguards")


if __name__ == "__main__":
    verify()
