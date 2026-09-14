import os
import json
from datetime import datetime

CAMPAIGN_DB_FILE = os.path.join(os.path.dirname(__file__), "campaign_db.json")
campaign_index = {}

def load_campaigns():
    global campaign_index
    if os.path.exists(CAMPAIGN_DB_FILE):
        try:
            with open(CAMPAIGN_DB_FILE, "r", encoding="utf-8") as f:
                campaign_index = json.load(f)
        except Exception:
            campaign_index = {}

def save_campaigns():
    try:
        with open(CAMPAIGN_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(campaign_index, f, indent=2)
    except Exception:
        pass

def register_report(evidence_hash: str, reporter_id: str, timestamp=None, persist=False):
    """Registers an incident evidence hash into the syndicated campaign database."""
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    campaign_index.setdefault(evidence_hash, []).append({
        "reporter": reporter_id,
        "timestamp": str(timestamp)
    })
    if persist:
        save_campaigns()

def get_campaign_for_hash(evidence_hash: str) -> dict:
    """Returns the campaign cluster details and victim count for a given SHA-256 evidence hash."""
    reports = campaign_index.get(evidence_hash, [])
    return {
        "campaignId": evidence_hash,
        "victimCount": len(reports),
        "reports": reports
    }

# Load existing database on module load if available
load_campaigns()

if __name__ == "__main__":
    HASH_A = "abc123canonical"
    HASH_B = "def456canonical"
    register_report(HASH_A, "reporter-1", datetime.utcnow().isoformat())
    register_report(HASH_A, "reporter-2", datetime.utcnow().isoformat())
    register_report(HASH_B, "reporter-3", datetime.utcnow().isoformat())

    campaign_a = get_campaign_for_hash(HASH_A)
    campaign_b = get_campaign_for_hash(HASH_B)
    assert campaign_a["victimCount"] == 2, f"Expected 2, got {campaign_a['victimCount']}"
    assert campaign_b["victimCount"] == 1, f"Expected 1, got {campaign_b['victimCount']}"
    assert campaign_a["campaignId"] != campaign_b["campaignId"]
    print("PASS: campaign linking persistent test passed")
