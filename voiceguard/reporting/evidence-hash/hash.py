import hashlib, json

def compute_evidence_hash(incident: dict) -> str:
    # Canonical JSON (sorted keys, no whitespace) so the same incident always hashes identically
    canonical = json.dumps(incident, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    # Verification Gate 8: Run twice on the same incident, confirm identical output
    sample_incident = {
        "incidentId": "test-001",
        "detectedAt": "2026-09-13T10:22:36Z",
        "callType": "voip",
        "app": "whatsapp",
        "confidenceAtAlert": 0.93
    }
    h1 = compute_evidence_hash(sample_incident)
    h2 = compute_evidence_hash(sample_incident)
    print(f"Hash 1: {h1}")
    print(f"Hash 2: {h2}")
    print(f"Identical: {h1 == h2}")
    assert h1 == h2, "FAIL: hashes differ — non-deterministic serialization"
    print("PASS: deterministic hash confirmed")
