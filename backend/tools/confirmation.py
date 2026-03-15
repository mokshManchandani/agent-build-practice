from google.adk.tools import FunctionTool


def approve_payout(claim_id: str, payout_amount: float, reason: str) -> dict:
    """
    Approves and processes an insurance payout for a claim.

    Use this when the user wants to approve a payout for a specific claim
    This action is IRREVERSIBLE - ALWAYS requires human confirmation first.

    Args:
        claim_id (str): the unique claim identifier, e.g. 'CLM-98765'
        payout_amount (float): the amount in USD to be processed.
        reason (str): Brief reason for approving the payout

    Returns:
        dict: a dictionary with keys claim_id, payout_amount, status, message.
    """
    return {
        "claim_id": claim_id,
        "payout_amount": payout_amount,
        "status": "processed",
        "message": f"Payout of ${payout_amount:,.2f} for claim {claim_id} approved.",
    }


approve_payout_tool = FunctionTool(
    func=approve_payout,
    require_confirmation=True,  # this nudges ADK to always ask for user input.
)
