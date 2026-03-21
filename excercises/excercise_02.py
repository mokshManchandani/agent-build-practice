from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from backend.tools import (
    get_policy_details,
    get_claim_status,
    calculate_payout_estimate,
)


policy_agent = LlmAgent(
    name="policy_agent",
    model="gemini-2.0-flash",
    description="Looks up policy details.",
    instruction="Use get_policy_details. Ask for policy number if not provided.",
    tools=[get_policy_details],
    output_key="policy_result",
)

claims_agent = LlmAgent(
    name="claims_agent",
    model="gemini-2.0-flash",
    description="Handles claim status and payout estimates.",
    instruction="Use get_claim_status or calculate_payout_estimate as needed.",
    tools=[get_claim_status, calculate_payout_estimate],
    output_key="claims_result",
)

root_agent = LlmAgent(
    name="coordinator",
    model="gemini-2.0-flash",
    instruction="""
You are an insurance coordinator.
Call policy_agent for policy questions.
Call claims_agent for claims or payout questions.
If a question is outside insurance, say so directly.
Always respond yourself after calling a specialist.
""",
    tools=[
        AgentTool(agent=policy_agent),  # ← called like a function
        AgentTool(agent=claims_agent),  # ← result comes back to coordinator
    ],
    # Note: NO sub_agents here
)

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent, app_name="exercise-02", session_service=session_service
)
