from urllib.parse import urlencode

def build_chakshu_link(incident: dict) -> str:
    base = "https://sancharsaathi.gov.in/sfc/"  # base report path — confirm exact live path before final demo
    params = {
        "reportedAt": incident["detectedAt"],
        "callType": incident.get("callType", ""),
        "confidence": incident.get("confidenceAtAlert", ""),
    }
    return f"{base}?{urlencode(params)}"
    # NOTE: no public API exists. This is a best-effort pre-filled deep-link.
    # If the portal's actual query parameters differ, this is a mechanical fix, not a design change.


if __name__ == "__main__":
    # Verification Gate 8: Confirm syntactically valid URL
    sample_incident = {
        "incidentId": "test-001",
        "detectedAt": "2026-09-13T10:22:36Z",
        "callType": "voip",
        "app": "whatsapp",
        "confidenceAtAlert": 0.93
    }
    link = build_chakshu_link(sample_incident)
    print(f"Chakshu link: {link}")
    assert link.startswith("https://sancharsaathi.gov.in/sfc/?"), "FAIL: invalid URL format"
    assert "reportedAt=" in link, "FAIL: missing reportedAt param"
    print("PASS: valid URL produced")
