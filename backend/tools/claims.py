def get_policy_details(policy_number: str) -> dict:
    """
    Retrieves details of an insurance policy by its policy number.

    Use this when the user provides a policy number and wants to know
    their coverage, premium or policy status

    Args:
        policy_number (str): The unique policy identifier, e.g. 'POL-12345'.

    Returns:
        dict: A dictionary with keys policy_number, holder_name, policy_type, coverage_limit (USD float), premium_monthly (USD float), status ('active' | 'lapsed' | 'under_review')
    """
    return {
        "policy_number": policy_number,
        "holder_name": "Moksh Manchandani",
        "policy_type": "auto",
        "coverage_limit": 50000.0,
        "premium_monthly": 142.50,
        "status": "active",
    }


def get_claim_status(claim_id: str) -> dict:
    """
    Returns the current status of an exisisting insruance claim.

    Use this when the user asks for an update on a specific claim,
    wants to know if it has been approved, or asks about their payout.

    Args:
        claim_id (str): The unique claim identifier, e.g 'CLM-98765'.

    Returns:
        dict: A dictionary with keys claim_id, policy_number, incident_date, claim_type, status ('submitted' | 'under_review' | 'approved' | 'rejected' | 'paid'), estimated_payout (USD float), adjuster_notes (str)
    """
    return {
        "claim_id": claim_id,
        "policy_number": "POL-12345",
        "incident_date": "2025-03-01",
        "claim_type": "collision",
        "status": "under_review",
        "estimated_payout": 8400.0,
        "adjuster_notes": "Damage photos received. Awaiting garage estimate.",
    }


def calculate_payout_estimate(
    damage_type: str,
    repair_cost: float,
    deductible: float,
) -> dict:
    """
    Estimates the insurance payout for a potential claim.

    Use this when the user wants to know how much they might receive,
    asks if a claim is worth filing, or wants to understand how their
    deductible affects their payout.

    Args:
        damage_type: Type of damage, e.g. 'collision', 'flood', 'theft'.
        repair_cost: Total estimated repair or replacement cost in USD.
        deductible: The policyholder's deductible amount in USD.

    Returns:
        A dict with keys: damage_type, repair_cost, deductible,
        estimated_payout (float), recommendation (str).
    """
    payout = max(0.0, repair_cost - deductible)

    if payout < 500:
        recommendation = (
            "Consider paying out of pocket — filing may not be worth "
            "the potential premium increase."
        )
    else:
        recommendation = "Worth filing. Estimated payout covers most of the cost."

    return {
        "damage_type": damage_type,
        "repair_cost": repair_cost,
        "deductible": deductible,
        "estimated_payout": payout,
        "recommendation": recommendation,
    }
