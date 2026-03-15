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

# ── Policy agent ───────────────────────────────────────────────────────────
policy_agent = LlmAgent(
    name="policy_agent",
    model="gemini-2.0-flash",
    description=(
        "Handles policy lookups. Use this when the user asks about "
        "their policy details, coverage limits, or premium amount."
    ),
    instruction="""
You are a policy lookup specialist.
Use get_policy_details to retrieve policy information.
Always ask for the policy number if the user hasn't provided one.
Keep answers factual and concise.
""",
    tools=[get_policy_details],
    output_key="policy_result",
)

# ── Claims agent ───────────────────────────────────────────────────────────
claims_agent = LlmAgent(
    name="claims_agent",
    model="gemini-2.0-flash",
    description=(
        "Handles claim status checks and payout estimates. Use this when "
        "the user asks about an existing claim or wants to estimate a payout."
    ),
    instruction="""
You are a claims processing specialist.
Use get_claim_status to check existing claims.
Use calculate_payout_estimate when the user wants to know their payout.
Always ask for claim ID or damage details if not provided.
If a claim is rejected, refer the user to appeals@insurance.com.
""",
    tools=[get_claim_status, calculate_payout_estimate],
    output_key="claims_result",
)

# ── Coordinator ────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    name="coordinator",
    model="gemini-2.0-flash",
    description="Routes insurance queries to the right specialist agent.",
    instruction="""
You are an insurance assistant coordinator.
Route every request to the correct specialist:
- Policy questions → policy_agent
- Claims or payout questions → claims_agent

Do not answer questions directly. Always delegate to a specialist.
If a question is outside insurance entirely, respond directly yourself — do not transfer to any specialist. Say: "That is outside the scope of insurance inquiries."
""",
    sub_agents=[policy_agent, claims_agent],
)
# ── Runner (singleton) ─────────────────────────────────────────────────────
runner = Runner(
    agent=root_agent, app_name="insurance-agent", session_service=session_service
)
