import os
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from .tools import get_policy_details, get_claim_status, calculate_payout_estimate

load_dotenv()
# ── Session service (singleton) ────────────────────────────────────────────
session_service = InMemorySessionService()

# ── Agent definition ───────────────────────────────────────────────────────
root_agent = LlmAgent(
    name="claims_triage_agent",
    model="gemini-2.0-flash",
    description=(
        "Handles insurance policy lookups, claim status checks, "
        "and payout estimates for auto, home, and health policies."
    ),
    instruction="""
    You are an insruance claims triage assistant.
    You help policyholders with three things:
        1. Looking up policy details
        2. Checking the status of an exisisting claim
        3. Estimating a payout before filing
    Rules:
        - Always use the provided tools - never invent policy or claim data.
        - If the user needs to give you an policy number or claim ID and hasn't
        ask for it before calling any tool.
        - keep answers concise: lead with the direct answer then details.
        - If a claim status is 'rejected', acknolwedge it and refer the user to appeals@insurance.com for next steps
        - If the question is outside insurance, polietly say it is out of scope.
    """,
    tools=[get_policy_details, get_claim_status, calculate_payout_estimate],
    # output_key='traige_response'
)
# ── Runner (singleton) ─────────────────────────────────────────────────────
runner = Runner(
    agent=root_agent, app_name="insurance-agent", session_service=session_service
)
