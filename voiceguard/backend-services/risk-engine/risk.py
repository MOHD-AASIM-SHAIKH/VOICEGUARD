def evaluate_risk(amount: float, is_new_beneficiary: bool, hour_of_day: int) -> int:
    """Returns requiredApprovals: 1 (normal) or 2 (step-up)."""
    HIGH_AMOUNT_THRESHOLD = 1000000  # ₹10 lakh — adjust with team sign-off, not silently
    is_unusual_time = hour_of_day < 6 or hour_of_day > 22
    if amount > HIGH_AMOUNT_THRESHOLD or is_new_beneficiary or is_unusual_time:
        return 2
    return 1


if __name__ == "__main__":
    # Quick self-test
    assert evaluate_risk(500000, False, 14) == 1, "Normal tx should need 1 approval"
    assert evaluate_risk(2000000, False, 14) == 2, "High amount should need 2 approvals"
    assert evaluate_risk(500000, True, 14) == 2, "New beneficiary should need 2 approvals"
    assert evaluate_risk(500000, False, 3) == 2, "Unusual time should need 2 approvals"
    print("PASS: risk engine self-test passed")
