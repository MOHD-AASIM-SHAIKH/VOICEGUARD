import re, hashlib, json

# Supports Indian numbering (e.g. 50,00,000) and colloquial units (lakh, crore)
AMOUNT_PATTERN = re.compile(r"(?:₹|inr|rs\.?)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|lac|crore|cr)?", re.IGNORECASE)
ACTION_KEYWORDS = ["transfer", "send", "wire", "pay", "remit", "bhejo", "de do"]
RECIPIENT_PATTERN = re.compile(r"\bto\s+([A-Za-z0-9\s&]+?)(?:\s+(?:urgently|immediately|today|now)|\s*$)", re.IGNORECASE)

def parse_intent(spoken_text: str, recipient_hint: str = None) -> dict:
    """Robust slot extraction for transaction intent parsing in telephony fraud protection."""
    lower_text = spoken_text.lower()
    action = "TRANSFER" if any(kw in lower_text for kw in ACTION_KEYWORDS) else "UNKNOWN"
    
    amount = 0
    match = AMOUNT_PATTERN.search(spoken_text)
    if match:
        raw_num = match.group(1).replace(",", "")
        try:
            base = float(raw_num)
            unit = (match.group(2) or "").lower()
            multiplier = 1
            if unit in ["lakh", "lac"]:
                multiplier = 100000
            elif unit in ["crore", "cr"]:
                multiplier = 10000000
            amount = int(base * multiplier)
        except ValueError:
            amount = 0

    # Auto-extract recipient if not provided
    recipient = recipient_hint
    if not recipient:
        rec_match = RECIPIENT_PATTERN.search(spoken_text)
        if rec_match:
            recipient = rec_match.group(1).strip()
    recipient = recipient or "UNKNOWN"

    intent = {"action": action, "amount": amount, "recipient": recipient}
    canonical = json.dumps(intent, sort_keys=True, separators=(",", ":"))
    tx_hash = "0x" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    intent["txHash"] = tx_hash
    return intent


if __name__ == "__main__":
    # Test case 1: Standard
    r1 = parse_intent("transfer 50 lakh to ABC Industries", recipient_hint="ABC Industries")
    assert r1["action"] == "TRANSFER"
    assert r1["amount"] == 5000000
    assert r1["recipient"] == "ABC Industries"
    assert r1["txHash"].startswith("0x")

    # Test case 2: "send" keyword with auto recipient extraction
    r2 = parse_intent("Please send 50,00,000 to ABC Industries urgently")
    assert r2["action"] == "TRANSFER"
    assert r2["amount"] == 5000000
    assert "ABC Industries" in r2["recipient"]

    # Test case 3: ₹ currency prefix
    r3 = parse_intent("Send ₹25 lakh to XYZ Corp")
    assert r3["action"] == "TRANSFER"
    assert r3["amount"] == 2500000

    print("PASS: intent parser comprehensive test passed")
